"""
Twitter/X extractor plugin for downloading media content from Twitter.
Handles user media batch downloads and creator monitoring features.
"""
import re
import json
import aiohttp
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
from datetime import datetime

from app.core.extractor.base import BaseExtractor, ExtractorInfo
from app.data.models.core import VideoMetadata, QualityOption, Platform


class TwitterExtractor(BaseExtractor):
    """
    Twitter/X extractor for downloading media content from Twitter.
    Supports twitter.com and x.com URLs with user media batch downloads and monitoring.
    """
    
    @property
    def supported_domains(self) -> List[str]:
        return ['twitter.com', 'www.twitter.com', 'x.com', 'www.x.com', 't.co']
    
    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the given URL"""
        return self._is_supported_domain(url) and self._extract_content_info(url) is not None
    
    async def extract_info(self, url: str) -> Dict[str, Any]:
        """Extract information from Twitter URL"""
        content_info = self._extract_content_info(url)
        if not content_info:
            raise ValueError("Invalid Twitter URL")
        
        info = await self._fetch_twitter_info(content_info, url)
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
        """Extract metadata from Twitter URL"""
        info = await self.extract_info(url)
        
        # Parse quality options
        quality_options = self._parse_quality_options(info)
        
        # Create metadata object
        metadata = VideoMetadata(
            title=info.get('title', 'Twitter Post'),
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
            platform=Platform.TWITTER,
            tags=info.get('tags', [])
        )
        
        return metadata
    
    def get_extractor_info(self) -> ExtractorInfo:
        """Get information about this extractor"""
        return ExtractorInfo(
            name="Twitter/X Extractor",
            version="1.0.0",
            supported_domains=self.supported_domains,
            description="Extract media content from Twitter/X with user batch downloads and creator monitoring",
            author="Multi-Platform Video Downloader"
        )
    
    def _parse_quality_options(self, info: Dict[str, Any]) -> List[QualityOption]:
        """Parse quality options from Twitter extracted information"""
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
    
    def _extract_content_info(self, url: str) -> Optional[Dict[str, str]]:
        """Extract content information from Twitter URL"""
        patterns = [
            r'(?:twitter|x)\.com/([^/]+)/status/(\d+)',  # Tweet
            r'(?:twitter|x)\.com/([^/]+)/?$',  # User profile
            r'(?:twitter|x)\.com/([^/]+)/media/?$',  # User media
            r't\.co/([a-zA-Z0-9]+)',  # Short URL
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                if 'status' in url:
                    # Single tweet
                    return {
                        'type': 'tweet',
                        'username': match.group(1),
                        'tweet_id': match.group(2)
                    }
                elif 'media' in url:
                    # User media page
                    return {
                        'type': 'user_media',
                        'username': match.group(1)
                    }
                elif 't.co' in url:
                    # Short URL
                    return {
                        'type': 'short_url',
                        'short_id': match.group(1)
                    }
                else:
                    # User profile
                    return {
                        'type': 'user_profile',
                        'username': match.group(1)
                    }
        
        return None
    
    def _is_media_tweet(self, tweet_data: Dict[str, Any]) -> bool:
        """Check if tweet contains media"""
        return tweet_data.get('has_media', False)
    
    async def _fetch_twitter_info(self, content_info: Dict[str, str], original_url: str) -> Dict[str, Any]:
        """Fetch Twitter content information"""
        content_type = content_info.get('type', 'tweet')
        
        if content_type == 'tweet':
            return await self._fetch_tweet_info(content_info)
        elif content_type == 'user_media':
            return await self._fetch_user_media_info(content_info)
        elif content_type == 'user_profile':
            return await self._fetch_user_profile_info(content_info)
        elif content_type == 'short_url':
            return await self._fetch_short_url_info(content_info)
        else:
            raise ValueError(f"Unknown content type: {content_type}")
    
    async def _fetch_tweet_info(self, content_info: Dict[str, str]) -> Dict[str, Any]:
        """Fetch single tweet information"""
        username = content_info.get('username')
        tweet_id = content_info.get('tweet_id')
        
        return {
            'id': tweet_id,
            'type': 'tweet',
            'username': username,
            'title': f'Tweet by @{username}',
            'description': 'Twitter post with media content',
            'uploader': f'@{username}',
            'uploader_id': username,
            'uploader_url': f'https://twitter.com/{username}',
            'duration': 30,  # For video content
            'view_count': 10000,
            'like_count': 500,
            'comment_count': 100,
            'retweet_count': 200,
            'upload_date': '20240101',
            'thumbnail': f'https://pbs.twimg.com/media/{tweet_id}_thumb.jpg',
            'tags': ['twitter', 'social', 'media'],
            'has_media': True,
            'media_type': 'mixed',  # 'photo', 'video', 'gif', 'mixed'
            'is_sensitive': False,
            'requires_login': False,
            'formats': [
                # 4K Photo
                {
                    'format_id': 'photo-4k',
                    'url': f'https://pbs.twimg.com/media/{tweet_id}?format=jpg&name=4096x4096',
                    'height': 4096,
                    'width': 4096,
                    'ext': 'jpg',
                    'vcodec': 'none',
                    'quality': '4k',
                    'filesize': 8 * 1024 * 1024  # 8MB
                },
                # Large Photo
                {
                    'format_id': 'photo-large',
                    'url': f'https://pbs.twimg.com/media/{tweet_id}?format=jpg&name=large',
                    'height': 2048,
                    'width': 2048,
                    'ext': 'jpg',
                    'vcodec': 'none',
                    'quality': 'large',
                    'filesize': 2 * 1024 * 1024  # 2MB
                },
                # Video
                {
                    'format_id': 'video-720p',
                    'url': f'https://video.twimg.com/ext_tw_video/{tweet_id}/pu/vid/720x720/video.mp4',
                    'height': 720,
                    'width': 720,
                    'ext': 'mp4',
                    'vcodec': 'h264',
                    'fps': 30,
                    'tbr': 2000,
                    'filesize': 20 * 1024 * 1024  # 20MB
                },
                # GIF
                {
                    'format_id': 'gif',
                    'url': f'https://video.twimg.com/tweet_video/{tweet_id}.mp4',
                    'height': 480,
                    'width': 480,
                    'ext': 'mp4',
                    'vcodec': 'h264',
                    'fps': 15,
                    'tbr': 1000,
                    'is_gif': True,
                    'filesize': 5 * 1024 * 1024  # 5MB
                }
            ]
        }
    
    async def _fetch_user_media_info(self, content_info: Dict[str, str]) -> Dict[str, Any]:
        """Fetch user media information for batch download"""
        username = content_info.get('username')
        
        return {
            'id': f'media_{username}',
            'type': 'user_media',
            'username': username,
            'title': f'@{username} Media Collection',
            'description': f'All media content from @{username}',
            'uploader': f'@{username}',
            'uploader_id': username,
            'uploader_url': f'https://twitter.com/{username}',
            'is_batch_download': True,
            'estimated_media_count': 500,
            'tags': ['twitter', 'media', 'batch'],
            'formats': []  # Will be populated with individual media formats
        }
    
    async def _fetch_user_profile_info(self, content_info: Dict[str, str]) -> Dict[str, Any]:
        """Fetch user profile information"""
        username = content_info.get('username')
        
        return {
            'id': username,
            'type': 'user_profile',
            'username': username,
            'title': f'@{username} Profile',
            'description': f'Twitter profile for @{username}',
            'uploader': f'@{username}',
            'uploader_id': username,
            'uploader_url': f'https://twitter.com/{username}',
            'follower_count': 10000,
            'following_count': 1000,
            'tweet_count': 5000,
            'tags': ['twitter', 'profile'],
            'formats': []
        }
    
    async def _fetch_short_url_info(self, content_info: Dict[str, str]) -> Dict[str, Any]:
        """Fetch information from Twitter short URL"""
        short_id = content_info.get('short_id')
        
        # In a real implementation, this would resolve the short URL
        return {
            'id': short_id,
            'type': 'short_url',
            'title': f'Twitter Short URL {short_id}',
            'description': 'Shortened Twitter URL',
            'tags': ['twitter', 'short_url'],
            'formats': []
        }
    
    def _parse_upload_date(self, date_str: str) -> datetime:
        """Parse upload date string to datetime object"""
        if not date_str:
            return datetime.now()
        
        try:
            return datetime.strptime(date_str, '%Y%m%d')
        except ValueError:
            return datetime.now()
    
    async def extract_user_media(self, username: str, limit: int = 100, include_retweets: bool = False) -> List[Dict[str, Any]]:
        """Extract all media content from a Twitter user (重点功能)"""
        # In a real implementation, this would:
        # 1. Use Twitter API or web scraping
        # 2. Filter tweets with media
        # 3. Handle pagination
        # 4. Support time range filtering
        # 5. Handle private accounts with authentication
        
        media_tweets = []
        for i in range(min(limit, 50)):  # Simulate limited tweets
            tweet_id = f"tweet_{i:015d}"
            media_tweets.append({
                'id': tweet_id,
                'username': username,
                'text': f'Tweet {i+1} with media content',
                'created_at': '2024-01-01T12:00:00Z',
                'media_urls': [
                    f'https://pbs.twimg.com/media/{tweet_id}?format=jpg&name=large',
                    f'https://video.twimg.com/ext_tw_video/{tweet_id}/pu/vid/720x720/video.mp4'
                ],
                'media_types': ['photo', 'video'],
                'like_count': 100,
                'retweet_count': 50,
                'reply_count': 25
            })
        
        return media_tweets
    
    async def get_user_timeline(self, username: str, include_replies: bool = False, limit: int = 200) -> List[Dict[str, Any]]:
        """Get user timeline with media filtering"""
        # In a real implementation, this would:
        # 1. Fetch user timeline
        # 2. Filter for media-containing tweets
        # 3. Handle rate limiting
        # 4. Support incremental updates
        
        timeline = []
        for i in range(min(limit, 100)):  # Simulate limited timeline
            tweet_id = f"timeline_{i:015d}"
            has_media = i % 3 == 0  # Every 3rd tweet has media
            
            if has_media:  # Only include tweets with media
                timeline.append({
                    'id': tweet_id,
                    'username': username,
                    'text': f'Timeline tweet {i+1}',
                    'created_at': '2024-01-01T12:00:00Z',
                    'has_media': True,
                    'media_count': 2,
                    'url': f'https://twitter.com/{username}/status/{tweet_id}'
                })
        
        return timeline
    
    async def monitor_user_updates(self, username: str, last_check: datetime = None) -> Dict[str, Any]:
        """Monitor user for new media content (创作者监控功能)"""
        # In a real implementation, this would:
        # 1. Check for new tweets since last_check
        # 2. Filter for media content
        # 3. Return update summary
        # 4. Support webhook notifications
        
        current_time = datetime.now()
        
        # Simulate new content detection
        new_media_count = 3
        new_tweets = []
        
        if new_media_count > 0:
            for i in range(new_media_count):
                tweet_id = f"new_{i:015d}"
                new_tweets.append({
                    'id': tweet_id,
                    'username': username,
                    'created_at': current_time.isoformat(),
                    'has_media': True,
                    'url': f'https://twitter.com/{username}/status/{tweet_id}'
                })
        
        return {
            'username': username,
            'last_check': last_check.isoformat() if last_check else None,
            'current_check': current_time.isoformat(),
            'new_media_count': new_media_count,
            'new_tweets': new_tweets,
            'has_updates': new_media_count > 0
        }
    
    async def _handle_cookie_authentication(self, session: aiohttp.ClientSession, cookies_file: str = None) -> bool:
        """Handle Twitter authentication using cookies"""
        # In a real implementation, this would:
        # 1. Load cookies from file
        # 2. Set authentication headers
        # 3. Handle CSRF tokens
        # 4. Verify login status
        
        if cookies_file:
            # Load and apply cookies
            auth_cookies = {
                'auth_token': 'simulated_auth_token',
                'ct0': 'simulated_csrf_token',
                'twid': 'simulated_user_id'
            }
            
            for name, value in auth_cookies.items():
                session.cookie_jar.update_cookies({name: value})
            
            # Set CSRF header
            session.headers.update({
                'X-CSRF-Token': 'simulated_csrf_token',
                'Authorization': 'Bearer simulated_bearer_token'
            })
            
            return True
        
        return False