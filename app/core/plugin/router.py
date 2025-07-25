"""
URL router for intelligent routing of URLs to appropriate plugins.
"""
import logging
import re
from typing import Optional, List, Dict, Tuple, Pattern
from urllib.parse import urlparse, parse_qs
from dataclasses import dataclass
import threading
from enum import Enum

from app.core.plugin.registry import PluginRegistry, RegisteredPlugin


class URLType(Enum):
    """URL type enumeration"""
    VIDEO = "video"
    PLAYLIST = "playlist"
    CHANNEL = "channel"
    USER = "user"
    LIVE = "live"
    UNKNOWN = "unknown"


@dataclass
class URLInfo:
    """Information about a URL"""
    url: str
    domain: str
    url_type: URLType
    platform: str
    video_id: Optional[str] = None
    playlist_id: Optional[str] = None
    channel_id: Optional[str] = None
    user_id: Optional[str] = None
    parameters: Dict[str, str] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class RoutingResult:
    """Result of URL routing"""
    success: bool
    plugin: Optional[RegisteredPlugin] = None
    url_info: Optional[URLInfo] = None
    error_message: Optional[str] = None
    confidence: float = 0.0  # Confidence score (0.0 - 1.0)


class URLPattern:
    """URL pattern for matching and extracting information"""
    
    def __init__(self, pattern: str, url_type: URLType, platform: str,
                 video_id_group: Optional[str] = None,
                 playlist_id_group: Optional[str] = None,
                 channel_id_group: Optional[str] = None,
                 user_id_group: Optional[str] = None):
        self.pattern: Pattern = re.compile(pattern, re.IGNORECASE)
        self.url_type = url_type
        self.platform = platform
        self.video_id_group = video_id_group
        self.playlist_id_group = playlist_id_group
        self.channel_id_group = channel_id_group
        self.user_id_group = user_id_group
    
    def match(self, url: str) -> Optional[URLInfo]:
        """
        Match URL against this pattern.
        
        Args:
            url: URL to match
            
        Returns:
            URLInfo object if match successful, None otherwise
        """
        match = self.pattern.search(url)
        if not match:
            return None
        
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            # Extract IDs from regex groups
            video_id = None
            playlist_id = None
            channel_id = None
            user_id = None
            
            if self.video_id_group:
                video_id = match.group(self.video_id_group)
            
            if self.playlist_id_group:
                playlist_id = match.group(self.playlist_id_group)
            
            if self.channel_id_group:
                channel_id = match.group(self.channel_id_group)
            
            if self.user_id_group:
                user_id = match.group(self.user_id_group)
            
            # Also check query parameters for IDs
            if not video_id and 'v' in query_params:
                video_id = query_params['v'][0]
            
            if not playlist_id and 'list' in query_params:
                playlist_id = query_params['list'][0]
            
            return URLInfo(
                url=url,
                domain=parsed.netloc.lower(),
                url_type=self.url_type,
                platform=self.platform,
                video_id=video_id,
                playlist_id=playlist_id,
                channel_id=channel_id,
                user_id=user_id,
                parameters={k: v[0] if v else '' for k, v in query_params.items()}
            )
            
        except Exception:
            return None


class URLRouter:
    """
    Intelligent URL router that analyzes URLs and routes them to appropriate plugins.
    """
    
    def __init__(self, registry: PluginRegistry):
        self.logger = logging.getLogger(__name__)
        self.registry = registry
        
        # URL patterns for different platforms
        self.url_patterns: List[URLPattern] = []
        
        # Routing cache
        self._routing_cache: Dict[str, RoutingResult] = {}
        self._cache_size_limit = 1000
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize built-in URL patterns
        self._init_url_patterns()
    
    def _init_url_patterns(self):
        """Initialize built-in URL patterns for common platforms"""
        patterns = [
            # YouTube patterns
            URLPattern(
                r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)(?P<video_id>[a-zA-Z0-9_-]{11})',
                URLType.VIDEO, 'youtube', video_id_group='video_id'
            ),
            URLPattern(
                r'(?:https?://)?(?:www\.)?youtube\.com/playlist\?list=(?P<playlist_id>[a-zA-Z0-9_-]+)',
                URLType.PLAYLIST, 'youtube', playlist_id_group='playlist_id'
            ),
            URLPattern(
                r'(?:https?://)?(?:www\.)?youtube\.com/channel/(?P<channel_id>[a-zA-Z0-9_-]+)',
                URLType.CHANNEL, 'youtube', channel_id_group='channel_id'
            ),
            URLPattern(
                r'(?:https?://)?(?:www\.)?youtube\.com/user/(?P<user_id>[a-zA-Z0-9_-]+)',
                URLType.USER, 'youtube', user_id_group='user_id'
            ),
            URLPattern(
                r'(?:https?://)?(?:www\.)?youtube\.com/c/(?P<user_id>[a-zA-Z0-9_-]+)',
                URLType.CHANNEL, 'youtube', user_id_group='user_id'
            ),
            
            # Bilibili patterns
            URLPattern(
                r'(?:https?://)?(?:www\.)?bilibili\.com/video/(?P<video_id>[a-zA-Z0-9]+)',
                URLType.VIDEO, 'bilibili', video_id_group='video_id'
            ),
            URLPattern(
                r'(?:https?://)?(?:www\.)?space\.bilibili\.com/(?P<user_id>\d+)',
                URLType.USER, 'bilibili', user_id_group='user_id'
            ),
            
            # TikTok patterns
            URLPattern(
                r'(?:https?://)?(?:www\.)?tiktok\.com/@[^/]+/video/(?P<video_id>\d+)',
                URLType.VIDEO, 'tiktok', video_id_group='video_id'
            ),
            URLPattern(
                r'(?:https?://)?(?:www\.)?tiktok\.com/@(?P<user_id>[^/]+)',
                URLType.USER, 'tiktok', user_id_group='user_id'
            ),
            
            # Instagram patterns
            URLPattern(
                r'(?:https?://)?(?:www\.)?instagram\.com/p/(?P<video_id>[a-zA-Z0-9_-]+)',
                URLType.VIDEO, 'instagram', video_id_group='video_id'
            ),
            URLPattern(
                r'(?:https?://)?(?:www\.)?instagram\.com/(?P<user_id>[a-zA-Z0-9_.]+)/?$',
                URLType.USER, 'instagram', user_id_group='user_id'
            ),
            
            # Twitter patterns
            URLPattern(
                r'(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/[^/]+/status/(?P<video_id>\d+)',
                URLType.VIDEO, 'twitter', video_id_group='video_id'
            ),
            URLPattern(
                r'(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/(?P<user_id>[^/]+)/?$',
                URLType.USER, 'twitter', user_id_group='user_id'
            ),
            
            # Adult content platforms
            URLPattern(
                r'(?:https?://)?(?:www\.)?pornhub\.com/view_video\.php\?viewkey=(?P<video_id>[a-zA-Z0-9]+)',
                URLType.VIDEO, 'pornhub', video_id_group='video_id'
            ),
            URLPattern(
                r'(?:https?://)?(?:www\.)?youporn\.com/watch/(?P<video_id>\d+)',
                URLType.VIDEO, 'youporn', video_id_group='video_id'
            ),
            URLPattern(
                r'(?:https?://)?(?:www\.)?xvideos\.com/video(?P<video_id>\d+)',
                URLType.VIDEO, 'xvideos', video_id_group='video_id'
            ),
            URLPattern(
                r'(?:https?://)?(?:www\.)?xhamster\.com/videos/[^/]+-(?P<video_id>\d+)',
                URLType.VIDEO, 'xhamster', video_id_group='video_id'
            ),
            
            # Other platforms
            URLPattern(
                r'(?:https?://)?(?:www\.)?weibo\.com/tv/show/(?P<video_id>\d+:\d+)',
                URLType.VIDEO, 'weibo', video_id_group='video_id'
            ),
            URLPattern(
                r'(?:https?://)?(?:www\.)?pixiv\.net/(?:en/)?artworks/(?P<video_id>\d+)',
                URLType.VIDEO, 'pixiv', video_id_group='video_id'
            ),
            URLPattern(
                r'(?:https?://)?(?:www\.)?twitch\.tv/videos/(?P<video_id>\d+)',
                URLType.VIDEO, 'twitch', video_id_group='video_id'
            ),
        ]
        
        self.url_patterns.extend(patterns)
        self.logger.info(f"Initialized {len(patterns)} URL patterns")
    
    def add_url_pattern(self, pattern: URLPattern):
        """
        Add a custom URL pattern.
        
        Args:
            pattern: URLPattern object
        """
        with self._lock:
            self.url_patterns.append(pattern)
            # Clear cache as new pattern might affect routing
            self._routing_cache.clear()
    
    def route_url(self, url: str) -> RoutingResult:
        """
        Route a URL to the appropriate plugin.
        
        Args:
            url: URL to route
            
        Returns:
            RoutingResult object
        """
        with self._lock:
            # Check cache first
            if url in self._routing_cache:
                return self._routing_cache[url]
            
            try:
                # Analyze URL
                url_info = self._analyze_url(url)
                if not url_info:
                    result = RoutingResult(
                        success=False,
                        error_message="Failed to analyze URL"
                    )
                    self._cache_result(url, result)
                    return result
                
                # Find appropriate plugin
                plugin = self.registry.get_plugin_for_url(url)
                if not plugin:
                    result = RoutingResult(
                        success=False,
                        url_info=url_info,
                        error_message="No suitable plugin found"
                    )
                    self._cache_result(url, result)
                    return result
                
                # Calculate confidence score
                confidence = self._calculate_confidence(url_info, plugin)
                
                result = RoutingResult(
                    success=True,
                    plugin=plugin,
                    url_info=url_info,
                    confidence=confidence
                )
                
                self._cache_result(url, result)
                return result
                
            except Exception as e:
                self.logger.error(f"Error routing URL {url}: {e}")
                result = RoutingResult(
                    success=False,
                    error_message=str(e)
                )
                self._cache_result(url, result)
                return result
    
    def batch_route_urls(self, urls: List[str]) -> List[RoutingResult]:
        """
        Route multiple URLs.
        
        Args:
            urls: List of URLs to route
            
        Returns:
            List of RoutingResult objects
        """
        results = []
        for url in urls:
            result = self.route_url(url)
            results.append(result)
        
        return results
    
    def get_url_info(self, url: str) -> Optional[URLInfo]:
        """
        Get URL information without routing to plugin.
        
        Args:
            url: URL to analyze
            
        Returns:
            URLInfo object or None if analysis failed
        """
        return self._analyze_url(url)
    
    def is_supported_url(self, url: str) -> bool:
        """
        Check if URL is supported by any plugin.
        
        Args:
            url: URL to check
            
        Returns:
            True if supported, False otherwise
        """
        result = self.route_url(url)
        return result.success
    
    def get_supported_platforms(self) -> List[str]:
        """
        Get list of supported platforms.
        
        Returns:
            List of platform names
        """
        platforms = set()
        for pattern in self.url_patterns:
            platforms.add(pattern.platform)
        
        return sorted(list(platforms))
    
    def clear_cache(self):
        """Clear the routing cache"""
        with self._lock:
            self._routing_cache.clear()
            self.logger.info("URL routing cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        with self._lock:
            return {
                'cache_size': len(self._routing_cache),
                'cache_limit': self._cache_size_limit
            }
    
    def _analyze_url(self, url: str) -> Optional[URLInfo]:
        """Analyze URL and extract information"""
        try:
            # Normalize URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Try each pattern
            for pattern in self.url_patterns:
                url_info = pattern.match(url)
                if url_info:
                    return url_info
            
            # If no pattern matches, create basic URL info
            parsed = urlparse(url)
            return URLInfo(
                url=url,
                domain=parsed.netloc.lower(),
                url_type=URLType.UNKNOWN,
                platform='unknown',
                parameters=dict(parse_qs(parsed.query))
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing URL {url}: {e}")
            return None
    
    def _calculate_confidence(self, url_info: URLInfo, plugin: RegisteredPlugin) -> float:
        """Calculate confidence score for plugin selection"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence if platform matches
        if url_info.platform in plugin.name.lower():
            confidence += 0.3
        
        # Boost confidence if domain is directly supported
        if any(domain in url_info.domain for domain in plugin.supported_domains):
            confidence += 0.2
        
        # Boost confidence based on plugin usage
        if plugin.usage_count > 0:
            confidence += min(0.1, plugin.usage_count / 100)
        
        # Boost confidence based on plugin priority
        if plugin.priority > 0:
            confidence += min(0.1, plugin.priority / 10)
        
        return min(1.0, confidence)
    
    def _cache_result(self, url: str, result: RoutingResult):
        """Cache routing result"""
        if len(self._routing_cache) >= self._cache_size_limit:
            # Remove oldest entries (simple FIFO)
            oldest_keys = list(self._routing_cache.keys())[:100]
            for key in oldest_keys:
                del self._routing_cache[key]
        
        self._routing_cache[url] = result