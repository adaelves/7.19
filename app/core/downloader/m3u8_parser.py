"""
M3U8 playlist parser for HLS (HTTP Live Streaming) support.
"""
import re
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class M3U8Segment:
    """Represents a single segment in an M3U8 playlist"""
    uri: str
    duration: float
    title: Optional[str] = None
    byte_range: Optional[str] = None
    discontinuity: bool = False
    key: Optional[Dict[str, str]] = None
    program_date_time: Optional[str] = None
    sequence: Optional[int] = None


@dataclass
class M3U8Playlist:
    """Represents an M3U8 playlist"""
    version: Optional[int] = None
    target_duration: Optional[int] = None
    media_sequence: Optional[int] = None
    is_live: bool = False
    is_endlist: bool = False
    segments: List[M3U8Segment] = None
    
    def __post_init__(self):
        if self.segments is None:
            self.segments = []


class M3U8Parser:
    """
    Parser for M3U8 playlists (HLS - HTTP Live Streaming).
    
    Supports:
    - Basic M3U8 parsing
    - Master playlist parsing (multiple quality streams)
    - Media playlist parsing (segment lists)
    - Encryption key handling
    - Byte range support
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def parse_playlist(self, url: str, session: aiohttp.ClientSession) -> M3U8Playlist:
        """
        Parse M3U8 playlist from URL.
        
        Args:
            url: URL of the M3U8 playlist
            session: HTTP session to use for requests
            
        Returns:
            M3U8Playlist object
        """
        self.session = session
        
        try:
            # Download playlist content
            content = await self._download_playlist(url)
            
            # Check if this is a master playlist or media playlist
            if self._is_master_playlist(content):
                # Parse master playlist and get the best quality stream
                best_stream_url = await self._parse_master_playlist(content, url)
                if best_stream_url:
                    # Download and parse the media playlist
                    media_content = await self._download_playlist(best_stream_url)
                    return self._parse_media_playlist(media_content, best_stream_url)
                else:
                    raise Exception("No suitable stream found in master playlist")
            else:
                # Parse as media playlist directly
                return self._parse_media_playlist(content, url)
                
        except Exception as e:
            logger.error(f"Failed to parse M3U8 playlist: {e}")
            raise e
    
    async def _download_playlist(self, url: str) -> str:
        """Download playlist content from URL"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    return content
                else:
                    raise Exception(f"HTTP {response.status}: Failed to download playlist")
        except Exception as e:
            logger.error(f"Failed to download playlist from {url}: {e}")
            raise e
    
    def _is_master_playlist(self, content: str) -> bool:
        """Check if the playlist is a master playlist"""
        return '#EXT-X-STREAM-INF:' in content
    
    async def _parse_master_playlist(self, content: str, base_url: str) -> Optional[str]:
        """
        Parse master playlist and return the best quality stream URL.
        
        Args:
            content: Playlist content
            base_url: Base URL for resolving relative URLs
            
        Returns:
            URL of the best quality stream
        """
        lines = content.strip().split('\n')
        streams = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('#EXT-X-STREAM-INF:'):
                # Parse stream info
                stream_info = self._parse_stream_inf(line)
                
                # Next line should be the stream URL
                if i + 1 < len(lines):
                    stream_url = lines[i + 1].strip()
                    if not stream_url.startswith('#'):
                        # Resolve relative URL
                        if not stream_url.startswith('http'):
                            stream_url = urljoin(base_url, stream_url)
                        
                        stream_info['url'] = stream_url
                        streams.append(stream_info)
                        i += 1  # Skip the URL line
            
            i += 1
        
        if not streams:
            return None
        
        # Select the best quality stream (highest bandwidth)
        best_stream = max(streams, key=lambda s: s.get('bandwidth', 0))
        logger.info(f"Selected stream: {best_stream.get('resolution', 'unknown')} "
                   f"@ {best_stream.get('bandwidth', 0)} bps")
        
        return best_stream['url']
    
    def _parse_stream_inf(self, line: str) -> Dict[str, Any]:
        """Parse EXT-X-STREAM-INF line"""
        stream_info = {}
        
        # Extract attributes
        attributes = line.split(':', 1)[1] if ':' in line else ''
        
        # Parse bandwidth
        bandwidth_match = re.search(r'BANDWIDTH=(\d+)', attributes)
        if bandwidth_match:
            stream_info['bandwidth'] = int(bandwidth_match.group(1))
        
        # Parse resolution
        resolution_match = re.search(r'RESOLUTION=(\d+x\d+)', attributes)
        if resolution_match:
            stream_info['resolution'] = resolution_match.group(1)
        
        # Parse codecs
        codecs_match = re.search(r'CODECS="([^"]+)"', attributes)
        if codecs_match:
            stream_info['codecs'] = codecs_match.group(1)
        
        # Parse frame rate
        frame_rate_match = re.search(r'FRAME-RATE=([\d.]+)', attributes)
        if frame_rate_match:
            stream_info['frame_rate'] = float(frame_rate_match.group(1))
        
        return stream_info
    
    def _parse_media_playlist(self, content: str, base_url: str) -> M3U8Playlist:
        """
        Parse media playlist (segment list).
        
        Args:
            content: Playlist content
            base_url: Base URL for resolving relative URLs
            
        Returns:
            M3U8Playlist object
        """
        lines = content.strip().split('\n')
        playlist = M3U8Playlist()
        
        current_segment = None
        sequence_number = 0
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('#EXTM3U'):
                # M3U8 header
                continue
            elif line.startswith('#EXT-X-VERSION:'):
                playlist.version = int(line.split(':')[1])
            elif line.startswith('#EXT-X-TARGETDURATION:'):
                playlist.target_duration = int(line.split(':')[1])
            elif line.startswith('#EXT-X-MEDIA-SEQUENCE:'):
                playlist.media_sequence = int(line.split(':')[1])
                sequence_number = playlist.media_sequence
            elif line.startswith('#EXT-X-ENDLIST'):
                playlist.is_endlist = True
            elif line.startswith('#EXTINF:'):
                # Segment info
                duration_info = line.split(':', 1)[1]
                parts = duration_info.split(',', 1)
                duration = float(parts[0])
                title = parts[1] if len(parts) > 1 else None
                
                current_segment = M3U8Segment(
                    uri='',  # Will be set by next non-comment line
                    duration=duration,
                    title=title,
                    sequence=sequence_number
                )
            elif line.startswith('#EXT-X-BYTERANGE:'):
                if current_segment:
                    current_segment.byte_range = line.split(':', 1)[1]
            elif line.startswith('#EXT-X-DISCONTINUITY'):
                if current_segment:
                    current_segment.discontinuity = True
            elif line.startswith('#EXT-X-KEY:'):
                # Encryption key info
                key_info = self._parse_key_line(line)
                if current_segment:
                    current_segment.key = key_info
            elif line.startswith('#EXT-X-PROGRAM-DATE-TIME:'):
                if current_segment:
                    current_segment.program_date_time = line.split(':', 1)[1]
            elif line and not line.startswith('#'):
                # This is a segment URL
                if current_segment:
                    # Resolve relative URL
                    if not line.startswith('http'):
                        segment_url = urljoin(base_url, line)
                    else:
                        segment_url = line
                    
                    current_segment.uri = segment_url
                    playlist.segments.append(current_segment)
                    sequence_number += 1
                    current_segment = None
        
        # Determine if this is a live stream
        playlist.is_live = not playlist.is_endlist
        
        logger.info(f"Parsed M3U8 playlist: {len(playlist.segments)} segments, "
                   f"target duration: {playlist.target_duration}s, "
                   f"live: {playlist.is_live}")
        
        return playlist
    
    def _parse_key_line(self, line: str) -> Dict[str, str]:
        """Parse EXT-X-KEY line for encryption information"""
        key_info = {}
        
        attributes = line.split(':', 1)[1] if ':' in line else ''
        
        # Parse METHOD
        method_match = re.search(r'METHOD=([^,]+)', attributes)
        if method_match:
            key_info['method'] = method_match.group(1)
        
        # Parse URI
        uri_match = re.search(r'URI="([^"]+)"', attributes)
        if uri_match:
            key_info['uri'] = uri_match.group(1)
        
        # Parse IV
        iv_match = re.search(r'IV=0x([0-9A-Fa-f]+)', attributes)
        if iv_match:
            key_info['iv'] = iv_match.group(1)
        
        return key_info
    
    async def get_playlist_info(self, url: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """
        Get basic information about an M3U8 playlist without full parsing.
        
        Args:
            url: URL of the M3U8 playlist
            session: HTTP session to use for requests
            
        Returns:
            Dictionary with playlist information
        """
        try:
            content = await self._download_playlist(url)
            
            info = {
                'url': url,
                'is_master': self._is_master_playlist(content),
                'is_live': '#EXT-X-ENDLIST' not in content,
                'segments_count': content.count('#EXTINF:'),
                'version': None,
                'target_duration': None
            }
            
            # Extract version
            version_match = re.search(r'#EXT-X-VERSION:(\d+)', content)
            if version_match:
                info['version'] = int(version_match.group(1))
            
            # Extract target duration
            duration_match = re.search(r'#EXT-X-TARGETDURATION:(\d+)', content)
            if duration_match:
                info['target_duration'] = int(duration_match.group(1))
            
            # If it's a master playlist, get stream information
            if info['is_master']:
                streams = []
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith('#EXT-X-STREAM-INF:'):
                        stream_info = self._parse_stream_inf(line)
                        if i + 1 < len(lines) and not lines[i + 1].startswith('#'):
                            stream_info['url'] = lines[i + 1].strip()
                        streams.append(stream_info)
                info['streams'] = streams
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get playlist info: {e}")
            return {'error': str(e)}


class M3U8Downloader:
    """
    Specialized downloader for M3U8 playlists with advanced features.
    """
    
    def __init__(self):
        self.parser = M3U8Parser()
    
    async def download_playlist(self, url: str, output_path: str, session: aiohttp.ClientSession,
                              progress_callback: Optional[callable] = None) -> bool:
        """
        Download complete M3U8 playlist.
        
        Args:
            url: M3U8 playlist URL
            output_path: Output file path
            session: HTTP session
            progress_callback: Progress callback function
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Parse playlist
            playlist = await self.parser.parse_playlist(url, session)
            
            if not playlist.segments:
                logger.error("No segments found in playlist")
                return False
            
            # Download segments
            segment_files = []
            total_segments = len(playlist.segments)
            
            for i, segment in enumerate(playlist.segments):
                segment_file = f"{output_path}.segment_{i:06d}"
                
                # Download segment
                success = await self._download_segment(segment, segment_file, session)
                if success:
                    segment_files.append(segment_file)
                    
                    # Progress callback
                    if progress_callback:
                        progress = (i + 1) / total_segments * 100
                        progress_callback(progress)
                else:
                    logger.error(f"Failed to download segment {i}")
                    return False
            
            # Concatenate segments
            await self._concatenate_segments(segment_files, output_path)
            
            # Clean up segment files
            for segment_file in segment_files:
                try:
                    import os
                    os.unlink(segment_file)
                except:
                    pass
            
            return True
            
        except Exception as e:
            logger.error(f"M3U8 download failed: {e}")
            return False
    
    async def _download_segment(self, segment: M3U8Segment, output_file: str, session: aiohttp.ClientSession) -> bool:
        """Download a single segment"""
        try:
            async with session.get(segment.uri) as response:
                if response.status == 200:
                    with open(output_file, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                    return True
                else:
                    logger.error(f"Segment download failed with status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Segment download error: {e}")
            return False
    
    async def _concatenate_segments(self, segment_files: List[str], output_file: str) -> None:
        """Concatenate segment files"""
        with open(output_file, 'wb') as outf:
            for segment_file in segment_files:
                try:
                    with open(segment_file, 'rb') as inf:
                        while True:
                            chunk = inf.read(65536)
                            if not chunk:
                                break
                            outf.write(chunk)
                except Exception as e:
                    logger.error(f"Error concatenating segment {segment_file}: {e}")
                    raise e