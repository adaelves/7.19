"""
Test cases for social media platform plugins.
"""
import pytest
import asyncio
from datetime import datetime

from app.plugins.weibo import WeiboExtractor
from app.plugins.tumblr import TumblrExtractor
from app.plugins.pixiv import PixivExtractor
from app.data.models.core import Platform


class TestWeiboExtractor:
    """Test Weibo extractor functionality"""
    
    def setup_method(self):
        self.extractor = WeiboExtractor()
    
    def test_supported_domains(self):
        """Test supported domains"""
        expected_domains = ['weibo.com', 'www.weibo.com', 'weibo.cn', 'm.weibo.cn', 't.cn']
        assert self.extractor.supported_domains == expected_domains
    
    def test_can_handle_valid_urls(self):
        """Test URL handling for valid Weibo URLs"""
        valid_urls = [
            'https://weibo.com/1234567890/ABC123DEF456',
            'https://www.weibo.com/detail/GHI789JKL012',
            'https://weibo.cn/detail/MNO345PQR678',
            'https://t.cn/shorturl123'
        ]
        
        for url in valid_urls:
            assert self.extractor.can_handle(url), f"Should handle URL: {url}"
    
    @pytest.mark.asyncio
    async def test_get_metadata(self):
        """Test metadata extraction"""
        url = 'https://weibo.com/1234567890/ABC123DEF456'
        metadata = await self.extractor.get_metadata(url)
        
        assert metadata.platform == Platform.WEIBO
        assert len(metadata.quality_options) > 0
        assert metadata.video_id == 'ABC123DEF456'
    
    @pytest.mark.asyncio
    async def test_long_weibo_detection(self):
        """Test long Weibo content detection"""
        url = 'https://weibo.com/1234567890/ABC123DEF456'
        info = await self.extractor.extract_info(url)
        
        # Check for long Weibo indicators
        assert 'is_long_weibo' in info
        assert 'content_type' in info
    
    @pytest.mark.asyncio
    async def test_mixed_content_support(self):
        """Test mixed content (video + image) support"""
        url = 'https://weibo.com/1234567890/ABC123DEF456'
        info = await self.extractor.extract_info(url)
        
        formats = info.get('formats', [])
        
        # Check for both video and image formats
        video_formats = [f for f in formats if f.get('vcodec') != 'none']
        image_formats = [f for f in formats if f.get('vcodec') == 'none']
        
        assert len(video_formats) > 0
        assert len(image_formats) > 0


class TestTumblrExtractor:
    """Test Tumblr extractor functionality"""
    
    def setup_method(self):
        self.extractor = TumblrExtractor()
    
    def test_supported_domains(self):
        """Test supported domains"""
        expected_domains = ['tumblr.com', 'www.tumblr.com']
        assert self.extractor.supported_domains == expected_domains
    
    def test_can_handle_valid_urls(self):
        """Test URL handling for valid Tumblr URLs"""
        valid_urls = [
            'https://example.tumblr.com/post/123456789',
            'https://www.tumblr.com/example/123456789',
            'https://example.tumblr.com/image/987654321',
            'https://example.tumblr.com/'  # Blog URL for batch download
        ]
        
        for url in valid_urls:
            assert self.extractor.can_handle(url), f"Should handle URL: {url}"
    
    @pytest.mark.asyncio
    async def test_get_metadata(self):
        """Test metadata extraction"""
        url = 'https://example.tumblr.com/post/123456789'
        metadata = await self.extractor.get_metadata(url)
        
        assert metadata.platform == Platform.TUMBLR
        assert len(metadata.quality_options) > 0
        assert metadata.video_id == '123456789'
    
    @pytest.mark.asyncio
    async def test_nsfw_content_handling(self):
        """Test NSFW content handling"""
        url = 'https://example.tumblr.com/post/123456789'
        info = await self.extractor.extract_info(url)
        
        assert 'is_nsfw' in info
        assert 'post_type' in info
    
    @pytest.mark.asyncio
    async def test_blog_batch_download(self):
        """Test blog batch download functionality"""
        blog_url = 'https://example.tumblr.com/'
        info = await self.extractor.extract_info(blog_url)
        
        assert info.get('is_blog_batch') is True
        assert 'post_count' in info
        assert info.get('blog_name') == 'example'
    
    @pytest.mark.asyncio
    async def test_multiple_media_formats(self):
        """Test support for multiple media formats (photo, video, gif)"""
        url = 'https://example.tumblr.com/post/123456789'
        info = await self.extractor.extract_info(url)
        
        formats = info.get('formats', [])
        
        # Check for different format types
        format_types = [f.get('ext') for f in formats]
        assert 'jpg' in format_types  # Photo
        assert 'mp4' in format_types  # Video
        assert 'gif' in format_types  # GIF


class TestPixivExtractor:
    """Test Pixiv extractor functionality"""
    
    def setup_method(self):
        self.extractor = PixivExtractor()
    
    def test_supported_domains(self):
        """Test supported domains"""
        expected_domains = ['pixiv.net', 'www.pixiv.net', 'i.pximg.net']
        assert self.extractor.supported_domains == expected_domains
    
    def test_can_handle_valid_urls(self):
        """Test URL handling for valid Pixiv URLs"""
        valid_urls = [
            'https://www.pixiv.net/artworks/123456789',
            'https://pixiv.net/member_illust.php?illust_id=987654321',
            'https://i.pximg.net/img-original/img/123456789_p0.jpg'
        ]
        
        for url in valid_urls:
            assert self.extractor.can_handle(url), f"Should handle URL: {url}"
    
    @pytest.mark.asyncio
    async def test_get_metadata(self):
        """Test metadata extraction"""
        url = 'https://www.pixiv.net/artworks/123456789'
        metadata = await self.extractor.get_metadata(url)
        
        assert metadata.platform == Platform.PIXIV
        assert len(metadata.quality_options) > 0
        assert metadata.video_id == '123456789'
    
    @pytest.mark.asyncio
    async def test_artwork_type_detection(self):
        """Test artwork type detection"""
        url = 'https://www.pixiv.net/artworks/123456789'
        info = await self.extractor.extract_info(url)
        
        assert 'artwork_type' in info
        assert 'is_ugoira' in info
        assert 'is_multi_page' in info
        assert 'requires_login' in info
    
    @pytest.mark.asyncio
    async def test_high_resolution_support(self):
        """Test high-resolution image support"""
        url = 'https://www.pixiv.net/artworks/123456789'
        info = await self.extractor.extract_info(url)
        
        formats = info.get('formats', [])
        
        # Check for original quality format
        original_formats = [f for f in formats if f.get('format_id') == 'original']
        assert len(original_formats) > 0
        
        # Check high resolution
        for fmt in original_formats:
            assert fmt.get('height', 0) >= 1200
            assert fmt.get('width', 0) >= 960
    
    @pytest.mark.asyncio
    async def test_ugoira_support(self):
        """Test ugoira (animated illustration) support"""
        # This would be tested with an actual ugoira URL in real implementation
        # For now, test the detection logic
        assert self.extractor._is_ugoira('ugoira') is True
        assert self.extractor._is_ugoira('illustration') is False
    
    @pytest.mark.asyncio
    async def test_multi_page_artwork(self):
        """Test multi-page artwork handling"""
        # Test the detection logic
        assert self.extractor._is_multi_page(5) is True
        assert self.extractor._is_multi_page(1) is False


class TestSocialAuthFeatures:
    """Test social media authentication features"""
    
    def test_social_auth_manager(self):
        """Test social authentication manager"""
        from app.core.utils.social_auth import social_auth
        
        # Test platform status
        status = social_auth.get_platform_status('weibo')
        assert 'logged_in' in status
        assert 'valid' in status
        
        # Test session management
        social_auth.set_session_data('test_platform', {
            'username': 'test_user',
            'logged_in': True
        })
        
        session_data = social_auth.get_session_data('test_platform')
        assert session_data is not None
        assert session_data['username'] == 'test_user'
        
        # Cleanup
        social_auth.logout_platform('test_platform')
    
    @pytest.mark.asyncio
    async def test_platform_session_setup(self):
        """Test platform session setup"""
        from app.core.utils.social_auth import social_auth
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            # Test Weibo session setup
            result = await social_auth.setup_weibo_session(session)
            assert result is True
            
            # Test Tumblr session setup
            result = await social_auth.setup_tumblr_session(session)
            assert result is True
            
            # Test Pixiv session setup (without credentials)
            result = await social_auth.setup_pixiv_session(session)
            # Should return False for anonymous access (limited)
            assert result is False


class TestBatchDownloadFeatures:
    """Test batch download features for social media platforms"""
    
    @pytest.mark.asyncio
    async def test_tumblr_blog_posts(self):
        """Test Tumblr blog posts extraction"""
        extractor = TumblrExtractor()
        posts = await extractor.get_blog_posts('example', limit=10)
        
        assert len(posts) > 0
        for post in posts:
            assert 'id' in post
            assert 'blog_name' in post
            assert 'url' in post
    
    @pytest.mark.asyncio
    async def test_pixiv_artist_works(self):
        """Test Pixiv artist works extraction"""
        extractor = PixivExtractor()
        works = await extractor.get_artist_works('artist123', limit=10)
        
        assert len(works) > 0
        for work in works:
            assert 'id' in work
            assert 'artist_id' in work
            assert 'url' in work


class TestExtractorInfo:
    """Test extractor information for social media platforms"""
    
    def test_all_social_extractors_have_info(self):
        """Test that all social media extractors provide proper information"""
        extractors = [
            WeiboExtractor(),
            TumblrExtractor(),
            PixivExtractor()
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