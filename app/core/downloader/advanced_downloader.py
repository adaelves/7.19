"""
Advanced downloader with resume, multi-threading, M3U8 support, rate limiting, and proxy support.
"""
import asyncio
import aiohttp
import aiofiles
import hashlib
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Callable
from urllib.parse import urljoin, urlparse
import re
import json
from dataclasses import dataclass

from .base import BaseDownloader, DownloadStatus, ProgressInfo
from .rate_limiter import TokenBucketRateLimiter
from .m3u8_parser import M3U8Parser, M3U8Playlist
from app.data.models.core import VideoMetadata, DownloadOptions, DownloadResult

logger = logging.getLogger(__name__)


@dataclass
class SegmentInfo:
    """Information about a download segment"""
    start_byte: int
    end_byte: int
    segment_id: int
    url: str
    temp_file: str
    completed: bool = False
    retries: int = 0


@dataclass
class ProxyConfig:
    """Proxy configuration"""
    proxy_type: str  # 'http', 'https', 'socks4', 'socks5'
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    
    @property
    def proxy_url(self) -> str:
        """Get proxy URL for aiohttp"""
        if self.proxy_type.lower() in ['socks4', 'socks5']:
            # For SOCKS proxies, we need to use aiohttp-socks
            return f"{self.proxy_type.lower()}://{self.host}:{self.port}"
        else:
            # HTTP/HTTPS proxy
            auth = ""
            if self.username and self.password:
                auth = f"{self.username}:{self.password}@"
            return f"http://{auth}{self.host}:{self.port}"


class AdvancedDownloader(BaseDownloader):
    """
    Advanced downloader with support for:
    - Resume downloads (HTTP Range requests)
    - Multi-threaded segmented downloads
    - M3U8 streaming media parsing and download
    - Rate limiting with token bucket algorithm
    - Proxy support (HTTP/HTTPS/SOCKS)
    """
    
    def __init__(self, max_concurrent_segments: int = 4):
        super().__init__()
        self.max_concurrent_segments = max_concurrent_segments
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter: Optional[TokenBucketRateLimiter] = None
        self.proxy_config: Optional[ProxyConfig] = None
        self.m3u8_parser = M3U8Parser()
        
        # Download state
        self._segments: List[SegmentInfo] = []
        self._total_size: Optional[int] = None
        self._downloaded_size: int = 0
        self._start_time: float = 0
        self._cancelled = False
        self._paused = False
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        
        # User agent for requests
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
    
    async def _create_session(self, options: DownloadOptions) -> aiohttp.ClientSession:
        """Create HTTP session with appropriate configuration"""
        headers = {
            'User-Agent': options.user_agent or self.user_agent
        }
        
        # Configure timeout
        timeout = aiohttp.ClientTimeout(total=300, connect=30)
        
        # Configure connector
        connector_kwargs = {
            'limit': 100,
            'limit_per_host': self.max_concurrent_segments + 2,
            'ttl_dns_cache': 300,
            'use_dns_cache': True,
        }
        
        # Proxy configuration
        if options.proxy_url:
            self.proxy_config = self._parse_proxy_url(options.proxy_url)
            
            # For SOCKS proxies, we need aiohttp-socks
            if self.proxy_config.proxy_type.lower() in ['socks4', 'socks5']:
                try:
                    from aiohttp_socks import ProxyConnector
                    connector = ProxyConnector.from_url(self.proxy_config.proxy_url)
                except ImportError:
                    logger.warning("aiohttp-socks not installed, SOCKS proxy not supported")
                    connector = aiohttp.TCPConnector(**connector_kwargs)
            else:
                connector = aiohttp.TCPConnector(**connector_kwargs)
        else:
            connector = aiohttp.TCPConnector(**connector_kwargs)
        
        return aiohttp.ClientSession(
            headers=headers,
            timeout=timeout,
            connector=connector
        )
    
    def _parse_proxy_url(self, proxy_url: str) -> ProxyConfig:
        """Parse proxy URL into ProxyConfig"""
        parsed = urlparse(proxy_url)
        
        return ProxyConfig(
            proxy_type=parsed.scheme,
            host=parsed.hostname,
            port=parsed.port,
            username=parsed.username,
            password=parsed.password
        )
    
    async def download(self, url: str, options: DownloadOptions) -> DownloadResult:
        """Download content with advanced features"""
        try:
            self._cancelled = False
            self._paused = False
            self._start_time = time.time()
            self._update_status(DownloadStatus.DOWNLOADING)
            
            # Set up rate limiter if speed limit is specified
            if options.speed_limit:
                self.rate_limiter = TokenBucketRateLimiter(
                    rate=options.speed_limit * 1024,  # Convert KB/s to bytes/s
                    capacity=options.speed_limit * 1024 * 2  # 2 second burst
                )
            
            # Create HTTP session
            self.session = await self._create_session(options)
            
            # Check if URL is M3U8 playlist
            if await self._is_m3u8_url(url):
                return await self._download_m3u8(url, options)
            else:
                return await self._download_regular(url, options)
                
        except Exception as e:
            self._update_status(DownloadStatus.FAILED)
            logger.error(f"Download failed: {e}")
            return DownloadResult(
                success=False,
                error_message=str(e)
            )
        finally:
            if self.session:
                await self.session.close()
    
    async def _is_m3u8_url(self, url: str) -> bool:
        """Check if URL points to M3U8 playlist"""
        try:
            async with self.session.head(url) as response:
                content_type = response.headers.get('content-type', '').lower()
                return (
                    'application/vnd.apple.mpegurl' in content_type or
                    'application/x-mpegurl' in content_type or
                    url.lower().endswith('.m3u8')
                )
        except:
            return url.lower().endswith('.m3u8')
    
    async def _download_m3u8(self, url: str, options: DownloadOptions) -> DownloadResult:
        """Download M3U8 streaming media"""
        logger.info(f"Downloading M3U8 playlist: {url}")
        
        try:
            # Parse M3U8 playlist
            playlist = await self.m3u8_parser.parse_playlist(url, self.session)
            
            if not playlist.segments:
                raise Exception("No segments found in M3U8 playlist")
            
            # Create output file path
            output_path = Path(options.output_path)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            filename = self._generate_filename(url, options, 'ts')
            output_file = output_path / filename
            
            # Check for resume
            resume_position = 0
            if options.enable_resume and output_file.exists():
                resume_position = len([f for f in output_path.glob(f"{output_file.stem}_segment_*.ts") if f.exists()])
                logger.info(f"Resuming M3U8 download from segment {resume_position}")
            
            # Download segments
            total_segments = len(playlist.segments)
            self._total_size = total_segments  # Use segment count as "size"
            
            segment_files = []
            for i, segment in enumerate(playlist.segments[resume_position:], resume_position):
                if self._cancelled:
                    break
                
                while self._paused:
                    await asyncio.sleep(0.1)
                
                segment_url = urljoin(url, segment.uri)
                segment_file = output_path / f"{output_file.stem}_segment_{i:06d}.ts"
                
                # Download segment
                success = await self._download_segment(segment_url, segment_file, options)
                if success:
                    segment_files.append(segment_file)
                    self._downloaded_size = i + 1
                    
                    # Update progress
                    progress = ProgressInfo(
                        downloaded_bytes=self._downloaded_size,
                        total_bytes=total_segments,
                        percentage=(self._downloaded_size / total_segments) * 100,
                        speed=self._calculate_speed()
                    )
                    self._update_progress(progress)
                else:
                    raise Exception(f"Failed to download segment {i}")
            
            if not self._cancelled:
                # Concatenate segments
                await self._concatenate_segments(segment_files, output_file)
                
                # Clean up segment files
                for segment_file in segment_files:
                    try:
                        segment_file.unlink()
                    except:
                        pass
                
                self._update_status(DownloadStatus.COMPLETED)
                
                return DownloadResult(
                    success=True,
                    file_path=str(output_file),
                    file_size=output_file.stat().st_size if output_file.exists() else 0,
                    download_time=time.time() - self._start_time
                )
            else:
                return DownloadResult(success=False, error_message="Download cancelled")
                
        except Exception as e:
            logger.error(f"M3U8 download failed: {e}")
            raise e
    
    async def _download_segment(self, url: str, output_file: Path, options: DownloadOptions) -> bool:
        """Download a single segment"""
        for attempt in range(self.max_retries):
            try:
                proxy = self.proxy_config.proxy_url if self.proxy_config else None
                
                async with self.session.get(url, proxy=proxy) as response:
                    if response.status == 200:
                        async with aiofiles.open(output_file, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                if self._cancelled:
                                    return False
                                
                                # Apply rate limiting
                                if self.rate_limiter:
                                    await self.rate_limiter.acquire(len(chunk))
                                
                                await f.write(chunk)
                        
                        return True
                    else:
                        logger.warning(f"Segment download failed with status {response.status}: {url}")
                        
            except Exception as e:
                logger.warning(f"Segment download attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
        
        return False
    
    async def _concatenate_segments(self, segment_files: List[Path], output_file: Path) -> None:
        """Concatenate segment files into final output"""
        async with aiofiles.open(output_file, 'wb') as outf:
            for segment_file in segment_files:
                if segment_file.exists():
                    async with aiofiles.open(segment_file, 'rb') as inf:
                        while True:
                            chunk = await inf.read(65536)
                            if not chunk:
                                break
                            await outf.write(chunk)
    
    async def _download_regular(self, url: str, options: DownloadOptions) -> DownloadResult:
        """Download regular file with resume and multi-threading support"""
        logger.info(f"Downloading regular file: {url}")
        
        try:
            # Get file info
            file_info = await self._get_file_info(url)
            if not file_info:
                raise Exception("Could not get file information")
            
            self._total_size = file_info['size']
            supports_range = file_info['supports_range']
            
            # Create output file path
            output_path = Path(options.output_path)
            output_path.mkdir(parents=True, exist_ok=True)
            
            filename = self._generate_filename(url, options)
            output_file = output_path / filename
            
            # Check for resume
            resume_position = 0
            if options.enable_resume and output_file.exists():
                resume_position = output_file.stat().st_size
                logger.info(f"Resuming download from byte {resume_position}")
            
            # Determine download strategy
            if supports_range and self._total_size and self._total_size > 10 * 1024 * 1024:  # 10MB
                # Use multi-threaded segmented download for large files
                return await self._download_segmented(url, output_file, resume_position, options)
            else:
                # Use single-threaded download
                return await self._download_single_thread(url, output_file, resume_position, options)
                
        except Exception as e:
            logger.error(f"Regular download failed: {e}")
            raise e
    
    async def _get_file_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get file information including size and range support"""
        try:
            proxy = self.proxy_config.proxy_url if self.proxy_config else None
            
            async with self.session.head(url, proxy=proxy) as response:
                if response.status not in [200, 206]:
                    return None
                
                size = None
                content_length = response.headers.get('content-length')
                if content_length:
                    size = int(content_length)
                
                supports_range = 'bytes' in response.headers.get('accept-ranges', '')
                
                return {
                    'size': size,
                    'supports_range': supports_range,
                    'headers': dict(response.headers)
                }
        except Exception as e:
            logger.warning(f"Failed to get file info: {e}")
            return None
    
    async def _download_segmented(self, url: str, output_file: Path, resume_position: int, options: DownloadOptions) -> DownloadResult:
        """Download file using multiple segments"""
        logger.info(f"Starting segmented download with {self.max_concurrent_segments} segments")
        
        # Calculate segments
        remaining_size = self._total_size - resume_position
        segment_size = remaining_size // self.max_concurrent_segments
        
        self._segments = []
        for i in range(self.max_concurrent_segments):
            start_byte = resume_position + (i * segment_size)
            if i == self.max_concurrent_segments - 1:
                end_byte = self._total_size - 1
            else:
                end_byte = start_byte + segment_size - 1
            
            temp_file = f"{output_file}.part{i}"
            
            segment = SegmentInfo(
                start_byte=start_byte,
                end_byte=end_byte,
                segment_id=i,
                url=url,
                temp_file=temp_file
            )
            self._segments.append(segment)
        
        # Download segments concurrently
        tasks = []
        for segment in self._segments:
            task = asyncio.create_task(self._download_segment_range(segment, options))
            tasks.append(task)
        
        # Wait for all segments to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check if all segments completed successfully
        if all(isinstance(result, bool) and result for result in results):
            # Merge segments
            await self._merge_segments(output_file, resume_position)
            
            self._update_status(DownloadStatus.COMPLETED)
            
            return DownloadResult(
                success=True,
                file_path=str(output_file),
                file_size=output_file.stat().st_size if output_file.exists() else 0,
                download_time=time.time() - self._start_time
            )
        else:
            # Some segments failed
            failed_segments = [i for i, result in enumerate(results) if not (isinstance(result, bool) and result)]
            raise Exception(f"Segments {failed_segments} failed to download")
    
    async def _download_segment_range(self, segment: SegmentInfo, options: DownloadOptions) -> bool:
        """Download a specific byte range segment"""
        for attempt in range(self.max_retries):
            try:
                headers = {
                    'Range': f'bytes={segment.start_byte}-{segment.end_byte}'
                }
                
                proxy = self.proxy_config.proxy_url if self.proxy_config else None
                
                async with self.session.get(segment.url, headers=headers, proxy=proxy) as response:
                    if response.status in [200, 206]:
                        async with aiofiles.open(segment.temp_file, 'wb') as f:
                            downloaded = 0
                            async for chunk in response.content.iter_chunked(8192):
                                if self._cancelled:
                                    return False
                                
                                while self._paused:
                                    await asyncio.sleep(0.1)
                                
                                # Apply rate limiting
                                if self.rate_limiter:
                                    await self.rate_limiter.acquire(len(chunk))
                                
                                await f.write(chunk)
                                downloaded += len(chunk)
                                
                                # Update progress
                                self._downloaded_size += len(chunk)
                                self._update_segment_progress()
                        
                        segment.completed = True
                        return True
                    else:
                        logger.warning(f"Segment {segment.segment_id} download failed with status {response.status}")
                        
            except Exception as e:
                logger.warning(f"Segment {segment.segment_id} download attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
        
        return False
    
    async def _merge_segments(self, output_file: Path, resume_position: int) -> None:
        """Merge downloaded segments into final file"""
        # If resuming, we need to append to existing file
        mode = 'ab' if resume_position > 0 else 'wb'
        
        async with aiofiles.open(output_file, mode) as outf:
            for segment in sorted(self._segments, key=lambda s: s.segment_id):
                temp_file = Path(segment.temp_file)
                if temp_file.exists():
                    async with aiofiles.open(temp_file, 'rb') as inf:
                        while True:
                            chunk = await inf.read(65536)
                            if not chunk:
                                break
                            await outf.write(chunk)
                    
                    # Clean up temp file
                    try:
                        temp_file.unlink()
                    except:
                        pass
    
    async def _download_single_thread(self, url: str, output_file: Path, resume_position: int, options: DownloadOptions) -> DownloadResult:
        """Download file using single thread with resume support"""
        logger.info("Starting single-threaded download")
        
        headers = {}
        if resume_position > 0:
            headers['Range'] = f'bytes={resume_position}-'
        
        mode = 'ab' if resume_position > 0 else 'wb'
        proxy = self.proxy_config.proxy_url if self.proxy_config else None
        
        async with self.session.get(url, headers=headers, proxy=proxy) as response:
            if response.status not in [200, 206]:
                raise Exception(f"HTTP {response.status}: {response.reason}")
            
            async with aiofiles.open(output_file, mode) as f:
                downloaded = resume_position
                async for chunk in response.content.iter_chunked(8192):
                    if self._cancelled:
                        return DownloadResult(success=False, error_message="Download cancelled")
                    
                    while self._paused:
                        await asyncio.sleep(0.1)
                    
                    # Apply rate limiting
                    if self.rate_limiter:
                        await self.rate_limiter.acquire(len(chunk))
                    
                    await f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Update progress
                    if self._total_size:
                        percentage = (downloaded / self._total_size) * 100
                    else:
                        percentage = 0
                    
                    progress = ProgressInfo(
                        downloaded_bytes=downloaded,
                        total_bytes=self._total_size,
                        percentage=percentage,
                        speed=self._calculate_speed()
                    )
                    self._update_progress(progress)
        
        self._update_status(DownloadStatus.COMPLETED)
        
        return DownloadResult(
            success=True,
            file_path=str(output_file),
            file_size=output_file.stat().st_size if output_file.exists() else 0,
            download_time=time.time() - self._start_time
        )
    
    def _update_segment_progress(self) -> None:
        """Update progress based on segment downloads"""
        if self._total_size:
            percentage = (self._downloaded_size / self._total_size) * 100
        else:
            percentage = 0
        
        progress = ProgressInfo(
            downloaded_bytes=self._downloaded_size,
            total_bytes=self._total_size,
            percentage=percentage,
            speed=self._calculate_speed()
        )
        self._update_progress(progress)
    
    def _calculate_speed(self) -> float:
        """Calculate current download speed"""
        elapsed = time.time() - self._start_time
        if elapsed > 0:
            return self._downloaded_size / elapsed
        return 0.0
    
    def _generate_filename(self, url: str, options: DownloadOptions, extension: str = None) -> str:
        """Generate filename from URL and options"""
        if extension:
            return f"download_{int(time.time())}.{extension}"
        
        # Extract filename from URL
        parsed = urlparse(url)
        filename = Path(parsed.path).name
        
        if not filename or '.' not in filename:
            filename = f"download_{int(time.time())}.mp4"
        
        return filename
    
    async def get_metadata(self, url: str) -> VideoMetadata:
        """Extract metadata (basic implementation)"""
        from datetime import datetime
        
        # For advanced downloader, we provide basic metadata
        # Real metadata extraction should be done by specific extractors
        return VideoMetadata(
            title="Advanced Download",
            author="Unknown",
            thumbnail_url="",
            duration=0,
            view_count=0,
            upload_date=datetime.now(),
            quality_options=[]
        )
    
    async def pause(self) -> None:
        """Pause download"""
        self._paused = True
        self._update_status(DownloadStatus.PAUSED)
        logger.info("Download paused")
    
    async def resume(self) -> None:
        """Resume download"""
        self._paused = False
        self._update_status(DownloadStatus.DOWNLOADING)
        logger.info("Download resumed")
    
    async def cancel(self) -> None:
        """Cancel download"""
        self._cancelled = True
        self._update_status(DownloadStatus.CANCELLED)
        logger.info("Download cancelled")