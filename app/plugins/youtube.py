"""
YouTube extractor plugin for downloading videos from YouTube.
Supports various video qualities and formats.
"""
import re
import json
import aiohttp
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
from datetime import datetime

from app.core.extractor.base import BaseExtractor, ExtractorInfo
from app.data.models.core import VideoMetadata, QualityOption, Platform


class YouTubeExtractor(BaseExtractor):
    """
    YouTube extractor for downloading videos from YouTube.
    Supports youtube.com and youtu.be URLs.
    """
    
    @property
    def supported_domains(self) -> List[str]:
        return ['youtube.com', 'www.youtube.com', 'youtu.be', 'm.youtube.com']
    
    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the given URL"""
        return self._is_supported_domain(url) and self._extract_video_id(url) is not None
    
    async def extract_info(self, url: str) -> Dict[str, Any]:
        """Extract information from YouTube URL"""
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")
        
        # Use yt-dlp style extraction (simplified simulation)
        info = await self._fetch_video_info(video_id)
        return info
    
    async def get_download_urls(self, info: Dict[str, Any]) -> List[str]:
        """Get direct download URLs from extracted information"""
        urls = []
        
        if 'formats' in info:
            for format_info in info['formats']:
                if 'url' in format_info:
                    urls.append(format_info['url'])
        
        return urls
    
    async def get_metadata(self, url: str) -> VideoMetadata:
        """Extract metadata from YouTube URL"""
        info = await self.extract_info(url)
        
        # Parse quality options
        quality_options = self._parse_quality_options(info)
        
        # Create metadata object
        metadata = VideoMetadata(
            title=info.get('title', 'Unknown Title'),
            author=info.get('uploader', 'Unknown Channel'),
            thumbnail_url=info.get('thumbnail', ''),
            duration=info.get('duration', 0),
            view_count=info.get('view_count', 0),
            upload_date=self._parse_upload_date(info.get('upload_date', '')),
            quality_options=quality_options,
            description=info.get('description', ''),
            like_count=info.get('like_count'),
            comment_count=info.get('comment_count'),
            channel_id=info.get('channel_id'),
            channel_url=info.get('channel_url'),
            video_id=info.get('id'),
            platform=Platform.YOUTUBE,
            tags=info.get('tags', [])
        )
        
        return metadata
    
    def get_extractor_info(self) -> ExtractorInfo:
        """Get information about this extractor"""
        return ExtractorInfo(
            name="YouTube Extractor",
            version="1.0.0",
            supported_domains=self.supported_domains,
            description="Extract videos from YouTube with support for various qualities and formats",
            author="Multi-Platform Video Downloader"
        )
    
    def _parse_quality_options(self, info: Dict[str, Any]) -> List[QualityOption]:
        """Parse quality options from YouTube extracted information"""
        quality_options = []
        
        if 'formats' in info:
            for format_info in info['formats']:
                # Skip audio-only formats for video quality options
                if format_info.get('vcodec') == 'none':
                    continue
                
                quality_option = QualityOption(
                    quality_id=format_info.get('format_id', 'unknown'),
                    resolution=f"{format_info.get('width', 0)}x{format_info.get('height', 0)}",
                    format_name=format_info.get('ext', 'mp4'),
                    file_size=format_info.get('filesize'),
                    bitrate=format_info.get('tbr'),
                    fps=format_info.get('fps'),
                    codec=format_info.get('vcodec'),
                    is_audio_only=False
                )
                quality_options.append(quality_option)
        
        return quality_options
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/v/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def _fetch_video_info(self, video_id: str) -> Dict[str, Any]:
        """Fetch video information from YouTube (simulated)"""
        # In a real implementation, this would use yt-dlp or YouTube API
        # For now, we'll return simulated data
        
        return {
            'id': video_id,
            'title': f'YouTube Video {video_id}',
            'description': 'A YouTube video description',
            'uploader': 'YouTube Channel',
            'duration': 300,  # 5 minutes
            'view_count': 10000,
            'like_count': 500,
            'comment_count': 50,
            'upload_date': '20240101',
            'thumbnail': f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg',
            'channel_id': 'UC' + video_id[:22],
            'channel_url': f'https://www.youtube.com/channel/UC{video_id[:22]}',
            'tags': ['youtube', 'video'],
            'formats': [
                {
                    'format_id': '137',
                    'url': f'https://youtube.com/video/{video_id}_1080p.mp4',
                    'height': 1080,
                    'width': 1920,
                    'ext': 'mp4',
                    'vcodec': 'avc1.640028',
                    'fps': 30,
                    'tbr': 4000,
                    'filesize': 100 * 1024 * 1024  # 100MB
                },
                {
                    'format_id': '136',
                    'url': f'https://youtube.com/video/{video_id}_720p.mp4',
                    'height': 720,
                    'width': 1280,
                    'ext': 'mp4',
                    'vcodec': 'avc1.4d401f',
                    'fps': 30,
                    'tbr': 2500,
                    'filesize': 60 * 1024 * 1024  # 60MB
                },
                {
                    'format_id': '135',
                    'url': f'https://youtube.com/video/{video_id}_480p.mp4',
                    'height': 480,
                    'width': 854,
                    'ext': 'mp4',
                    'vcodec': 'avc1.4d4015',
                    'fps': 30,
                    'tbr': 1000,
                    'filesize': 30 * 1024 * 1024  # 30MB
                }
            ]
        }
    
    def _parse_upload_date(self, date_str: str) -> datetime:
        """Parse upload date string to datetime object"""
        if not date_str:
            return datetime.now()
        
        try:
            return datetime.strptime(date_str, '%Y%m%d')
        except ValueError:
            return datetime.now()