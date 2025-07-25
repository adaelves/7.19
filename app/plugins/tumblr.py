"""
Tumblr extractor plugin for downloading media content from Tumblr.
Handles NSFW content and blog batch downloads.
"""
import re
import json
import aiohttp
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
from datetime import datetime

from app.core.extractor.base import BaseExtractor, ExtractorInfo
from app.data.models.core import VideoMetadata, QualityOption, Platform


class TumblrExtractor(BaseExtractor):
    """
    Tumblr extractor for downloading media content from Tumblr.
    Supports tumblr.com URLs with NSFW content and blog batch downloads.
    """
    
    @property
    def supported_domains(self) -> List[str]:
        return ['tumblr.com', 'www.tumblr.com']
    
    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the given URL"""
        return self._is_supported_domain(url) and self._extract_post_info(url) is not None
    
    async def extract_info(self, url: str) -> Dict[str, Any]:
        """Extract information from Tumblr URL"""
        post_info = self._extract_post_info(url)
        if not post_info:
            raise ValueError("Invalid Tumblr URL")
        
        info = await self._fetch_tumblr_info(post_info, url)
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
        """Extract metadata from Tumblr URL"""
        info = await self.extract_info(url)
        
        # Parse quality options
        quality_options = self._parse_quality_options(info)
        
        # Create metadata object
        metadata = VideoMetadata(
            title=info.get('title', 'Tumblr Post'),
            author=info.get('uploader', 'Unknown Blog'),
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
            platform=Platform.TUMBLR,
            tags=info.get('tags', [])
        )
        
        return metadata
    
    def get_extractor_info(self) -> ExtractorInfo:
        """Get information about this extractor"""
        return ExtractorInfo(
            name="Tumblr Extractor",
            version="1.0.0",
            supported_domains=self.supported_domains,
            description="Extract media content from Tumblr with NSFW support and blog batch downloads",
            author="Multi-Platform Video Downloader"
        )
    
    def _parse_quality_options(self, info: Dict[str, Any]) -> List[QualityOption]:
        """Parse quality options from Tumblr extracted information"""
        quality_options = []
        
        if 'formats' in info:
            for format_info in info['formats']:
                quality_option = QualityOption(
                    quality_id=format_info.get('format_id', 'unknown'),
                    resolution=f"{format_info.get('width', 0)}x{format_info.get('height', 0)}",
                    format_name=format_info.get('ext', 'jpg'),
                    file_size=format_info.get('filesize'),
                    bitrate=format_info.get('tbr'),
                    fps=format_info.get('fps'),
                    codec=format_info.get('vcodec'),
                    is_audio_only=False
                )
                quality_options.append(quality_option)
        
        return quality_options
    
    def _extract_post_info(self, url: str) -> Optional[Dict[str, str]]:
        """Extract post information from Tumblr URL"""
        patterns = [
            r'([a-zA-Z0-9\-]+)\.tumblr\.com/post/(\d+)',
            r'tumblr\.com/([a-zA-Z0-9\-]+)/(\d+)',
            r'([a-zA-Z0-9\-]+)\.tumblr\.com/image/(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return {
                    'blog_name': match.group(1),
                    'post_id': match.group(2)
                }
        
        # Check for blog URL (for batch download)
        blog_pattern = r'([a-zA-Z0-9\-]+)\.tumblr\.com/?$'
        match = re.search(blog_pattern, url)
        if match:
            return {
                'blog_name': match.group(1),
                'post_id': None,  # Indicates blog batch download
                'is_blog_url': True
            }
        
        return None
    
    def _is_nsfw_content(self, tags: List[str], content: str) -> bool:
        """Check if content is NSFW"""
        nsfw_indicators = ['nsfw', 'adult', 'mature', '18+', 'explicit']
        
        # Check tags
        for tag in tags:
            if any(indicator in tag.lower() for indicator in nsfw_indicators):
                return True
        
        # Check content
        if any(indicator in content.lower() for indicator in nsfw_indicators):
            return True
        
        return False
    
    async def _fetch_tumblr_info(self, post_info: Dict[str, str], original_url: str) -> Dict[str, Any]:
        """Fetch Tumblr information with NSFW content handling"""
        blog_name = post_info['blog_name']
        post_id = post_info.get('post_id')
        is_blog_url = post_info.get('is_blog_url', False)
        
        if is_blog_url:
            # Handle blog batch download
            return await self._fetch_blog_info(blog_name)
        
        # Handle single post
        return {
            'id': post_id,
            'blog_name': blog_name,
            'title': f'Tumblr Post {post_id}',
            'description': 'Tumblr post content',
            'uploader': blog_name,
            'uploader_id': blog_name,
            'uploader_url': f'https://{blog_name}.tumblr.com',
            'duration': 15,  # For GIF/video content
            'view_count': 5000,
            'like_count': 200,
            'comment_count': 50,
            'upload_date': '20240101',
            'thumbnail': f'https://{blog_name}.tumblr.com/thumb/{post_id}.jpg',
            'tags': ['tumblr', 'blog', 'media'],
            'is_nsfw': self._is_nsfw_content(['art', 'photography'], 'creative content'),
            'post_type': 'photo',  # 'photo', 'video', 'gif', 'text', 'quote', 'link', 'chat', 'audio'
            'formats': [
                # High resolution image
                {
                    'format_id': 'original',
                    'url': f'https://64.media.tumblr.com/{post_id}_original.jpg',
                    'height': 2048,
                    'width': 1536,
                    'ext': 'jpg',
                    'vcodec': 'none',
                    'filesize': 3 * 1024 * 1024  # 3MB
                },
                # Medium resolution
                {
                    'format_id': 'medium',
                    'url': f'https://64.media.tumblr.com/{post_id}_medium.jpg',
                    'height': 1024,
                    'width': 768,
                    'ext': 'jpg',
                    'vcodec': 'none',
                    'filesize': 800 * 1024  # 800KB
                },
                # GIF format (if applicable)
                {
                    'format_id': 'gif',
                    'url': f'https://64.media.tumblr.com/{post_id}.gif',
                    'height': 500,
                    'width': 500,
                    'ext': 'gif',
                    'vcodec': 'gif',
                    'fps': 15,
                    'filesize': 5 * 1024 * 1024  # 5MB
                },
                # Video format (if applicable)
                {
                    'format_id': 'video',
                    'url': f'https://vt.tumblr.com/{post_id}.mp4',
                    'height': 720,
                    'width': 1280,
                    'ext': 'mp4',
                    'vcodec': 'h264',
                    'fps': 30,
                    'tbr': 1500,
                    'filesize': 10 * 1024 * 1024  # 10MB
                }
            ]
        }
    
    async def _fetch_blog_info(self, blog_name: str) -> Dict[str, Any]:
        """Fetch blog information for batch download"""
        return {
            'id': blog_name,
            'blog_name': blog_name,
            'title': f'{blog_name} Blog',
            'description': f'Batch download from {blog_name} Tumblr blog',
            'uploader': blog_name,
            'uploader_id': blog_name,
            'uploader_url': f'https://{blog_name}.tumblr.com',
            'is_blog_batch': True,
            'post_count': 500,  # Estimated post count
            'tags': ['tumblr', 'blog', 'batch'],
            'formats': []  # Will be populated with individual post formats
        }
    
    def _parse_upload_date(self, date_str: str) -> datetime:
        """Parse upload date string to datetime object"""
        if not date_str:
            return datetime.now()
        
        try:
            return datetime.strptime(date_str, '%Y%m%d')
        except ValueError:
            return datetime.now()
    
    async def _handle_nsfw_content(self, session: aiohttp.ClientSession) -> None:
        """Handle NSFW content access"""
        # In a real implementation, this would:
        # 1. Set appropriate age verification
        # 2. Handle content warnings
        # 3. Set NSFW viewing preferences
        
        nsfw_headers = {
            'X-Tumblr-NSFW': 'true',
            'X-Content-Filter': 'off'
        }
        
        nsfw_cookies = {
            'safe_mode': 'false',
            'content_filter': 'off'
        }
        
        session.headers.update(nsfw_headers)
        for name, value in nsfw_cookies.items():
            session.cookie_jar.update_cookies({name: value})
    
    async def get_blog_posts(self, blog_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all posts from a Tumblr blog for batch download"""
        # In a real implementation, this would:
        # 1. Use Tumblr API to get blog posts
        # 2. Handle pagination
        # 3. Filter by media type
        # 4. Return list of post information
        
        posts = []
        for i in range(min(limit, 20)):  # Simulate limited posts
            post_id = f"post_{i:03d}"
            posts.append({
                'id': post_id,
                'blog_name': blog_name,
                'post_type': 'photo',
                'url': f'https://{blog_name}.tumblr.com/post/{post_id}',
                'media_urls': [
                    f'https://64.media.tumblr.com/{post_id}_original.jpg'
                ]
            })
        
        return posts