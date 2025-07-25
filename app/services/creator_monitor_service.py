"""
Creator monitoring service for tracking and auto-downloading new content.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.data.models.core import (
    CreatorProfile, Platform, DownloadOptions, VideoMetadata
)
from app.data.database.service import DatabaseService
from app.core.plugin.manager import PluginManager
from app.services.download_service import DownloadService
from app.core.config import config_manager

logger = logging.getLogger(__name__)


@dataclass
class CreatorUpdateResult:
    """Result of creator update check"""
    creator_id: str
    success: bool
    new_videos_count: int = 0
    new_videos: List[VideoMetadata] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.new_videos is None:
            self.new_videos = []


@dataclass
class MonitoringStats:
    """Creator monitoring statistics"""
    total_creators: int = 0
    active_creators: int = 0
    auto_download_enabled: int = 0
    last_check_time: Optional[datetime] = None
    total_checks: int = 0
    successful_checks: int = 0
    failed_checks: int = 0
    new_videos_found: int = 0
    auto_downloads_triggered: int = 0


class CreatorMonitorService:
    """
    Service for monitoring creators and automatically downloading new content.
    Implements periodic checking, new video detection, and auto-download functionality.
    """
    
    def __init__(self, 
                 db_service: Optional[DatabaseService] = None,
                 download_service: Optional[DownloadService] = None,
                 plugin_manager: Optional[PluginManager] = None):
        self.db_service = db_service
        self.download_service = download_service
        self.plugin_manager = plugin_manager
        self._initialized = False
        
        # Monitoring configuration
        self.check_interval = config_manager.get('check_interval', 3600)  # 1 hour default
        self.max_concurrent_checks = config_manager.get('max_concurrent_downloads', 3)
        self.enable_auto_download = config_manager.get('auto_download_new', True)
        
        # State management
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
        self._checking_creators: Set[str] = set()
        
        # Statistics
        self._stats = MonitoringStats()
        
        # Event callbacks
        self._callbacks: Dict[str, List[Callable]] = {
            'creator_checked': [],
            'new_videos_found': [],
            'auto_download_started': [],
            'monitoring_error': []
        }
    
    async def initialize(self) -> bool:
        """Initialize the creator monitor service"""
        if self._initialized:
            return True
        
        try:
            # Initialize plugin manager if not provided
            if self.plugin_manager is None:
                self.plugin_manager = PluginManager()
                await self.plugin_manager.initialize()
            
            # Initialize download service if not provided
            if self.download_service is None:
                from app.services.download_service import get_download_service
                self.download_service = await get_download_service(self.db_service)
            
            self._initialized = True
            logger.info("Creator monitor service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize creator monitor service: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the creator monitor service"""
        if not self._initialized:
            return
        
        try:
            await self.stop_monitoring()
            
            if self.plugin_manager:
                await self.plugin_manager.shutdown()
            
            self._initialized = False
            logger.info("Creator monitor service shut down")
            
        except Exception as e:
            logger.error(f"Error during creator monitor service shutdown: {e}")
    
    async def start_monitoring(self) -> bool:
        """Start periodic creator monitoring"""
        if not self._initialized:
            raise RuntimeError("Creator monitor service not initialized")
        
        if self._running:
            logger.warning("Creator monitoring is already running")
            return True
        
        try:
            self._running = True
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info(f"Started creator monitoring with {self.check_interval}s interval")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start creator monitoring: {e}")
            self._running = False
            return False
    
    async def stop_monitoring(self):
        """Stop periodic creator monitoring"""
        if not self._running:
            return
        
        self._running = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
        
        logger.info("Stopped creator monitoring")
    
    async def add_creator(self, 
                         channel_url: str, 
                         auto_download: bool = False,
                         priority: int = 5,
                         download_options: Optional[DownloadOptions] = None) -> Optional[str]:
        """
        Add a new creator to monitor
        
        Args:
            channel_url: Creator's channel URL
            auto_download: Enable auto-download for new videos
            priority: Priority level (1-10, higher is more important)
            download_options: Download options for this creator
            
        Returns:
            Creator ID if successful, None otherwise
        """
        if not self._initialized or not self.db_service:
            return None
        
        try:
            # Check if creator already exists
            existing = await self.db_service.creator.get_by_url(channel_url)
            if existing:
                logger.warning(f"Creator already exists: {channel_url}")
                return existing.id
            
            # Extract creator information
            creator_info = await self._extract_creator_info(channel_url)
            if not creator_info:
                logger.error(f"Failed to extract creator info from: {channel_url}")
                return None
            
            # Create creator profile
            creator = CreatorProfile(
                id="",  # Will be generated
                name=creator_info.get('name', 'Unknown Creator'),
                platform=creator_info.get('platform', Platform.UNKNOWN),
                channel_url=channel_url,
                avatar_url=creator_info.get('avatar_url', ''),
                last_check=datetime.now(),
                auto_download=auto_download,
                priority=priority,
                description=creator_info.get('description'),
                subscriber_count=creator_info.get('subscriber_count'),
                video_count=creator_info.get('video_count'),
                last_video_count=creator_info.get('video_count'),
                download_options=download_options
            )
            
            # Save to database
            success = await self.db_service.creator.create(creator)
            if success:
                self._stats.total_creators += 1
                if auto_download:
                    self._stats.auto_download_enabled += 1
                
                logger.info(f"Added creator: {creator.name} ({creator.id})")
                return creator.id
            else:
                logger.error(f"Failed to save creator to database: {channel_url}")
                return None
                
        except Exception as e:
            logger.error(f"Error adding creator {channel_url}: {e}")
            return None
    
    async def remove_creator(self, creator_id: str) -> bool:
        """Remove a creator from monitoring"""
        if not self._initialized or not self.db_service:
            return False
        
        try:
            success = await self.db_service.creator.delete(creator_id)
            if success:
                self._stats.total_creators = max(0, self._stats.total_creators - 1)
                logger.info(f"Removed creator: {creator_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error removing creator {creator_id}: {e}")
            return False
    
    async def update_creator(self, creator: CreatorProfile) -> bool:
        """Update creator profile"""
        if not self._initialized or not self.db_service:
            return False
        
        try:
            success = await self.db_service.creator.update(creator)
            if success:
                logger.info(f"Updated creator: {creator.name} ({creator.id})")
            return success
            
        except Exception as e:
            logger.error(f"Error updating creator {creator.id}: {e}")
            return False
    
    async def get_all_creators(self) -> List[CreatorProfile]:
        """Get all monitored creators"""
        if not self._initialized or not self.db_service:
            return []
        
        try:
            return await self.db_service.creator.get_all()
        except Exception as e:
            logger.error(f"Error getting creators: {e}")
            return []
    
    async def get_creator_by_id(self, creator_id: str) -> Optional[CreatorProfile]:
        """Get creator by ID"""
        if not self._initialized or not self.db_service:
            return None
        
        try:
            return await self.db_service.creator.get_by_id(creator_id)
        except Exception as e:
            logger.error(f"Error getting creator {creator_id}: {e}")
            return None    

    async def check_creator_updates(self, creator_id: str) -> CreatorUpdateResult:
        """
        Check for updates from a specific creator
        
        Args:
            creator_id: Creator ID to check
            
        Returns:
            CreatorUpdateResult with check results
        """
        if not self._initialized or not self.db_service:
            return CreatorUpdateResult(creator_id, False, error_message="Service not initialized")
        
        # Prevent concurrent checks for the same creator
        if creator_id in self._checking_creators:
            return CreatorUpdateResult(creator_id, False, error_message="Already checking this creator")
        
        self._checking_creators.add(creator_id)
        
        try:
            # Get creator profile
            creator = await self.db_service.creator.get_by_id(creator_id)
            if not creator:
                return CreatorUpdateResult(creator_id, False, error_message="Creator not found")
            
            # Extract current video information
            current_info = await self._extract_creator_info(creator.channel_url)
            if not current_info:
                return CreatorUpdateResult(creator_id, False, error_message="Failed to extract creator info")
            
            # Detect new videos
            current_video_count = current_info.get('video_count', 0)
            last_video_count = creator.last_video_count or 0
            
            new_videos = []
            new_videos_count = 0
            
            if current_video_count > last_video_count:
                new_videos_count = current_video_count - last_video_count
                logger.info(f"Found {new_videos_count} new videos for {creator.name}")
                
                # Get new video details if possible
                try:
                    new_videos = await self._get_new_videos(creator, new_videos_count)
                except Exception as e:
                    logger.warning(f"Failed to get new video details for {creator.name}: {e}")
            
            # Update creator profile
            creator.video_count = current_video_count
            creator.last_video_count = current_video_count
            creator.last_check = datetime.now()
            creator.subscriber_count = current_info.get('subscriber_count', creator.subscriber_count)
            
            await self.db_service.creator.update(creator)
            
            # Update statistics
            self._stats.total_checks += 1
            self._stats.successful_checks += 1
            self._stats.last_check_time = datetime.now()
            
            if new_videos_count > 0:
                self._stats.new_videos_found += new_videos_count
                
                # Trigger auto-download if enabled
                if creator.auto_download and self.enable_auto_download:
                    await self._trigger_auto_download(creator, new_videos)
            
            result = CreatorUpdateResult(
                creator_id=creator_id,
                success=True,
                new_videos_count=new_videos_count,
                new_videos=new_videos
            )
            
            # Notify callbacks
            await self._notify_callbacks('creator_checked', result)
            if new_videos_count > 0:
                await self._notify_callbacks('new_videos_found', result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking creator {creator_id}: {e}")
            self._stats.failed_checks += 1
            
            result = CreatorUpdateResult(creator_id, False, error_message=str(e))
            await self._notify_callbacks('monitoring_error', result)
            return result
            
        finally:
            self._checking_creators.discard(creator_id)
    
    async def check_all_creators(self) -> List[CreatorUpdateResult]:
        """Check all creators for updates"""
        if not self._initialized or not self.db_service:
            return []
        
        try:
            # Get creators that need checking
            creators = await self.db_service.creator.get_needs_check(self.check_interval)
            
            if not creators:
                logger.debug("No creators need checking")
                return []
            
            logger.info(f"Checking {len(creators)} creators for updates")
            
            # Check creators with concurrency limit
            semaphore = asyncio.Semaphore(self.max_concurrent_checks)
            
            async def check_with_semaphore(creator):
                async with semaphore:
                    return await self.check_creator_updates(creator.id)
            
            # Execute checks concurrently
            tasks = [check_with_semaphore(creator) for creator in creators]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and return valid results
            valid_results = []
            for result in results:
                if isinstance(result, CreatorUpdateResult):
                    valid_results.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Creator check failed with exception: {result}")
            
            return valid_results
            
        except Exception as e:
            logger.error(f"Error checking all creators: {e}")
            return []
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("Started creator monitoring loop")
        
        while self._running:
            try:
                # Check all creators
                results = await self.check_all_creators()
                
                if results:
                    successful = sum(1 for r in results if r.success)
                    failed = len(results) - successful
                    new_videos_total = sum(r.new_videos_count for r in results)
                    
                    logger.info(f"Creator check completed: {successful} successful, {failed} failed, {new_videos_total} new videos")
                
                # Wait for next check interval
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                logger.info("Creator monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in creator monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
        
        logger.info("Creator monitoring loop stopped") 
   
    async def _extract_creator_info(self, channel_url: str) -> Optional[Dict[str, Any]]:
        """Extract creator information from channel URL"""
        try:
            if not self.plugin_manager:
                return None
            
            # Use plugin manager to extract channel information
            info = await self.plugin_manager.extract_info(channel_url)
            if not info:
                return None
            
            # Determine platform from URL
            platform = self._detect_platform(channel_url)
            
            return {
                'name': info.get('uploader', info.get('channel', 'Unknown Creator')),
                'platform': platform,
                'avatar_url': info.get('uploader_url', ''),
                'description': info.get('description', ''),
                'subscriber_count': info.get('subscriber_count'),
                'video_count': info.get('video_count', len(info.get('entries', [])))
            }
            
        except Exception as e:
            logger.error(f"Error extracting creator info from {channel_url}: {e}")
            return None
    
    async def _get_new_videos(self, creator: CreatorProfile, count: int) -> List[VideoMetadata]:
        """Get details of new videos from creator"""
        try:
            if not self.plugin_manager:
                return []
            
            # Extract recent videos from creator's channel
            info = await self.plugin_manager.extract_info(creator.channel_url)
            if not info or 'entries' not in info:
                return []
            
            # Get the most recent videos (up to the count of new videos)
            recent_entries = info['entries'][:count]
            new_videos = []
            
            for entry in recent_entries:
                try:
                    # Convert entry to VideoMetadata
                    metadata = VideoMetadata(
                        title=entry.get('title', 'Unknown Title'),
                        author=entry.get('uploader', creator.name),
                        thumbnail_url=entry.get('thumbnail', ''),
                        duration=entry.get('duration', 0),
                        view_count=entry.get('view_count', 0),
                        upload_date=datetime.now(),  # Should parse from entry if available
                        quality_options=[],
                        platform=creator.platform,
                        video_id=entry.get('id'),
                        channel_id=entry.get('channel_id'),
                        channel_url=creator.channel_url
                    )
                    new_videos.append(metadata)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse video entry: {e}")
                    continue
            
            return new_videos
            
        except Exception as e:
            logger.error(f"Error getting new videos for {creator.name}: {e}")
            return []
    
    async def _trigger_auto_download(self, creator: CreatorProfile, new_videos: List[VideoMetadata]):
        """Trigger auto-download for new videos"""
        if not self.download_service or not new_videos:
            return
        
        try:
            download_options = creator.download_options or DownloadOptions(
                output_path=config_manager.get('download_path', './downloads'),
                quality_preference=config_manager.get('default_quality', 'best')
            )
            
            # Add downloads for new videos
            task_ids = []
            for video in new_videos:
                try:
                    # Construct video URL (this depends on platform)
                    video_url = self._construct_video_url(video, creator.platform)
                    if video_url:
                        task_id = await self.download_service.add_download(video_url, download_options)
                        task_ids.append(task_id)
                        logger.info(f"Auto-download started for: {video.title}")
                    
                except Exception as e:
                    logger.error(f"Failed to start auto-download for {video.title}: {e}")
            
            if task_ids:
                self._stats.auto_downloads_triggered += len(task_ids)
                await self._notify_callbacks('auto_download_started', {
                    'creator': creator,
                    'videos': new_videos,
                    'task_ids': task_ids
                })
            
        except Exception as e:
            logger.error(f"Error triggering auto-download for {creator.name}: {e}")
    
    def _detect_platform(self, url: str) -> Platform:
        """Detect platform from URL"""
        url_lower = url.lower()
        
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return Platform.YOUTUBE
        elif 'bilibili.com' in url_lower:
            return Platform.BILIBILI
        elif 'tiktok.com' in url_lower:
            return Platform.TIKTOK
        elif 'instagram.com' in url_lower:
            return Platform.INSTAGRAM
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return Platform.TWITTER
        elif 'twitch.tv' in url_lower:
            return Platform.TWITCH
        elif 'weibo.com' in url_lower:
            return Platform.WEIBO
        elif 'tumblr.com' in url_lower:
            return Platform.TUMBLR
        elif 'pixiv.net' in url_lower:
            return Platform.PIXIV
        else:
            return Platform.UNKNOWN
    
    def _construct_video_url(self, video: VideoMetadata, platform: Platform) -> Optional[str]:
        """Construct video URL from metadata and platform"""
        if not video.video_id:
            return None
        
        if platform == Platform.YOUTUBE:
            return f"https://www.youtube.com/watch?v={video.video_id}"
        elif platform == Platform.BILIBILI:
            return f"https://www.bilibili.com/video/{video.video_id}"
        elif platform == Platform.TIKTOK:
            return f"https://www.tiktok.com/@{video.author}/video/{video.video_id}"
        elif platform == Platform.TWITTER:
            return f"https://twitter.com/{video.author}/status/{video.video_id}"
        # Add more platforms as needed
        else:
            return None
    
    def add_callback(self, event: str, callback: Callable) -> None:
        """Add event callback"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def remove_callback(self, event: str, callback: Callable) -> None:
        """Remove event callback"""
        if event in self._callbacks and callback in self._callbacks[event]:
            self._callbacks[event].remove(callback)
    
    def get_statistics(self) -> MonitoringStats:
        """Get monitoring statistics"""
        return self._stats
    
    def set_check_interval(self, interval: int) -> None:
        """Set check interval in seconds"""
        self.check_interval = max(300, interval)  # Minimum 5 minutes
        config_manager.set('check_interval', self.check_interval)
    
    def set_auto_download_enabled(self, enabled: bool) -> None:
        """Enable or disable auto-download globally"""
        self.enable_auto_download = enabled
        config_manager.set('auto_download_new', enabled)
    
    async def _notify_callbacks(self, event: str, data: Any) -> None:
        """Notify event callbacks"""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Error in {event} callback: {e}")


# Global creator monitor service instance
_creator_monitor_service: Optional[CreatorMonitorService] = None


async def get_creator_monitor_service(
    db_service: Optional[DatabaseService] = None,
    download_service: Optional[DownloadService] = None,
    plugin_manager: Optional[PluginManager] = None
) -> CreatorMonitorService:
    """Get global creator monitor service instance"""
    global _creator_monitor_service
    
    if _creator_monitor_service is None:
        _creator_monitor_service = CreatorMonitorService(db_service, download_service, plugin_manager)
        await _creator_monitor_service.initialize()
    
    return _creator_monitor_service


async def shutdown_creator_monitor_service() -> None:
    """Shutdown global creator monitor service"""
    global _creator_monitor_service
    
    if _creator_monitor_service is not None:
        await _creator_monitor_service.shutdown()
        _creator_monitor_service = None