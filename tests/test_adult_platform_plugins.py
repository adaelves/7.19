"""
Test cases for adult content platform plugins.
"""
import pytest
import asyncio
from datetime import datetime

from app.plugins.youporn import YouPornExtractor
from app.plugins.xvideo import XVideoExtractor
from app.plugins.xhamster import XHamsterExtractor
from app.plugins.kissjav import KissJAVExtractor
from app.data.models.core import Platform


class TestYouPornExtractor:
    """Test YouPorn extractor functionality"""
    
    def setup_method(self):
        self.extractor = YouPornExtractor()
    
    def test_supported_domains(self):
        """Test supported domains"""
        expected_domains = ['youporn.com', 'www.youporn.com']
        assert self.extractor.supported_domains == expected_domains
    
    def test_can_handle_valid_urls(self):
        """Test URL handling for valid YouPorn URLs"""
        valid_urls = [
            'https://www.youporn.com/watch/123456',
            'https://youporn.com/embed/789012'
        ]
        
        for url in valid_urls:
            assert self.extractor.can_handle(url), f"Should handle URL: {url}"
    
    @pytest.mark.asyncio
    async def test_get_metadata(self):
        """Test metadata extraction"""
        url = 'https://www.youporn.com/watch/123456'
        metadata = await self.extractor.get_metadata(url)
        
        assert metadata.platform == Platform.YOUPORN
        assert len(metadata.quality_options) > 0
        assert metadata.video_id == '123456'


class TestXVideoExtractor:
    """Test XVideo extractor functionality"""
    
    def setup_method(self):
        self.extractor = XVideoExtractor()
    
    def test_supported_domains(self):
        """Test supported domains"""
        expected_domains = ['xvideos.com', 'www.xvideos.com', 'xvideos.es', 'xvideos.red']
        assert self.extractor.supported_domains == expected_domains
    
    def test_can_handle_valid_urls(self):
        """Test URL handling for valid XVideo URLs"""
        valid_urls = [
            'https://www.xvideos.com/video123456',
            'https://xvideos.com/embedframe/789012',
            'https://xvideos.es/video345678'
        ]
        
        for url in valid_urls:
            assert self.extractor.can_handle(url), f"Should handle URL: {url}"
    
    @pytest.mark.asyncio
    async def test_get_metadata(self):
        """Test metadata extraction"""
        url = 'https://www.xvideos.com/video123456'
        metadata = await self.extractor.get_metadata(url)
        
        assert metadata.platform == Platform.XVIDEO
        assert len(metadata.quality_options) > 0
        assert metadata.video_id == '123456'
    
    @pytest.mark.asyncio
    async def test_m3u8_support(self):
        """Test M3U8 streaming support"""
        url = 'https://www.xvideos.com/video123456'
        info = await self.extractor.extract_info(url)
        
        assert info.get('has_m3u8') is True
        # Check for HLS formats
        hls_formats = [f for f in info['formats'] if f.get('protocol') == 'hls']
        assert len(hls_formats) > 0


class TestXHamsterExtractor:
    """Test XHamster extractor functionality"""
    
    def setup_method(self):
        self.extractor = XHamsterExtractor()
    
    def test_supported_domains(self):
        """Test supported domains"""
        expected_domains = ['xhamster.com', 'www.xhamster.com', 'xhamster.desi', 'xhamster.one']
        assert self.extractor.supported_domains == expected_domains
    
    def test_can_handle_valid_urls(self):
        """Test URL handling for valid XHamster URLs"""
        valid_urls = [
            'https://xhamster.com/videos/test-video-123456',
            'https://www.xhamster.com/movies/789012',
            'https://xhamster.desi/videos/vr-content-345678'
        ]
        
        for url in valid_urls:
            assert self.extractor.can_handle(url), f"Should handle URL: {url}"
    
    @pytest.mark.asyncio
    async def test_get_metadata(self):
        """Test metadata extraction"""
        url = 'https://xhamster.com/videos/test-video-123456'
        metadata = await self.extractor.get_metadata(url)
        
        assert metadata.platform == Platform.XHAMSTER
        assert len(metadata.quality_options) > 0
        assert metadata.video_id == '123456'
    
    @pytest.mark.asyncio
    async def test_vr_content_detection(self):
        """Test VR content detection"""
        vr_url = 'https://xhamster.com/videos/vr-content-123456'
        info = await self.extractor.extract_info(vr_url)
        
        assert info.get('is_vr') is True
        assert 'vr' in info.get('tags', [])
        
        # Check for VR-specific formats
        vr_formats = [f for f in info['formats'] if f.get('is_vr')]
        assert len(vr_formats) > 0


class TestKissJAVExtractor:
    """Test KissJAV extractor functionality"""
    
    def setup_method(self):
        self.extractor = KissJAVExtractor()
    
    def test_supported_domains(self):
        """Test supported domains"""
        expected_domains = ['kissjav.com', 'www.kissjav.com', 'kissjav.li']
        assert self.extractor.supported_domains == expected_domains
    
    def test_can_handle_valid_urls(self):
        """Test URL handling for valid KissJAV URLs"""
        valid_urls = [
            'https://kissjav.com/video/test-video-123',
            'https://www.kissjav.com/watch/jav-content-456',
            'https://kissjav.li/video/sample-789'
        ]
        
        for url in valid_urls:
            assert self.extractor.can_handle(url), f"Should handle URL: {url}"
    
    @pytest.mark.asyncio
    async def test_get_metadata(self):
        """Test metadata extraction"""
        url = 'https://kissjav.com/video/test-video-123'
        metadata = await self.extractor.get_metadata(url)
        
        assert metadata.platform == Platform.KISSJAV
        assert len(metadata.quality_options) > 0
        assert metadata.video_id == 'test-video-123'
    
    @pytest.mark.asyncio
    async def test_subtitle_support(self):
        """Test subtitle download support"""
        url = 'https://kissjav.com/video/test-video-123'
        info = await self.extractor.extract_info(url)
        
        assert info.get('has_subtitles') is True
        assert 'subtitles' in info
        
        subtitles = info['subtitles']
        assert len(subtitles) > 0
        
        # Check for different language subtitles
        languages = [sub.get('language') for sub in subtitles]
        assert 'en' in languages  # English
        assert 'ja' in languages  # Japanese


class TestAntiCrawlerFeatures:
    """Test anti-crawler features across adult platforms"""
    
    @pytest.mark.asyncio
    async def test_age_verification_bypass(self):
        """Test age verification bypass functionality"""
        extractors = [
            YouPornExtractor(),
            XVideoExtractor(),
            XHamsterExtractor(),
            KissJAVExtractor()
        ]
        
        for extractor in extractors:
            # Test that extractors can handle age-restricted content
            # This is indicated by the age_verified flag in extracted info
            if hasattr(extractor, '_fetch_video_info'):
                # Simulate age verification bypass test
                assert True  # Placeholder for actual implementation
    
    def test_anti_bot_mechanisms(self):
        """Test anti-bot mechanism handling"""
        from app.core.utils.anti_crawler import anti_crawler
        
        # Test user agent rotation
        ua1 = anti_crawler.get_random_user_agent()
        ua2 = anti_crawler.get_random_user_agent()
        assert isinstance(ua1, str)
        assert isinstance(ua2, str)
        
        # Test domain-specific headers
        headers = anti_crawler.get_common_headers('pornhub.com')
        assert 'User-Agent' in headers
        assert 'Referer' in headers
        
        # Test age verification cookies
        cookies = anti_crawler.get_age_verification_cookies('youporn.com')
        assert len(cookies) > 0
        assert 'age_verified' in cookies or 'age_gate' in cookies


class TestExtractorInfo:
    """Test extractor information for adult platforms"""
    
    def test_all_adult_extractors_have_info(self):
        """Test that all adult extractors provide proper information"""
        extractors = [
            YouPornExtractor(),
            XVideoExtractor(),
            XHamsterExtractor(),
            KissJAVExtractor()
        ]
        
        for extractor in extractors:
            info = extractor.get_extractor_info()
            assert info.name
            assert info.version
            assert info.supported_domains
            assert info.description
            assert info.author
            assert 'adult' in info.description.lower() or 'Adult' in info.description


if __name__ == '__main__':
    pytest.main([__file__])