"""
TikTok/Douyin extractor plugin for downloading short videos.
Supports TikTok and Douyin URLs.
"""
import re
import json
import aiohttp
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
from datetime import datetime

from app.core.extractor.base import BaseExtractor, ExtractorInfo
from app.data.models.core import VideoMetadata, QualityOption, Platform


class TikTokExtractor(BaseExtractor):
    """
    TikTok/Douyin extractor for downloading short videos.
    Supports tiktok.com and douyin.com URLs.
    """
    
    @property
    def supported_domains(self) -> List[str]:
        return [
            'tiktok.com', 'www.tiktok.com', 'm.tiktok.com',
            'douyin.com', 'www.douyin.com', 'v.douyin.com',
            'vm.tiktok.com'  # Short URLs
        ]
    
    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the given URL"""
        return self._is_supported_domain(url) and self._extract_video_id(url) is not None
    
    async def extract_info(self, url: str) -> Dict[str, Any]:
        """Extract information from TikTok/Douyin URL"""
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid TikTok/Douyin URL")
        
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
        """Extract metadata from TikTok/Douyin URL"""
        info = await self.extract_info(url)
        
        # Parse quality options
        quality_options = self._parse_quality_options(info)
        
        # Create metadata object
        metadata = VideoMetadata(
            title=info.get('title', 'TikTok Video'),
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
            platform=Platform.TIKTOK,
            tags=info.get('tags', [])
        )
        
        return metadata
    
    def get_extractor_info(self) -> ExtractorInfo:
        """Get information about this extractor"""
        return ExtractorInfo(
            name="TikTok/Douyin Extractor",
            version="1.0.0",
            supported_domains=self.supported_domains,
            description="Extract short videos from TikTok and Douyin platforms",
            author="Multi-Platform Video Downloader"
        )
    
    def _parse_quality_options(self, info: Dict[str, Any]) -> List[QualityOption]:
        """Parse quality options from TikTok extracted information"""
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
        """Extract video ID from TikTok/Douyin URL"""
        patterns = [
            r'tiktok\.com/@[^/]+/video/(\d+)',
            r'tiktok\.com/t/([a-zA-Z0-9]+)',
            r'vm\.tiktok\.com/([a-zA-Z0-9]+)',
            r'douyin\.com/video/(\d+)',
            r'v\.douyin\.com/([a-zA-Z0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def _fetch_video_info(self, video_id: str, original_url: str) -> Dict[str, Any]:
        """Fetch video information from TikTok/Douyin (simulated)"""
        # In a real implementation, this would handle TikTok's API or web scraping
        # For now, we'll return simulated data
        
        is_douyin = 'douyin.com' in original_url
        platform_name = 'Douyin' if is_douyin else 'TikTok'
        
        return {
            'id': video_id,
            'title': f'{platform_name} Short Video',
            'description': f'A short video from {platform_name}',
            'uploader': f'{platform_name} User',
            'uploader_id': f'user_{video_id[:8]}',
            'uploader_url': f'https://{"douyin" if is_douyin else "tiktok"}.com/@user_{video_id[:8]}',
            'duration': 30,  # Typical short video duration
            'view_count': 100000,
            'like_count': 5000,
            'comment_count': 200,
            'upload_date': '20240101',
            'thumbnail': f'https://{"douyin" if is_douyin else "tiktok"}.com/thumb/{video_id}.jpg',
            'tags': [platform_name.lower(), 'short', 'video'],
            'formats': [
                {
                    'format_id': 'hd',
                    'url': f'https://{"douyin" if is_douyin else "tiktok"}.com/video/{video_id}_hd.mp4',
                    'height': 1920,
                    'width': 1080,
                    'ext': 'mp4',
                    'vcodec': 'h264',
                    'fps': 30,
                    'tbr': 3000,
                    'filesize': 15 * 1024 * 1024  # 15MB
                },
                {
                    'format_id': 'sd',
                    'url': f'https://{"douyin" if is_douyin else "tiktok"}.com/video/{video_id}_sd.mp4',
                    'height': 1280,
                    'width': 720,
                    'ext': 'mp4',
                    'vcodec': 'h264',
                    'fps': 30,
                    'tbr': 1500,
                    'filesize': 8 * 1024 * 1024  # 8MB
                },
                {
                    'format_id': 'audio',
                    'url': f'https://{"douyin" if is_douyin else "tiktok"}.com/audio/{video_id}.mp3',
                    'ext': 'mp3',
                    'vcodec': 'none',
                    'acodec': 'mp3',
                    'tbr': 128,
                    'filesize': 1 * 1024 * 1024  # 1MB
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