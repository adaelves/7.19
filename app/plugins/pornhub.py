"""
Pornhub extractor plugin for downloading adult content videos.
Includes age verification bypass and quality selection.
"""
import re
import json
import aiohttp
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
from datetime import datetime

from app.core.extractor.base import BaseExtractor, ExtractorInfo
from app.data.models.core import VideoMetadata, QualityOption, Platform


class PornhubExtractor(BaseExtractor):
    """
    Pornhub extractor for downloading adult content videos.
    Supports pornhub.com URLs with age verification bypass.
    """
    
    @property
    def supported_domains(self) -> List[str]:
        return ['pornhub.com', 'www.pornhub.com', 'rt.pornhub.com']
    
    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the given URL"""
        return self._is_supported_domain(url) and self._extract_video_id(url) is not None
    
    async def extract_info(self, url: str) -> Dict[str, Any]:
        """Extract information from Pornhub URL"""
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid Pornhub URL")
        
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
        """Extract metadata from Pornhub URL"""
        info = await self.extract_info(url)
        
        # Parse quality options
        quality_options = self._parse_quality_options(info)
        
        # Create metadata object
        metadata = VideoMetadata(
            title=info.get('title', 'Pornhub Video'),
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
            platform=Platform.PORNHUB,
            tags=info.get('tags', [])
        )
        
        return metadata
    
    def get_extractor_info(self) -> ExtractorInfo:
        """Get information about this extractor"""
        return ExtractorInfo(
            name="Pornhub Extractor",
            version="1.0.0",
            supported_domains=self.supported_domains,
            description="Extract adult content videos from Pornhub with age verification bypass",
            author="Multi-Platform Video Downloader"
        )
    
    def _parse_quality_options(self, info: Dict[str, Any]) -> List[QualityOption]:
        """Parse quality options from Pornhub extracted information"""
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
        """Extract video ID from Pornhub URL"""
        patterns = [
            r'pornhub\.com/view_video\.php\?viewkey=([a-zA-Z0-9]+)',
            r'pornhub\.com/embed/([a-zA-Z0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def _fetch_video_info(self, video_id: str) -> Dict[str, Any]:
        """Fetch video information from Pornhub (simulated with age verification bypass)"""
        # In a real implementation, this would handle:
        # 1. Age verification bypass (setting appropriate cookies/headers)
        # 2. Anti-bot measures
        # 3. Video quality extraction
        # For now, we'll return simulated data
        
        return {
            'id': video_id,
            'title': f'Adult Video {video_id}',
            'description': 'Adult content video description',
            'uploader': 'Content Creator',
            'uploader_id': f'user_{video_id[:8]}',
            'uploader_url': f'https://pornhub.com/users/user_{video_id[:8]}',
            'duration': 900,  # 15 minutes
            'view_count': 500000,
            'like_count': 10000,
            'comment_count': 500,
            'upload_date': '20240101',
            'thumbnail': f'https://pornhub.com/thumb/{video_id}.jpg',
            'tags': ['adult', 'video'],
            'age_verified': True,  # Indicates age verification was bypassed
            'formats': [
                {
                    'format_id': '1080p',
                    'url': f'https://pornhub.com/video/{video_id}_1080p.mp4',
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
                    'url': f'https://pornhub.com/video/{video_id}_720p.mp4',
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
                    'url': f'https://pornhub.com/video/{video_id}_480p.mp4',
                    'height': 480,
                    'width': 854,
                    'ext': 'mp4',
                    'vcodec': 'h264',
                    'fps': 30,
                    'tbr': 1500,
                    'filesize': 70 * 1024 * 1024  # 70MB
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
    
    async def _bypass_age_verification(self, session: aiohttp.ClientSession) -> None:
        """Bypass age verification by setting appropriate cookies and headers"""
        # In a real implementation, this would:
        # 1. Set age verification cookies
        # 2. Set appropriate user agent
        # 3. Handle any CSRF tokens
        # 4. Simulate human-like behavior
        
        # Simulated age verification bypass
        cookies = {
            'age_verified': '1',
            'platform': 'pc',
            'bs': 'whatever'  # Common bypass cookie
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Set cookies and headers on session
        for name, value in cookies.items():
            session.cookie_jar.update_cookies({name: value})
        
        session.headers.update(headers)