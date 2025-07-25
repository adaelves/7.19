"""
Instagram extractor plugin for downloading photos, videos, and stories.
Supports Instagram posts, reels, and IGTV.
"""
import re
import json
import aiohttp
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
from datetime import datetime

from app.core.extractor.base import BaseExtractor, ExtractorInfo
from app.data.models.core import VideoMetadata, QualityOption, Platform


class InstagramExtractor(BaseExtractor):
    """
    Instagram extractor for downloading photos, videos, and stories.
    Supports instagram.com URLs for posts, reels, and IGTV.
    """
    
    @property
    def supported_domains(self) -> List[str]:
        return ['instagram.com', 'www.instagram.com', 'instagr.am']
    
    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the given URL"""
        return self._is_supported_domain(url) and self._extract_media_id(url) is not None
    
    async def extract_info(self, url: str) -> Dict[str, Any]:
        """Extract information from Instagram URL"""
        media_id = self._extract_media_id(url)
        if not media_id:
            raise ValueError("Invalid Instagram URL")
        
        info = await self._fetch_media_info(media_id, url)
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
        """Extract metadata from Instagram URL"""
        info = await self.extract_info(url)
        
        # Parse quality options
        quality_options = self._parse_quality_options(info)
        
        # Create metadata object
        metadata = VideoMetadata(
            title=info.get('title', 'Instagram Post'),
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
            platform=Platform.INSTAGRAM,
            tags=info.get('tags', [])
        )
        
        return metadata
    
    def get_extractor_info(self) -> ExtractorInfo:
        """Get information about this extractor"""
        return ExtractorInfo(
            name="Instagram Extractor",
            version="1.0.0",
            supported_domains=self.supported_domains,
            description="Extract photos, videos, and stories from Instagram",
            author="Multi-Platform Video Downloader"
        )
    
    def _parse_quality_options(self, info: Dict[str, Any]) -> List[QualityOption]:
        """Parse quality options from Instagram extracted information"""
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
    
    def _extract_media_id(self, url: str) -> Optional[str]:
        """Extract media ID from Instagram URL"""
        patterns = [
            r'instagram\.com/p/([a-zA-Z0-9_-]+)',
            r'instagram\.com/reel/([a-zA-Z0-9_-]+)',
            r'instagram\.com/tv/([a-zA-Z0-9_-]+)',
            r'instagr\.am/p/([a-zA-Z0-9_-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def _fetch_media_info(self, media_id: str, original_url: str) -> Dict[str, Any]:
        """Fetch media information from Instagram (simulated)"""
        # In a real implementation, this would handle Instagram's API or web scraping
        # For now, we'll return simulated data
        
        media_type = self._determine_media_type(original_url)
        
        return {
            'id': media_id,
            'title': f'Instagram {media_type}',
            'description': f'An Instagram {media_type.lower()}',
            'uploader': 'Instagram User',
            'uploader_id': f'user_{media_id[:8]}',
            'uploader_url': f'https://instagram.com/user_{media_id[:8]}',
            'duration': 60 if media_type in ['Reel', 'IGTV'] else 0,
            'view_count': 10000,
            'like_count': 500,
            'comment_count': 50,
            'upload_date': '20240101',
            'thumbnail': f'https://instagram.com/thumb/{media_id}.jpg',
            'tags': ['instagram', media_type.lower()],
            'media_type': media_type,
            'formats': self._get_formats_for_media_type(media_id, media_type)
        }
    
    def _determine_media_type(self, url: str) -> str:
        """Determine the type of Instagram media from URL"""
        if '/reel/' in url:
            return 'Reel'
        elif '/tv/' in url:
            return 'IGTV'
        elif '/p/' in url:
            return 'Post'
        else:
            return 'Media'
    
    def _get_formats_for_media_type(self, media_id: str, media_type: str) -> List[Dict[str, Any]]:
        """Get format options based on media type"""
        if media_type in ['Reel', 'IGTV']:
            # Video formats
            return [
                {
                    'format_id': 'hd',
                    'url': f'https://instagram.com/video/{media_id}_hd.mp4',
                    'height': 1920,
                    'width': 1080,
                    'ext': 'mp4',
                    'vcodec': 'h264',
                    'fps': 30,
                    'tbr': 2500,
                    'filesize': 25 * 1024 * 1024  # 25MB
                },
                {
                    'format_id': 'sd',
                    'url': f'https://instagram.com/video/{media_id}_sd.mp4',
                    'height': 1280,
                    'width': 720,
                    'ext': 'mp4',
                    'vcodec': 'h264',
                    'fps': 30,
                    'tbr': 1500,
                    'filesize': 15 * 1024 * 1024  # 15MB
                }
            ]
        else:
            # Photo formats
            return [
                {
                    'format_id': 'original',
                    'url': f'https://instagram.com/photo/{media_id}_original.jpg',
                    'height': 1080,
                    'width': 1080,
                    'ext': 'jpg',
                    'vcodec': 'none',
                    'filesize': 2 * 1024 * 1024  # 2MB
                },
                {
                    'format_id': 'medium',
                    'url': f'https://instagram.com/photo/{media_id}_medium.jpg',
                    'height': 640,
                    'width': 640,
                    'ext': 'jpg',
                    'vcodec': 'none',
                    'filesize': 500 * 1024  # 500KB
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