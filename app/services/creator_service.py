"""
Creator monitoring service
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

from PySide6.QtCore import QObject, Signal, QTimer
from app.core.portable import get_portable_manager

logger = logging.getLogger(__name__)


@dataclass
class CreatorInfo:
    """Creator information"""
    url: str
    name: str = ""
    platform: str = ""
    last_check: Optional[datetime] = None
    video_count: int = 0
    auto_download: bool = False
    enabled: bool = True
    

@dataclass
class VideoInfo:
    """Video information"""
    url: str
    title: str
    creator_url: str
    upload_date: Optional[datetime] = None
    duration: int = 0  # seconds
    view_count: int = 0
    is_new: bool = False
    

class CreatorService(QObject):
    """Creator monitoring service"""
    
    creator_added = Signal(str)  # creator_url
    creator_updated = Signal(str, dict)  # creator_url, info
    creator_removed = Signal(str)  # creator_url
    new_videos_found = Signal(str, list)  # creator_url, video_list
    check_started = Signal()
    check_completed = Signal()
    
    def __init__(self):
        super().__init__()
        self.portable_manager = get_portable_manager()
        self.creators: Dict[str, CreatorInfo] = {}
        self.known_videos: Dict[str, Set[str]] = {}  # creator_url -> set of video_urls
        
        # Setup timer for periodic checks
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_all_creators)
        
        self._load_creators()
        
    def _load_creators(self):
        """Load creators from file"""
        creators_file = self.portable_manager.get_config_file("creators.json")
        try:
            if creators_file.exists():
                import json
                with open(creators_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for creator_data in data.get('creators', []):
                    creator = CreatorInfo(**creator_data)
                    if creator.last_check:
                        creator.last_check = datetime.fromisoformat(creator.last_check)
                    self.creators[creator.url] = creator
                    
                # Load known videos
                for creator_url, video_urls in data.get('known_videos', {}).items():
                    self.known_videos[creator_url] = set(video_urls)
                    
        except Exception as e:
            logger.error(f"Failed to load creators: {e}")
    
    def _save_creators(self):
        """Save creators to file"""
        creators_file = self.portable_manager.get_config_file("creators.json")
        try:
            creators_file.parent.mkdir(parents=True, exist_ok=True)
            
            creators_data = []
            for creator in self.creators.values():
                creator_dict = {
                    'url': creator.url,
                    'name': creator.name,
                    'platform': creator.platform,
                    'last_check': creator.last_check.isoformat() if creator.last_check else None,
                    'video_count': creator.video_count,
                    'auto_download': creator.auto_download,
                    'enabled': creator.enabled,
                }
                creators_data.append(creator_dict)
            
            known_videos_data = {}
            for creator_url, video_urls in self.known_videos.items():
                known_videos_data[creator_url] = list(video_urls)
            
            data = {
                'creators': creators_data,
                'known_videos': known_videos_data,
            }
            
            import json
            with open(creators_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save creators: {e}")
    
    def add_creator(self, url: str, auto_download: bool = False) -> bool:
        """Add a creator to monitor"""
        if url in self.creators:
            return False
            
        if not yt_dlp:
            logger.error("yt-dlp not available")
            return False
            
        try:
            # Extract creator info
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                
                creator = CreatorInfo(
                    url=url,
                    name=info.get('uploader', '') or info.get('channel', '') or url,
                    platform=self._detect_platform(url),
                    auto_download=auto_download,
                )
                
                self.creators[url] = creator
                self.known_videos[url] = set()
                
                # Initial check to populate known videos
                self._check_creator(url, is_initial=True)
                
                self._save_creators()
                self.creator_added.emit(url)
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to add creator {url}: {e}")
            return False
    
    def remove_creator(self, url: str) -> bool:
        """Remove a creator from monitoring"""
        if url not in self.creators:
            return False
            
        del self.creators[url]
        if url in self.known_videos:
            del self.known_videos[url]
            
        self._save_creators()
        self.creator_removed.emit(url)
        return True
    
    def update_creator(self, url: str, **kwargs) -> bool:
        """Update creator settings"""
        if url not in self.creators:
            return False
            
        creator = self.creators[url]
        for key, value in kwargs.items():
            if hasattr(creator, key):
                setattr(creator, key, value)
        
        self._save_creators()
        
        creator_info = {
            'name': creator.name,
            'platform': creator.platform,
            'last_check': creator.last_check,
            'video_count': creator.video_count,
            'auto_download': creator.auto_download,
            'enabled': creator.enabled,
        }
        self.creator_updated.emit(url, creator_info)
        return True
    
    def get_creators(self) -> Dict[str, CreatorInfo]:
        """Get all creators"""
        return self.creators.copy()
    
    def get_creator(self, url: str) -> Optional[CreatorInfo]:
        """Get specific creator"""
        return self.creators.get(url)
    
    def start_monitoring(self, interval_minutes: int = 60):
        """Start periodic monitoring"""
        if interval_minutes > 0:
            self.check_timer.start(interval_minutes * 60 * 1000)  # Convert to milliseconds
            logger.info(f"Started creator monitoring with {interval_minutes} minute interval")
    
    def stop_monitoring(self):
        """Stop periodic monitoring"""
        self.check_timer.stop()
        logger.info("Stopped creator monitoring")
    
    def check_all_creators(self):
        """Check all enabled creators for new videos"""
        if not yt_dlp:
            logger.error("yt-dlp not available")
            return
            
        self.check_started.emit()
        
        enabled_creators = [url for url, creator in self.creators.items() if creator.enabled]
        
        for creator_url in enabled_creators:
            try:
                self._check_creator(creator_url)
            except Exception as e:
                logger.error(f"Failed to check creator {creator_url}: {e}")
        
        self.check_completed.emit()
    
    def check_creator(self, url: str):
        """Check specific creator for new videos"""
        if url not in self.creators:
            return
            
        self._check_creator(url)
    
    def _check_creator(self, creator_url: str, is_initial: bool = False):
        """Internal method to check creator for new videos"""
        creator = self.creators[creator_url]
        
        try:
            with yt_dlp.YoutubeDL({
                'quiet': True,
                'extract_flat': True,
                'playlistend': 20,  # Check last 20 videos
            }) as ydl:
                info = ydl.extract_info(creator_url, download=False)
                
                if 'entries' not in info:
                    return
                
                new_videos = []
                current_video_urls = set()
                
                for entry in info['entries']:
                    if not entry:
                        continue
                        
                    video_url = entry.get('url') or entry.get('webpage_url')
                    if not video_url:
                        continue
                        
                    current_video_urls.add(video_url)
                    
                    # Check if this is a new video
                    if video_url not in self.known_videos[creator_url]:
                        video_info = VideoInfo(
                            url=video_url,
                            title=entry.get('title', 'Unknown'),
                            creator_url=creator_url,
                            duration=entry.get('duration', 0),
                            view_count=entry.get('view_count', 0),
                            is_new=True,
                        )
                        
                        # Try to parse upload date
                        upload_date = entry.get('upload_date')
                        if upload_date:
                            try:
                                video_info.upload_date = datetime.strptime(upload_date, '%Y%m%d')
                            except:
                                pass
                        
                        new_videos.append(video_info)
                
                # Update known videos
                self.known_videos[creator_url].update(current_video_urls)
                
                # Update creator info
                creator.last_check = datetime.now()
                creator.video_count = len(current_video_urls)
                
                # Emit signals
                if new_videos and not is_initial:
                    self.new_videos_found.emit(creator_url, new_videos)
                    logger.info(f"Found {len(new_videos)} new videos for {creator.name}")
                
                creator_info = {
                    'name': creator.name,
                    'platform': creator.platform,
                    'last_check': creator.last_check,
                    'video_count': creator.video_count,
                    'auto_download': creator.auto_download,
                    'enabled': creator.enabled,
                }
                self.creator_updated.emit(creator_url, creator_info)
                
        except Exception as e:
            logger.error(f"Failed to check creator {creator_url}: {e}")
        
        finally:
            self._save_creators()
    
    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL"""
        url_lower = url.lower()
        
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'YouTube'
        elif 'bilibili.com' in url_lower:
            return 'Bilibili'
        elif 'douyin.com' in url_lower or 'tiktok.com' in url_lower:
            return 'TikTok/Douyin'
        elif 'instagram.com' in url_lower:
            return 'Instagram'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'Twitter/X'
        else:
            return 'Unknown'
    
    def get_auto_download_creators(self) -> List[str]:
        """Get creators with auto-download enabled"""
        return [url for url, creator in self.creators.items() 
                if creator.auto_download and creator.enabled]