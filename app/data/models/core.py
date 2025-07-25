"""
Core data models for the video downloader application.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid


class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Platform(Enum):
    """Supported platforms"""
    YOUTUBE = "youtube"
    BILIBILI = "bilibili"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    PORNHUB = "pornhub"
    YOUPORN = "youporn"
    XVIDEO = "xvideo"
    XHAMSTER = "xhamster"
    KISSJAV = "kissjav"
    WEIBO = "weibo"
    TUMBLR = "tumblr"
    PIXIV = "pixiv"
    FC2 = "fc2"
    FLICKR = "flickr"
    TWITCH = "twitch"
    TWITTER = "twitter"
    UNKNOWN = "unknown"


@dataclass
class QualityOption:
    """Video quality option"""
    quality_id: str
    resolution: str  # e.g., "1920x1080"
    format_name: str  # e.g., "mp4", "webm"
    file_size: Optional[int] = None  # in bytes
    bitrate: Optional[int] = None  # in kbps
    fps: Optional[int] = None
    codec: Optional[str] = None
    is_audio_only: bool = False


@dataclass
class VideoMetadata:
    """Video metadata information"""
    title: str
    author: str
    thumbnail_url: str
    duration: int  # in seconds
    view_count: int
    upload_date: datetime
    quality_options: List[QualityOption]
    
    # Optional fields
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    like_count: Optional[int] = None
    dislike_count: Optional[int] = None
    comment_count: Optional[int] = None
    channel_id: Optional[str] = None
    channel_url: Optional[str] = None
    video_id: Optional[str] = None
    platform: Platform = Platform.UNKNOWN
    
    def __post_init__(self):
        """Post-initialization processing"""
        if isinstance(self.upload_date, str):
            # Handle string date conversion if needed
            try:
                self.upload_date = datetime.fromisoformat(self.upload_date)
            except ValueError:
                self.upload_date = datetime.now()


@dataclass
class DownloadOptions:
    """Download configuration options"""
    output_path: str
    quality_preference: Optional[str] = None  # e.g., "best", "worst", "720p"
    format_preference: Optional[str] = None  # e.g., "mp4", "webm"
    audio_only: bool = False
    subtitle_languages: List[str] = field(default_factory=list)
    
    # Advanced options
    max_threads: int = 4
    enable_resume: bool = True
    speed_limit: Optional[int] = None  # in KB/s
    proxy_url: Optional[str] = None
    cookies_file: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Advanced download features
    enable_segmented_download: bool = True  # Use multi-threaded segmented download
    segment_size: Optional[int] = None  # Segment size in bytes (auto-calculated if None)
    max_concurrent_segments: int = 4  # Maximum concurrent segments
    enable_adaptive_rate_limiting: bool = False  # Use adaptive rate limiting
    retry_attempts: int = 3  # Number of retry attempts for failed downloads
    retry_delay: float = 1.0  # Delay between retries in seconds
    
    # M3U8 specific options
    m3u8_segment_threads: int = 4  # Concurrent threads for M3U8 segments
    m3u8_merge_segments: bool = True  # Merge segments into single file
    
    # Proxy configuration
    proxy_type: Optional[str] = None  # 'http', 'https', 'socks4', 'socks5'
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    
    # File naming
    filename_template: str = "%(title)s.%(ext)s"
    overwrite_existing: bool = False
    
    def __post_init__(self):
        """Post-initialization validation"""
        if self.max_threads < 1:
            self.max_threads = 1
        elif self.max_threads > 16:
            self.max_threads = 16
        
        if self.max_concurrent_segments < 1:
            self.max_concurrent_segments = 1
        elif self.max_concurrent_segments > 16:
            self.max_concurrent_segments = 16
        
        if self.m3u8_segment_threads < 1:
            self.m3u8_segment_threads = 1
        elif self.m3u8_segment_threads > 8:
            self.m3u8_segment_threads = 8
        
        if self.retry_attempts < 0:
            self.retry_attempts = 0
        elif self.retry_attempts > 10:
            self.retry_attempts = 10


@dataclass
class DownloadResult:
    """Result of a download operation"""
    success: bool
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_time: Optional[float] = None  # in seconds
    error_message: Optional[str] = None
    metadata: Optional[VideoMetadata] = None
    md5_hash: Optional[str] = None


@dataclass
class DownloadTask:
    """Download task representation"""
    id: str
    url: str
    metadata: Optional[VideoMetadata]
    status: TaskStatus
    progress: float  # 0.0 to 100.0
    download_path: str
    created_at: datetime
    
    # Optional fields
    options: Optional[DownloadOptions] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    file_size: Optional[int] = None
    downloaded_bytes: int = 0
    download_speed: float = 0.0  # bytes per second
    eta: Optional[int] = None  # estimated time remaining in seconds
    
    def __post_init__(self):
        """Post-initialization processing"""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if isinstance(self.created_at, str):
            try:
                self.created_at = datetime.fromisoformat(self.created_at)
            except ValueError:
                self.created_at = datetime.now()
    
    @property
    def is_active(self) -> bool:
        """Check if task is currently active"""
        return self.status in [TaskStatus.DOWNLOADING, TaskStatus.PENDING]
    
    @property
    def is_completed(self) -> bool:
        """Check if task is completed"""
        return self.status == TaskStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if task has failed"""
        return self.status == TaskStatus.FAILED
    
    def update_progress(self, downloaded_bytes: int, total_bytes: Optional[int] = None, speed: float = 0.0):
        """Update download progress"""
        self.downloaded_bytes = downloaded_bytes
        self.download_speed = speed
        
        if total_bytes and total_bytes > 0:
            self.progress = (downloaded_bytes / total_bytes) * 100.0
            if speed > 0:
                remaining_bytes = total_bytes - downloaded_bytes
                self.eta = int(remaining_bytes / speed)
        else:
            self.progress = 0.0
            self.eta = None


@dataclass
class CreatorProfile:
    """Creator/Channel profile for monitoring"""
    id: str
    name: str
    platform: Platform
    channel_url: str
    avatar_url: str
    last_check: datetime
    auto_download: bool
    priority: int  # 1-10, higher is more important
    
    # Optional fields
    description: Optional[str] = None
    subscriber_count: Optional[int] = None
    video_count: Optional[int] = None
    last_video_count: Optional[int] = None
    last_video_date: Optional[datetime] = None
    download_options: Optional[DownloadOptions] = None
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization processing"""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if isinstance(self.last_check, str):
            try:
                self.last_check = datetime.fromisoformat(self.last_check)
            except ValueError:
                self.last_check = datetime.now()
        
        if self.priority < 1:
            self.priority = 1
        elif self.priority > 10:
            self.priority = 10
    
    @property
    def needs_check(self) -> bool:
        """Check if creator needs to be checked for updates"""
        # Check if it's been more than an hour since last check
        time_diff = datetime.now() - self.last_check
        return time_diff.total_seconds() > 3600  # 1 hour
    
    def update_last_check(self):
        """Update the last check timestamp"""
        self.last_check = datetime.now()


# Type aliases for convenience
TaskList = List[DownloadTask]
CreatorList = List[CreatorProfile]
MetadataDict = Dict[str, Any]