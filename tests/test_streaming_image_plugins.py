"""
Test cases for streaming and image platform plugins.
"""
import pytest
import asyncio
from datetime import datetime

from app.plugins.fc2 import FC2Extractor
from app.plugins.flickr import FlickrExtractor
from app.plugins.twitch import TwitchExtractor
from app.plugins.twitter import TwitterExtractor
from app.data.models.core import Platform


class TestFC2Extractor:
    """Test FC2 extractor functionality"""
    
    def setup_method(self):
        self.extractor = FC2Extractor()
    
    def test_supported_domains(self):
        """Test supported domains"""
        expected_domains = ['video.fc2.com', 'fc2.com']
        assert self.extractor.supported_domains == expected_domains
    
    def test_can_handle_valid_urls(self):
        """Test URL handling for valid FC2 URLs"""
        valid_urls = [
            'https://video.fc2.com/content/123456789',
            'https://video.fc2.com/a/content/987654321',
            'https://fc2.com/video/555666777'
        ]
        
        for url in valid_urls:
            assert self.extractor.can_handle(url), f"Should handle URL: {url}"
    
    @pytest.mark.asyncio
    async def test_get_metadata(self):
        """Test metadata extraction"""
        url = 'https://video.fc2.com/content/123456789'
        metadata = await self.extractor.get_metadata(url)
        
        assert metadata.platform == Platform.FC2
        assert len(metadata.quality_options) > 0
        assert metadata.video_id == '123456789'
    
    @pytest.mark.asyncio
    async def test_hd_quality_support(self):
        """Test HD quality support"""
        url = 'https://video.fc2.com/content/123456789'
        info = await self.extractor.extract_info(url)
        
        assert info.get('has_hd') is True
        
        # Check for HD formats
        hd_formats = [f for f in info['formats'] if f.get('quality') == 'hd']
        assert len(hd_formats) > 0
    
    @pytest.mark.asyncio
    async def test_member_authentication_detection(self):
        """Test member authentication detection"""
        url = 'https://video.fc2.com/content/123456789'
        info = await self.extractor.extract_info(url)
        
        assert 'member_only' in info
        assert 'geo_restricted' in info


class TestFlickrExtractor:
    """Test Flickr extractor functionality"""
    
    def setup_method(self):
        self.extractor = FlickrExtractor()
    
    def test_supported_domains(self):
        """Test supported domains"""
        expected_domains = ['flickr.com', 'www.flickr.com', 'flic.kr']
        assert self.extractor.supported_domains == expected_domains
    
    def test_can_handle_valid_urls(self):
        """Test URL handling for valid Flickr URLs"""
        valid_urls = [
            'https://www.flickr.com/photos/user123/123456789',
            'https://flic.kr/p/abc123',
            'https://flickr.com/photos/user123/sets/987654321',
            'https://flickr.com/photos/user123/'
        ]
        
        for url in valid_urls:
            assert self.extractor.can_handle(url), f"Should handle URL: {url}"
    
    @pytest.mark.asyncio
    async def test_get_metadata(self):
        """Test metadata extraction"""
        url = 'https://www.flickr.com/photos/user123/123456789'
        metadata = await self.extractor.get_metadata(url)
        
        assert metadata.platform == Platform.FLICKR
        assert len(metadata.quality_options) > 0
        assert metadata.video_id == '123456789'
        assert metadata.duration == 0  # Photos don't have duration
    
    @pytest.mark.asyncio
    async def test_high_resolution_support(self):
        """Test high-resolution photo support"""
        url = 'https://www.flickr.com/photos/user123/123456789'
        info = await self.extractor.extract_info(url)
        
        formats = info.get('formats', [])
        
        # Check for original quality format
        original_formats = [f for f in formats if f.get('format_id') == 'original']
        assert len(original_formats) > 0
        
        # Check high resolution
        for fmt in original_formats:
            assert fmt.get('height', 0) >= 4000
            assert fmt.get('width', 0) >= 6000
    
    @pytest.mark.asyncio
    async def test_exif_data_support(self):
        """Test EXIF data extraction support"""
        url = 'https://www.flickr.com/photos/user123/123456789'
        info = await self.extractor.extract_info(url)
        
        assert info.get('has_exif') is True
        assert 'exif_data' in info
        
        exif_data = info['exif_data']
        assert 'camera' in exif_data
        assert 'lens' in exif_data
        assert 'focal_length' in exif_data
    
    @pytest.mark.asyncio
    async def test_album_batch_download(self):
        """Test album batch download functionality"""
        album_url = 'https://flickr.com/photos/user123/sets/987654321'
        info = await self.extractor.extract_info(album_url)
        
        assert info.get('is_album') is True
        assert 'photo_count' in info
        
        # Test album photos extraction
        photos = await self.extractor.get_album_photos('987654321', 'user123', limit=10)
        assert len(photos) > 0
        
        for photo in photos:
            assert 'id' in photo
            assert 'url' in photo
            assert 'original_url' in photo


class TestTwitchExtractor:
    """Test Twitch extractor functionality"""
    
    def setup_method(self):
        self.extractor = TwitchExtractor()
    
    def test_supported_domains(self):
        """Test supported domains"""
        expected_domains = ['twitch.tv', 'www.twitch.tv', 'clips.twitch.tv', 'm.twitch.tv']
        assert self.extractor.supported_domains == expected_domains
    
    def test_can_handle_valid_urls(self):
        """Test URL handling for valid Twitch URLs"""
        valid_urls = [
            'https://www.twitch.tv/videos/123456789',
            'https://twitch.tv/streamer/clip/ABC123DEF456',
            'https://clips.twitch.tv/XYZ789GHI012',
            'https://www.twitch.tv/streamer'
        ]
        
        for url in valid_urls:
            assert self.extractor.can_handle(url), f"Should handle URL: {url}"
    
    @pytest.mark.asyncio
    async def test_vod_extraction(self):
        """Test VOD extraction"""
        url = 'https://www.twitch.tv/videos/123456789'
        metadata = await self.extractor.get_metadata(url)
        
        assert metadata.platform == Platform.TWITCH
        assert len(metadata.quality_options) > 0
        assert metadata.video_id == '123456789'
    
    @pytest.mark.asyncio
    async def test_clip_extraction(self):
        """Test clip extraction"""
        url = 'https://clips.twitch.tv/ABC123DEF456'
        info = await self.extractor.extract_info(url)
        
        assert info.get('type') == 'clip'
        assert info.get('id') == 'ABC123DEF456'
        assert info.get('duration') <= 60  # Clips are typically short
    
    @pytest.mark.asyncio
    async def test_live_stream_detection(self):
        """Test live stream detection"""
        url = 'https://www.twitch.tv/streamer'
        info = await self.extractor.extract_info(url)
        
        assert info.get('type') == 'live'
        assert info.get('is_live') is True
        
        # Check for live stream formats
        live_formats = [f for f in info['formats'] if f.get('is_live')]
        assert len(live_formats) > 0
    
    @pytest.mark.asyncio
    async def test_chat_replay_support(self):
        """Test chat replay support for VODs"""
        url = 'https://www.twitch.tv/videos/123456789'
        info = await self.extractor.extract_info(url)
        
        if info.get('type') == 'vod':
            assert info.get('has_chat_replay') is True
            assert 'chat_replay' in info
            assert info['chat_replay']['available'] is True
    
    @pytest.mark.asyncio
    async def test_channel_vods_batch(self):
        """Test channel VODs batch extraction"""
        vods = await self.extractor.get_channel_vods('streamer', limit=10)
        
        assert len(vods) > 0
        for vod in vods:
            assert 'id' in vod
            assert 'channel' in vod
            assert 'url' in vod


class TestTwitterExtractor:
    """Test Twitter extractor functionality"""
    
    def setup_method(self):
        self.extractor = TwitterExtractor()
    
    def test_supported_domains(self):
        """Test supported domains"""
        expected_domains = ['twitter.com', 'www.twitter.com', 'x.com', 'www.x.com', 't.co']
        assert self.extractor.supported_domains == expected_domains
    
    def test_can_handle_valid_urls(self):
        """Test URL handling for valid Twitter URLs"""
        valid_urls = [
            'https://twitter.com/user/status/123456789',
            'https://x.com/user/status/987654321',
            'https://twitter.com/user/media',
            'https://twitter.com/user',
            'https://t.co/abc123'
        ]
        
        for url in valid_urls:
            assert self.extractor.can_handle(url), f"Should handle URL: {url}"
    
    @pytest.mark.asyncio
    async def test_tweet_extraction(self):
        """Test single tweet extraction"""
        url = 'https://twitter.com/user/status/123456789'
        metadata = await self.extractor.get_metadata(url)
        
        assert metadata.platform == Platform.TWITTER
        assert len(metadata.quality_options) > 0
        assert metadata.video_id == '123456789'
    
    @pytest.mark.asyncio
    async def test_4k_image_support(self):
        """Test 4K image download support"""
        url = 'https://twitter.com/user/status/123456789'
        info = await self.extractor.extract_info(url)
        
        formats = info.get('formats', [])
        
        # Check for 4K photo format
        photo_4k_formats = [f for f in formats if f.get('format_id') == 'photo-4k']
        assert len(photo_4k_formats) > 0
        
        for fmt in photo_4k_formats:
            assert fmt.get('height') == 4096
            assert fmt.get('width') == 4096
    
    @pytest.mark.asyncio
    async def test_user_media_batch_download(self):
        """Test user media batch download (重点功能)"""
        url = 'https://twitter.com/user/media'
        info = await self.extractor.extract_info(url)
        
        assert info.get('type') == 'user_media'
        assert info.get('is_batch_download') is True
        assert 'estimated_media_count' in info
        
        # Test user media extraction
        media_tweets = await self.extractor.extract_user_media('user', limit=10)
        assert len(media_tweets) > 0
        
        for tweet in media_tweets:
            assert 'id' in tweet
            assert 'media_urls' in tweet
            assert 'media_types' in tweet
    
    @pytest.mark.asyncio
    async def test_creator_monitoring(self):
        """Test creator monitoring functionality (创作者监控功能)"""
        last_check = datetime(2024, 1, 1)
        updates = await self.extractor.monitor_user_updates('user', last_check)
        
        assert 'username' in updates
        assert 'new_media_count' in updates
        assert 'has_updates' in updates
        assert 'new_tweets' in updates
        
        if updates['has_updates']:
            assert len(updates['new_tweets']) > 0
    
    @pytest.mark.asyncio
    async def test_timeline_media_filtering(self):
        """Test timeline with media filtering"""
        timeline = await self.extractor.get_user_timeline('user', limit=20)
        
        # All returned tweets should have media
        for tweet in timeline:
            assert tweet.get('has_media') is True
    
    @pytest.mark.asyncio
    async def test_mixed_media_support(self):
        """Test mixed media support (photo, video, gif)"""
        url = 'https://twitter.com/user/status/123456789'
        info = await self.extractor.extract_info(url)
        
        formats = info.get('formats', [])
        
        # Check for different media types
        photo_formats = [f for f in formats if f.get('vcodec') == 'none']
        video_formats = [f for f in formats if f.get('vcodec') != 'none' and not f.get('is_gif')]
        gif_formats = [f for f in formats if f.get('is_gif')]
        
        assert len(photo_formats) > 0
        assert len(video_formats) > 0
        assert len(gif_formats) > 0


class TestCookieAuthFeatures:
    """Test cookie authentication features"""
    
    def test_cookie_auth_manager(self):
        """Test cookie authentication manager"""
        from app.core.utils.cookie_auth import cookie_auth
        
        # Test authentication status
        status = cookie_auth.get_authentication_status('twitter')
        assert 'platform' in status
        assert 'authenticated' in status
        assert 'cookie_count' in status
        
        # Test cookie import simulation
        success = cookie_auth.import_cookies_from_browser('twitter', 'chrome')
        assert success is True
        
        # Test authentication check
        is_auth = cookie_auth.is_authenticated('twitter')
        assert isinstance(is_auth, bool)
    
    @pytest.mark.asyncio
    async def test_session_cookie_application(self):
        """Test applying cookies to session"""
        from app.core.utils.cookie_auth import cookie_auth
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            # Test cookie application
            result = await cookie_auth.apply_cookies_to_session(session, 'twitter')
            assert isinstance(result, bool)
    
    def test_cookie_instructions(self):
        """Test cookie instruction generation"""
        from app.core.utils.cookie_auth import cookie_auth
        
        instructions = cookie_auth.get_cookie_instructions('twitter')
        assert 'steps' in instructions
        assert 'required_cookies' in instructions
        assert len(instructions['steps']) > 0
        assert len(instructions['required_cookies']) > 0


class TestExtractorInfo:
    """Test extractor information for streaming and image platforms"""
    
    def test_all_streaming_image_extractors_have_info(self):
        """Test that all streaming/image extractors provide proper information"""
        extractors = [
            FC2Extractor(),
            FlickrExtractor(),
            TwitchExtractor(),
            TwitterExtractor()
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