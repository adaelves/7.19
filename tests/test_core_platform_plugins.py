"""
Test cases for core platform plugins.
"""
import pytest
import asyncio
from datetime import datetime

from app.plugins.youtube import YouTubeExtractor
from app.plugins.bilibili import BilibiliExtractor
from app.plugins.tiktok import TikTokExtractor
from app.plugins.instagram import InstagramExtractor
from app.plugins.pornhub import PornhubExtractor
from app.data.models.core import Platform


class TestYouTubeExtractor:
    """Test YouTube extractor functionality"""
    
    def setup_method(self):
        self.extractor = YouTubeExtractor()
    
    def test_supported_domains(self):
        """Test supported domains"""
        expected_domains = ['youtube.com', 'www.youtube.com', 'youtu.be', 'm.youtube.com']
        assert self.extractor.supported_domains == expected_domains
    
    def test_can_handle_valid_urls(self):
        """Test URL handling for valid YouTube URLs"""
        valid_urls = [
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'https://youtu.be/dQw4w9WgXcQ',
            'https://youtube.com/watch?v=dQw4w9WgXcQ',
            'https://m.youtube.com/watch?v=dQw4w9WgXcQ'
        ]
        
        for url in valid_urls:
            assert self.extractor.can_handle(url), f"Should handle URL: {url}"
    
    def test_can_handle_invalid_urls(self):
        """Test URL handling for invalid URLs"""
        invalid_urls = [
            'https://vimeo.com/123456',
            'https://example.com/video',
            'https://youtube.com/invalid',
            'not_a_url'
        ]
        
        for url in invalid_urls:
            assert not self.extractor.can_handle(url), f"Should not handle URL: {url}"
    
    @pytest.mark.asyncio
    async def test_extract_info(self):
        """Test information extraction"""
        url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        info = await self.extractor.extract_info(url)
        
        assert 'id' in info
        assert 'title' in info
        assert 'formats' in info
        assert info['id'] == 'dQw4w9WgXcQ'
    
    @pytest.mark.asyncio
    async def test_get_metadata(self):
        """Test metadata extraction"""
        url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        metadata = await self.extractor.get_metadata(url)
        
        assert metadata.platform == Platform.YOUTUBE
        assert metadata.video_id == 'dQw4w9WgXcQ'
        assert len(metadata.quality_options) > 0
        assert isinstance(metadata.upload_date, datetime)


class TestBilibiliExtractor:
    """Test Bilibili extractor functionality"""
    
    def setup_method(self):
        self.extractor = BilibiliExtractor()
    
    def test_supported_domains(self):
        """Test supported domains"""
        expected_domains = ['bilibili.com', 'www.bilibili.com', 'b23.tv', 'm.bilibili.com']
        assert self.extractor.supported_domains == expected_domains
    
    def test_can_handle_valid_urls(self):
        """Test URL handling for valid Bilibili URLs"""
        valid_urls = [
            'https://www.bilibili.com/video/BV1xx411c7mD',
            'https://bilibili.com/video/av123456',
            'https://b23.tv/abc123',
            'https://m.bilibili.com/video/BV1xx411c7mD'
        ]
        
        for url in valid_urls:
            assert self.extractor.can_handle(url), f"Should handle URL: {url}"
    
    @pytest.mark.asyncio
    async def test_get_metadata(self):
        """Test metadata extraction"""
        url = 'https://www.bilibili.com/video/BV1xx411c7mD'
        metadata = await self.extractor.get_metadata(url)
        
        assert metadata.platform == Platform.BILIBILI
        assert len(metadata.quality_options) > 0


class TestTikTokExtractor:
    """Test TikTok extractor functionality"""
    
    def setup_method(self):
        self.extractor = TikTokExtractor()
    
    def test_supported_domains(self):
        """Test supported domains"""
        expected_domains = [
            'tiktok.com', 'www.tiktok.com', 'm.tiktok.com',
            'douyin.com', 'www.douyin.com', 'v.douyin.com',
            'vm.tiktok.com'
        ]
        assert self.extractor.supported_domains == expected_domains
    
    def test_can_handle_valid_urls(self):
        """Test URL handling for valid TikTok URLs"""
        valid_urls = [
            'https://www.tiktok.com/@user/video/123456789',
            'https://vm.tiktok.com/abc123',
            'https://v.douyin.com/xyz789'
        ]
        
        for url in valid_urls:
            assert self.extractor.can_handle(url), f"Should handle URL: {url}"
    
    @pytest.mark.asyncio
    async def test_get_metadata(self):
        """Test metadata extraction"""
        url = 'https://www.tiktok.com/@user/video/123456789'
        metadata = await self.extractor.get_metadata(url)
        
        assert metadata.platform == Platform.TIKTOK
        assert len(metadata.quality_options) > 0


class TestInstagramExtractor:
    """Test Instagram extractor functionality"""
    
    def setup_method(self):
        self.extractor = InstagramExtractor()
    
    def test_supported_domains(self):
        """Test supported domains"""
        expected_domains = ['instagram.com', 'www.instagram.com', 'instagr.am']
        assert self.extractor.supported_domains == expected_domains
    
    def test_can_handle_valid_urls(self):
        """Test URL handling for valid Instagram URLs"""
        valid_urls = [
            'https://www.instagram.com/p/ABC123/',
            'https://instagram.com/reel/XYZ789/',
            'https://www.instagram.com/tv/DEF456/'
        ]
        
        for url in valid_urls:
            assert self.extractor.can_handle(url), f"Should handle URL: {url}"
    
    @pytest.mark.asyncio
    async def test_get_metadata(self):
        """Test metadata extraction"""
        url = 'https://www.instagram.com/p/ABC123/'
        metadata = await self.extractor.get_metadata(url)
        
        assert metadata.platform == Platform.INSTAGRAM
        assert len(metadata.quality_options) > 0


class TestPornhubExtractor:
    """Test Pornhub extractor functionality"""
    
    def setup_method(self):
        self.extractor = PornhubExtractor()
    
    def test_supported_domains(self):
        """Test supported domains"""
        expected_domains = ['pornhub.com', 'www.pornhub.com', 'rt.pornhub.com']
        assert self.extractor.supported_domains == expected_domains
    
    def test_can_handle_valid_urls(self):
        """Test URL handling for valid Pornhub URLs"""
        valid_urls = [
            'https://www.pornhub.com/view_video.php?viewkey=abc123',
            'https://pornhub.com/embed/xyz789'
        ]
        
        for url in valid_urls:
            assert self.extractor.can_handle(url), f"Should handle URL: {url}"
    
    @pytest.mark.asyncio
    async def test_get_metadata(self):
        """Test metadata extraction"""
        url = 'https://www.pornhub.com/view_video.php?viewkey=abc123'
        metadata = await self.extractor.get_metadata(url)
        
        assert metadata.platform == Platform.PORNHUB
        assert len(metadata.quality_options) > 0


class TestExtractorInfo:
    """Test extractor information"""
    
    def test_all_extractors_have_info(self):
        """Test that all extractors provide proper information"""
        extractors = [
            YouTubeExtractor(),
            BilibiliExtractor(),
            TikTokExtractor(),
            InstagramExtractor(),
            PornhubExtractor()
        ]
        
        for extractor in extractors:
            info = extractor.get_extractor_info()
            assert info.name
            assert info.version
            assert info.supported_domains
            assert info.description
            assert info.author


if __name__ == '__main__':
    pytest.main([__file__])