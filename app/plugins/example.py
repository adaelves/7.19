"""
Example plugin for testing the plugin system.
This plugin demonstrates how to create a basic extractor.
"""
import re
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs

from app.core.extractor.base import BaseExtractor, ExtractorInfo
from app.data.models.core import VideoMetadata, QualityOption


class ExampleExtractor(BaseExtractor):
    """
    Example extractor for demonstration purposes.
    This extractor handles example.com URLs.
    """
    
    @property
    def supported_domains(self) -> List[str]:
        return ['example.com', 'www.example.com']
    
    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the given URL"""
        domain = self._extract_domain(url)
        return any(supported in domain for supported in self.supported_domains)
    
    async def extract_info(self, url: str) -> Dict[str, Any]:
        """Extract information from the URL"""
        # Parse URL to extract video ID
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        video_id = query_params.get('v', ['unknown'])[0]
        
        # Simulate extracted information
        info = {
            'id': video_id,
            'title': f'Example Video {video_id}',
            'description': 'This is an example video for testing',
            'uploader': 'Example User',
            'duration': 120,  # 2 minutes
            'view_count': 1000,
            'upload_date': '20240101',
            'thumbnail': f'https://example.com/thumb/{video_id}.jpg',
            'formats': [
                {
                    'format_id': '720p',
                    'url': f'https://example.com/video/{video_id}_720p.mp4',
                    'height': 720,
                    'width': 1280,
                    'ext': 'mp4',
                    'filesize': 50 * 1024 * 1024  # 50MB
                },
                {
                    'format_id': '480p',
                    'url': f'https://example.com/video/{video_id}_480p.mp4',
                    'height': 480,
                    'width': 854,
                    'ext': 'mp4',
                    'filesize': 25 * 1024 * 1024  # 25MB
                }
            ]
        }
        
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
        """Extract metadata from the URL"""
        info = await self.extract_info(url)
        
        # Parse quality options
        quality_options = []
        if 'formats' in info:
            for format_info in info['formats']:
                quality_option = QualityOption(
                    quality_id=format_info.get('format_id', 'unknown'),
                    resolution=f"{format_info.get('width', 0)}x{format_info.get('height', 0)}",
                    format_name=format_info.get('ext', 'mp4'),
                    file_size=format_info.get('filesize', 0),
                    fps=30  # Default FPS
                )
                quality_options.append(quality_option)
        
        # Create metadata object
        from datetime import datetime
        
        metadata = VideoMetadata(
            title=info.get('title', 'Unknown Title'),
            author=info.get('uploader', 'Unknown Author'),
            thumbnail_url=info.get('thumbnail', ''),
            duration=info.get('duration', 0),
            view_count=info.get('view_count', 0),
            upload_date=datetime.strptime(info.get('upload_date', '20240101'), '%Y%m%d'),
            quality_options=quality_options
        )
        
        return metadata
    
    def get_extractor_info(self) -> ExtractorInfo:
        """Get information about this extractor"""
        return ExtractorInfo(
            name="Example Extractor",
            version="1.0.0",
            supported_domains=self.supported_domains,
            description="Example extractor for testing the plugin system",
            author="Plugin System Developer"
        )
    
    def _parse_quality_options(self, info: Dict[str, Any]) -> List[QualityOption]:
        """Parse quality options from extracted information"""
        quality_options = []
        
        if 'formats' in info:
            for format_info in info['formats']:
                quality_option = QualityOption(
                    quality_id=format_info.get('format_id', 'unknown'),
                    resolution=f"{format_info.get('width', 0)}x{format_info.get('height', 0)}",
                    format_name=format_info.get('ext', 'mp4'),
                    file_size=format_info.get('filesize', 0),
                    fps=30  # Default FPS
                )
                quality_options.append(quality_option)
        
        return quality_options