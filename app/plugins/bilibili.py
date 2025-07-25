"""
Bilibili extractor plugin for downloading videos from Bilibili.
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


class BilibiliExtractor(BaseExtractor):
    """
    Bilibili extractor for downloading videos from Bilibili.
    Supports bilibili.com URLs with BV and AV IDs.
    """
    
    @property
    def supported_domains(self) -> List[str]:
        return ['bilibili.com', 'www.bilibili.com', 'b23.tv', 'm.bilibili.com']
    
    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the given URL"""
        return self._is_supported_domain(url) and self._extract_video_id(url) is not None
    
    async def extract_info(self, url: str) -> Dict[str, Any]:
        """Extract information from Bilibili URL"""
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid Bilibili URL")
        
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
        """Extract metadata from Bilibili URL"""
        info = await self.extract_info(url)
        
        # Parse quality options
        quality_options = self._parse_quality_options(info)
        
        # Create metadata object
        metadata = VideoMetadata(
            title=info.get('title', 'Unknown Title'),
            author=info.get('uploader', 'Unknown UP主'),
            thumbnail_url=info.get('thumbnail', ''),
            duration=info.get('duration', 0),
            view_count=info.get('view_count', 0),
            upload_date=self._parse_upload_date(info.get('upload_date', '')),
            quality_options=quality_options,
            description=info.get('description', ''),
            like_count=info.get('like_count'),
            comment_count=info.get('comment_count'),
            channel_id=info.get('uploader_id'),
            channel_url=info.get('uploader_url'),
            video_id=info.get('id'),
            platform=Platform.BILIBILI,
            tags=info.get('tags', [])
        )
        
        return metadata
    
    def get_extractor_info(self) -> ExtractorInfo:
        """Get information about this extractor"""
        return ExtractorInfo(
            name="Bilibili Extractor",
            version="1.0.0",
            supported_domains=self.supported_domains,
            description="Extract videos from Bilibili with support for various qualities and formats",
            author="Multi-Platform Video Downloader"
        )
    
    def _parse_quality_options(self, info: Dict[str, Any]) -> List[QualityOption]:
        """Parse quality options from Bilibili extracted information"""
        quality_options = []
        
        if 'formats' in info:
            for format_info in info['formats']:
                quality_option = QualityOption(
                    quality_id=format_info.get('format_id', 'unknown'),
                    resolution=f"{format_info.get('width', 0)}x{format_info.get('height', 0)}",
                    format_name=format_info.get('ext', 'mp4'),
                    file_size=format_info.get('filesize'),
                    bitrate=format_info.get('tbr'),
                    fps=format_info.get('fps'),
                    codec=format_info.get('vcodec'),
                    is_audio_only=format_info.get('vcodec') == 'none'
                )
                quality_options.append(quality_option)
        
        return quality_options
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from Bilibili URL"""
        patterns = [
            r'bilibili\.com/video/(BV[a-zA-Z0-9]+)',
            r'bilibili\.com/video/(av\d+)',
            r'b23\.tv/([a-zA-Z0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def _fetch_video_info(self, video_id: str) -> Dict[str, Any]:
        """Fetch video information from Bilibili (simulated)"""
        # In a real implementation, this would use Bilibili API
        # For now, we'll return simulated data
        
        return {
            'id': video_id,
            'title': f'Bilibili视频 {video_id}',
            'description': 'B站视频描述',
            'uploader': 'UP主名称',
            'uploader_id': 'uid123456',
            'uploader_url': 'https://space.bilibili.com/123456',
            'duration': 600,  # 10 minutes
            'view_count': 50000,
            'like_count': 2000,
            'comment_count': 300,
            'upload_date': '20240101',
            'thumbnail': f'https://i0.hdslb.com/bfs/archive/{video_id}.jpg',
            'tags': ['bilibili', '视频'],
            'formats': [
                {
                    'format_id': '120',  # 4K
                    'url': f'https://bilibili.com/video/{video_id}_4k.mp4',
                    'height': 2160,
                    'width': 3840,
                    'ext': 'mp4',
                    'vcodec': 'avc1.640033',
                    'fps': 60,
                    'tbr': 8000,
                    'filesize': 200 * 1024 * 1024  # 200MB
                },
                {
                    'format_id': '116',  # 1080P60
                    'url': f'https://bilibili.com/video/{video_id}_1080p60.mp4',
                    'height': 1080,
                    'width': 1920,
                    'ext': 'mp4',
                    'vcodec': 'avc1.640028',
                    'fps': 60,
                    'tbr': 6000,
                    'filesize': 150 * 1024 * 1024  # 150MB
                },
                {
                    'format_id': '80',   # 1080P
                    'url': f'https://bilibili.com/video/{video_id}_1080p.mp4',
                    'height': 1080,
                    'width': 1920,
                    'ext': 'mp4',
                    'vcodec': 'avc1.640028',
                    'fps': 30,
                    'tbr': 4000,
                    'filesize': 100 * 1024 * 1024  # 100MB
                },
                {
                    'format_id': '64',   # 720P
                    'url': f'https://bilibili.com/video/{video_id}_720p.mp4',
                    'height': 720,
                    'width': 1280,
                    'ext': 'mp4',
                    'vcodec': 'avc1.4d401f',
                    'fps': 30,
                    'tbr': 2500,
                    'filesize': 60 * 1024 * 1024  # 60MB
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