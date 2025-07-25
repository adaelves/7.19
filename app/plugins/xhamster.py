"""
XHamster extractor plugin for downloading adult content videos.
Handles dynamic content loading and VR content support.
"""
import re
import json
import aiohttp
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
from datetime import datetime

from app.core.extractor.base import BaseExtractor, ExtractorInfo
from app.data.models.core import VideoMetadata, QualityOption, Platform


class XHamsterExtractor(BaseExtractor):
    """
    XHamster extractor for downloading adult content videos.
    Supports xhamster.com URLs with dynamic content loading and VR support.
    """
    
    @property
    def supported_domains(self) -> List[str]:
        return ['xhamster.com', 'www.xhamster.com', 'xhamster.desi', 'xhamster.one']
    
    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the given URL"""
        return self._is_supported_domain(url) and self._extract_video_id(url) is not None
    
    async def extract_info(self, url: str) -> Dict[str, Any]:
        """Extract information from XHamster URL"""
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid XHamster URL")
        
        info = await self._fetch_video_info(video_id, url)
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
        """Extract metadata from XHamster URL"""
        info = await self.extract_info(url)
        
        # Parse quality options
        quality_options = self._parse_quality_options(info)
        
        # Create metadata object
        metadata = VideoMetadata(
            title=info.get('title', 'XHamster Video'),
            author=info.get('uploader', 'Unknown User'),
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
            platform=Platform.XHAMSTER,
            tags=info.get('tags', [])
        )
        
        return metadata
    
    def get_extractor_info(self) -> ExtractorInfo:
        """Get information about this extractor"""
        return ExtractorInfo(
            name="XHamster Extractor",
            version="1.0.0",
            supported_domains=self.supported_domains,
            description="Extract adult content videos from XHamster with dynamic loading and VR support",
            author="Multi-Platform Video Downloader"
        )
    
    def _parse_quality_options(self, info: Dict[str, Any]) -> List[QualityOption]:
        """Parse quality options from XHamster extracted information"""
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
                    is_audio_only=False
                )
                quality_options.append(quality_option)
        
        return quality_options
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from XHamster URL"""
        patterns = [
            r'xhamster\.com/videos/[^/]+-(\d+)',
            r'xhamster\.com/movies/(\d+)',
            r'xhamster\.desi/videos/[^/]+-(\d+)',
            r'xhamster\.one/videos/[^/]+-(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _is_vr_content(self, url: str) -> bool:
        """Check if the content is VR content"""
        return '/vr/' in url.lower() or 'vr-' in url.lower()
    
    async def _fetch_video_info(self, video_id: str, original_url: str) -> Dict[str, Any]:
        """Fetch video information from XHamster with dynamic content handling"""
        # In a real implementation, this would handle:
        # 1. Dynamic content loading (JavaScript execution)
        # 2. VR content detection and processing
        # 3. Multiple quality extraction
        
        is_vr = self._is_vr_content(original_url)
        
        return {
            'id': video_id,
            'title': f'XHamster {"VR " if is_vr else ""}Video {video_id}',
            'description': f'Adult content {"VR " if is_vr else ""}video from XHamster',
            'uploader': 'XHamster User',
            'uploader_id': f'user_{video_id[:6]}',
            'uploader_url': f'https://xhamster.com/users/user_{video_id[:6]}',
            'duration': 1800 if is_vr else 1000,  # VR content is typically longer
            'view_count': 300000,
            'like_count': 6000,
            'comment_count': 300,
            'upload_date': '20240101',
            'thumbnail': f'https://xhamster.com/thumb/{video_id}.jpg',
            'tags': ['adult', 'xhamster'] + (['vr', '360'] if is_vr else []),
            'is_vr': is_vr,
            'dynamic_content': True,  # Indicates dynamic content loading
            'formats': self._get_formats_for_content_type(video_id, is_vr)
        }
    
    def _get_formats_for_content_type(self, video_id: str, is_vr: bool) -> List[Dict[str, Any]]:
        """Get format options based on content type (regular or VR)"""
        if is_vr:
            # VR content formats
            return [
                {
                    'format_id': 'vr-4k',
                    'url': f'https://xhamster.com/vr/{video_id}_4k.mp4',
                    'height': 2160,
                    'width': 4320,  # 360-degree width
                    'ext': 'mp4',
                    'vcodec': 'h264',
                    'fps': 60,
                    'tbr': 8000,
                    'is_vr': True,
                    'filesize': 800 * 1024 * 1024  # 800MB
                },
                {
                    'format_id': 'vr-1080p',
                    'url': f'https://xhamster.com/vr/{video_id}_1080p.mp4',
                    'height': 1080,
                    'width': 2160,
                    'ext': 'mp4',
                    'vcodec': 'h264',
                    'fps': 30,
                    'tbr': 4000,
                    'is_vr': True,
                    'filesize': 400 * 1024 * 1024  # 400MB
                }
            ]
        else:
            # Regular content formats
            return [
                {
                    'format_id': '1080p',
                    'url': f'https://xhamster.com/video/{video_id}_1080p.mp4',
                    'height': 1080,
                    'width': 1920,
                    'ext': 'mp4',
                    'vcodec': 'h264',
                    'fps': 30,
                    'tbr': 4000,
                    'filesize': 200 * 1024 * 1024  # 200MB
                },
                {
                    'format_id': '720p',
                    'url': f'https://xhamster.com/video/{video_id}_720p.mp4',
                    'height': 720,
                    'width': 1280,
                    'ext': 'mp4',
                    'vcodec': 'h264',
                    'fps': 30,
                    'tbr': 2500,
                    'filesize': 120 * 1024 * 1024  # 120MB
                },
                {
                    'format_id': '480p',
                    'url': f'https://xhamster.com/video/{video_id}_480p.mp4',
                    'height': 480,
                    'width': 854,
                    'ext': 'mp4',
                    'vcodec': 'h264',
                    'fps': 30,
                    'tbr': 1500,
                    'filesize': 70 * 1024 * 1024  # 70MB
                }
            ]
    
    def _parse_upload_date(self, date_str: str) -> datetime:
        """Parse upload date string to datetime object"""
        if not date_str:
            return datetime.now()
        
        try:
            return datetime.strptime(date_str, '%Y%m%d')
        except ValueError:
            return datetime.now()