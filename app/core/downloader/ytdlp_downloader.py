"""
yt-dlp based downloader implementation.
"""
import asyncio
import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import logging

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

from .base import BaseDownloader, DownloadStatus, ProgressInfo
from app.data.models.core import VideoMetadata, DownloadOptions, DownloadResult, QualityOption, Platform

logger = logging.getLogger(__name__)


class YtDlpDownloader(BaseDownloader):
    """
    yt-dlp based downloader implementation.
    Provides unified interface for downloading from various platforms.
    """
    
    def __init__(self):
        super().__init__()
        if yt_dlp is None:
            raise ImportError("yt-dlp is not installed. Please install it with: pip install yt-dlp")
        
        self._ydl = None
        self._current_task = None
        self._cancelled = False
    
    def _create_ydl_opts(self, options: DownloadOptions) -> Dict[str, Any]:
        """Create yt-dlp options from DownloadOptions"""
        opts = {
            'outtmpl': os.path.join(options.output_path, options.filename_template),
            'format': self._get_format_selector(options),
            'writesubtitles': bool(options.subtitle_languages),
            'writeautomaticsub': bool(options.subtitle_languages),
            'subtitleslangs': options.subtitle_languages or [],
            'ignoreerrors': False,
            'no_warnings': False,
            'extractflat': False,
            'writethumbnail': False,
            'writeinfojson': False,
            # FFmpeg post-processing options
            'postprocessors': self._get_postprocessors(options),
        }
        
        # Advanced options
        if options.proxy_url:
            opts['proxy'] = options.proxy_url
        
        if options.cookies_file:
            opts['cookiefile'] = options.cookies_file
        
        if options.user_agent:
            opts['http_headers'] = {'User-Agent': options.user_agent}
        
        # Speed limit
        if options.speed_limit:
            opts['ratelimit'] = options.speed_limit * 1024  # Convert KB/s to bytes/s
        
        # Resume support
        if options.enable_resume:
            opts['continuedl'] = True
        
        # Overwrite settings
        opts['overwrites'] = options.overwrite_existing
        
        return opts
    
    def _get_postprocessors(self, options: DownloadOptions) -> list[Dict[str, Any]]:
        """Get FFmpeg post-processors for yt-dlp"""
        postprocessors = []
        
        # Audio conversion if needed
        if options.audio_only:
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            })
        
        # Video format conversion if needed
        if options.format_preference and options.format_preference != 'best':
            postprocessors.append({
                'key': 'FFmpegVideoConvertor',
                'preferedformat': options.format_preference,
            })
        
        # Subtitle embedding
        if options.subtitle_languages:
            postprocessors.append({
                'key': 'FFmpegEmbedSubtitle',
            })
        
        return postprocessors
    
    def _get_format_selector(self, options: DownloadOptions) -> str:
        """Generate format selector string for yt-dlp"""
        if options.audio_only:
            return 'bestaudio/best'
        
        quality = options.quality_preference or 'best'
        format_pref = options.format_preference or 'mp4'
        
        if quality == 'best':
            return f'best[ext={format_pref}]/best'
        elif quality == 'worst':
            return f'worst[ext={format_pref}]/worst'
        else:
            # Specific quality (e.g., "720p", "1080p")
            height = quality.replace('p', '') if 'p' in quality else quality
            return f'best[height<={height}][ext={format_pref}]/best[height<={height}]/best'
    
    def _progress_hook(self, d: Dict[str, Any]):
        """Progress hook for yt-dlp"""
        if self._cancelled:
            raise yt_dlp.DownloadError("Download cancelled by user")
        
        status = d.get('status')
        if status == 'downloading':
            self._update_status(DownloadStatus.DOWNLOADING)
            
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            speed = d.get('speed', 0) or 0
            eta = d.get('eta')
            
            percentage = (downloaded / total * 100) if total > 0 else 0
            
            progress = ProgressInfo(
                downloaded_bytes=downloaded,
                total_bytes=total,
                speed=speed,
                eta=eta,
                percentage=percentage
            )
            
            self._update_progress(progress)
            
        elif status == 'finished':
            self._update_status(DownloadStatus.COMPLETED)
            
            # Final progress update
            total = d.get('total_bytes', 0)
            progress = ProgressInfo(
                downloaded_bytes=total,
                total_bytes=total,
                speed=0,
                eta=0,
                percentage=100.0
            )
            self._update_progress(progress)
    
    async def download(self, url: str, options: DownloadOptions) -> DownloadResult:
        """Download content from URL"""
        try:
            self._cancelled = False
            self._update_status(DownloadStatus.DOWNLOADING)
            
            # Create yt-dlp options
            ydl_opts = self._create_ydl_opts(options)
            ydl_opts['progress_hooks'] = [self._progress_hook]
            
            # Ensure output directory exists
            Path(options.output_path).mkdir(parents=True, exist_ok=True)
            
            # Run download in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._download_sync, 
                url, 
                ydl_opts
            )
            
            return result
            
        except Exception as e:
            self._update_status(DownloadStatus.FAILED)
            logger.error(f"Download failed: {e}")
            return DownloadResult(
                success=False,
                error_message=str(e)
            )
    
    def _download_sync(self, url: str, ydl_opts: Dict[str, Any]) -> DownloadResult:
        """Synchronous download method"""
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self._ydl = ydl
                
                # Extract info first
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise Exception("Could not extract video information")
                
                # Download the video
                ydl.download([url])
                
                # Get file info
                filename = ydl.prepare_filename(info)
                file_path = Path(filename)
                
                file_size = file_path.stat().st_size if file_path.exists() else 0
                
                # Create metadata
                metadata = self._create_metadata_from_info(info)
                
                return DownloadResult(
                    success=True,
                    file_path=str(file_path),
                    file_size=file_size,
                    metadata=metadata
                )
                
        except yt_dlp.DownloadError as e:
            if "cancelled" in str(e).lower():
                self._update_status(DownloadStatus.CANCELLED)
                return DownloadResult(success=False, error_message="Download cancelled")
            else:
                raise e
        finally:
            self._ydl = None
    
    async def get_metadata(self, url: str) -> VideoMetadata:
        """Extract metadata without downloading"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                self._extract_info_sync,
                url,
                ydl_opts
            )
            
            return self._create_metadata_from_info(info)
            
        except Exception as e:
            logger.error(f"Failed to extract metadata: {e}")
            raise e
    
    def _extract_info_sync(self, url: str, ydl_opts: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous info extraction"""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    
    def _create_metadata_from_info(self, info: Dict[str, Any]) -> VideoMetadata:
        """Create VideoMetadata from yt-dlp info dict"""
        from datetime import datetime
        
        # Extract basic info
        title = info.get('title', 'Unknown Title')
        uploader = info.get('uploader') or info.get('channel', 'Unknown Author')
        thumbnail = info.get('thumbnail', '')
        duration = info.get('duration', 0) or 0
        view_count = info.get('view_count', 0) or 0
        
        # Parse upload date
        upload_date = datetime.now()
        if info.get('upload_date'):
            try:
                upload_date = datetime.strptime(info['upload_date'], '%Y%m%d')
            except ValueError:
                pass
        
        # Extract quality options
        quality_options = self._extract_quality_options(info)
        
        # Determine platform
        platform = self._determine_platform(info)
        
        return VideoMetadata(
            title=title,
            author=uploader,
            thumbnail_url=thumbnail,
            duration=duration,
            view_count=view_count,
            upload_date=upload_date,
            quality_options=quality_options,
            description=info.get('description', ''),
            tags=info.get('tags', []) or [],
            like_count=info.get('like_count'),
            comment_count=info.get('comment_count'),
            channel_id=info.get('channel_id'),
            channel_url=info.get('channel_url'),
            video_id=info.get('id'),
            platform=platform
        )
    
    def _extract_quality_options(self, info: Dict[str, Any]) -> list[QualityOption]:
        """Extract quality options from yt-dlp info"""
        quality_options = []
        formats = info.get('formats', [])
        
        for fmt in formats:
            if not fmt.get('url'):
                continue
                
            quality_id = fmt.get('format_id', '')
            resolution = f"{fmt.get('width', 0)}x{fmt.get('height', 0)}"
            format_name = fmt.get('ext', 'unknown')
            file_size = fmt.get('filesize') or fmt.get('filesize_approx')
            bitrate = fmt.get('tbr')  # total bitrate
            fps = fmt.get('fps')
            codec = fmt.get('vcodec')
            is_audio_only = fmt.get('vcodec') == 'none'
            
            quality_option = QualityOption(
                quality_id=quality_id,
                resolution=resolution,
                format_name=format_name,
                file_size=file_size,
                bitrate=int(bitrate) if bitrate else None,
                fps=int(fps) if fps else None,
                codec=codec,
                is_audio_only=is_audio_only
            )
            
            quality_options.append(quality_option)
        
        return quality_options
    
    def _determine_platform(self, info: Dict[str, Any]) -> Platform:
        """Determine platform from yt-dlp info"""
        extractor = info.get('extractor', '').lower()
        webpage_url = info.get('webpage_url', '').lower()
        
        if 'youtube' in extractor or 'youtube.com' in webpage_url:
            return Platform.YOUTUBE
        elif 'bilibili' in extractor or 'bilibili.com' in webpage_url:
            return Platform.BILIBILI
        elif 'tiktok' in extractor or 'tiktok.com' in webpage_url:
            return Platform.TIKTOK
        elif 'instagram' in extractor or 'instagram.com' in webpage_url:
            return Platform.INSTAGRAM
        elif 'pornhub' in extractor or 'pornhub.com' in webpage_url:
            return Platform.PORNHUB
        else:
            return Platform.UNKNOWN
    
    async def pause(self) -> None:
        """Pause download (not directly supported by yt-dlp)"""
        self._update_status(DownloadStatus.PAUSED)
        # Note: yt-dlp doesn't support pausing, this is a placeholder
        logger.warning("Pause not directly supported by yt-dlp")
    
    async def resume(self) -> None:
        """Resume download"""
        self._update_status(DownloadStatus.DOWNLOADING)
        # Note: yt-dlp will resume automatically if continuedl is enabled
        logger.info("Resume requested - yt-dlp will continue from where it left off")
    
    async def cancel(self) -> None:
        """Cancel download"""
        self._cancelled = True
        self._update_status(DownloadStatus.CANCELLED)
        logger.info("Download cancellation requested")