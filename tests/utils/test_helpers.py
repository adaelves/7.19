"""
Test helper utilities and mock objects.
"""
import asyncio
import random
import string
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, AsyncMock
from pathlib import Path

from app.data.models.core import (
    VideoMetadata, DownloadTask, CreatorProfile, QualityOption,
    DownloadOptions, TaskStatus, Platform
)


class TestDataFactory:
    """Factory for creating test data objects"""
    
    @staticmethod
    def random_string(length: int = 10) -> str:
        """Generate random string"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    @staticmethod
    def random_url(domain: str = "example.com") -> str:
        """Generate random URL"""
        video_id = TestDataFactory.random_string(8)
        return f"https://{domain}/watch?v={video_id}"
    
    @staticmethod
    def create_quality_option(
        quality_id: str = "720p",
        resolution: str = "1280x720",
        format_name: str = "mp4",
        file_size: int = 50000000,
        bitrate: int = 2500
    ) -> QualityOption:
        """Create test quality option"""
        return QualityOption(
            quality_id=quality_id,
            resolution=resolution,
            format_name=format_name,
            file_size=file_size,
            bitrate=bitrate
        )
    
    @staticmethod
    def create_video_metadata(
        title: Optional[str] = None,
        author: Optional[str] = None,
        platform: Platform = Platform.YOUTUBE,
        duration: int = 300,
        view_count: int = 1000
    ) -> VideoMetadata:
        """Create test video metadata"""
        return VideoMetadata(
            title=title or f"Test Video {TestDataFactory.random_string(5)}",
            author=author or f"Test Author {TestDataFactory.random_string(5)}",
            thumbnail_url=f"https://example.com/thumb_{TestDataFactory.random_string(8)}.jpg",
            duration=duration,
            view_count=view_count,
            upload_date=datetime.now() - timedelta(days=random.randint(1, 365)),
            quality_options=[
                TestDataFactory.create_quality_option("720p", "1280x720"),
                TestDataFactory.create_quality_option("1080p", "1920x1080", file_size=100000000)
            ],
            platform=platform,
            video_id=TestDataFactory.random_string(11),
            channel_id=TestDataFactory.random_string(24)
        )
    
    @staticmethod
    def create_download_task(
        url: Optional[str] = None,
        status: TaskStatus = TaskStatus.PENDING,
        progress: float = 0.0,
        metadata: Optional[VideoMetadata] = None
    ) -> DownloadTask:
        """Create test download task"""
        task_id = TestDataFactory.random_string(12)
        return DownloadTask(
            id=task_id,
            url=url or TestDataFactory.random_url(),
            metadata=metadata or TestDataFactory.create_video_metadata(),
            status=status,
            progress=progress,
            download_path=f"/downloads/test_{task_id}.mp4",
            created_at=datetime.now() - timedelta(minutes=random.randint(1, 60)),
            file_size=50000000 if status == TaskStatus.COMPLETED else None,
            completed_at=datetime.now() if status == TaskStatus.COMPLETED else None
        )
    
    @staticmethod
    def create_creator_profile(
        name: Optional[str] = None,
        platform: Platform = Platform.YOUTUBE,
        auto_download: bool = True,
        priority: int = 5
    ) -> CreatorProfile:
        """Create test creator profile"""
        creator_id = TestDataFactory.random_string(10)
        creator_name = name or f"Test Creator {TestDataFactory.random_string(5)}"
        
        return CreatorProfile(
            id=creator_id,
            name=creator_name,
            platform=platform,
            channel_url=f"https://{platform.value.lower()}.com/channel/{creator_id}",
            avatar_url=f"https://example.com/avatar_{creator_id}.jpg",
            last_check=datetime.now() - timedelta(hours=random.randint(1, 24)),
            auto_download=auto_download,
            priority=priority,
            description=f"Test creator description for {creator_name}",
            subscriber_count=random.randint(1000, 1000000),
            video_count=random.randint(10, 500),
            tags=["test", "creator", platform.value.lower()]
        )
    
    @staticmethod
    def create_download_options(
        output_path: str = "/downloads",
        quality_preference: str = "720p",
        max_threads: int = 4
    ) -> DownloadOptions:
        """Create test download options"""
        return DownloadOptions(
            output_path=output_path,
            quality_preference=quality_preference,
            max_threads=max_threads,
            use_proxy=False,
            proxy_url=None,
            enable_resume=True,
            rate_limit=None
        )


class MockDownloadManager:
    """Mock download manager for testing"""
    
    def __init__(self):
        self.tasks: Dict[str, DownloadTask] = {}
        self.active_downloads = 0
        self.download_speed = 0
        self.callbacks = []
    
    async def add_task(self, task: DownloadTask) -> bool:
        """Add download task"""
        self.tasks[task.id] = task
        return True
    
    async def start_task(self, task_id: str) -> bool:
        """Start download task"""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.DOWNLOADING
            self.active_downloads += 1
            return True
        return False
    
    async def pause_task(self, task_id: str) -> bool:
        """Pause download task"""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.PAUSED
            return True
        return False
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel download task"""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.CANCELLED
            if self.active_downloads > 0:
                self.active_downloads -= 1
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """Get download task"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[DownloadTask]:
        """Get all download tasks"""
        return list(self.tasks.values())
    
    def get_active_tasks(self) -> List[DownloadTask]:
        """Get active download tasks"""
        return [task for task in self.tasks.values() 
                if task.status in [TaskStatus.DOWNLOADING, TaskStatus.PENDING]]
    
    def add_progress_callback(self, callback):
        """Add progress callback"""
        self.callbacks.append(callback)
    
    async def simulate_download_progress(self, task_id: str, duration: float = 1.0):
        """Simulate download progress for testing"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task.status = TaskStatus.DOWNLOADING
        
        steps = 10
        step_duration = duration / steps
        
        for i in range(steps + 1):
            progress = (i / steps) * 100
            task.progress = progress
            
            # Notify callbacks
            for callback in self.callbacks:
                await callback(task_id, progress)
            
            if i < steps:
                await asyncio.sleep(step_duration)
        
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        self.active_downloads = max(0, self.active_downloads - 1)


class MockExtractor:
    """Mock extractor for testing"""
    
    def __init__(self, supported_domains: List[str]):
        self.supported_domains = supported_domains
        self._extract_info = AsyncMock()
        self._get_download_urls = AsyncMock()
        self._get_metadata = AsyncMock()
    
    def can_handle(self, url: str) -> bool:
        """Check if extractor can handle URL"""
        return any(domain in url for domain in self.supported_domains)
    
    async def extract_info(self, url: str) -> Dict[str, Any]:
        """Extract video information"""
        return await self._extract_info(url)
    
    async def get_download_urls(self, info: Dict[str, Any]) -> List[str]:
        """Get download URLs"""
        return await self._get_download_urls(info)
    
    async def get_metadata(self, url: str) -> VideoMetadata:
        """Get video metadata"""
        return await self._get_metadata(url)


class TestFileManager:
    """Test file manager for handling test files"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.created_files = []
        self.created_dirs = []
    
    def create_test_file(self, relative_path: str, content: str = "") -> Path:
        """Create test file"""
        file_path = self.base_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        self.created_files.append(file_path)
        return file_path
    
    def create_test_dir(self, relative_path: str) -> Path:
        """Create test directory"""
        dir_path = self.base_path / relative_path
        dir_path.mkdir(parents=True, exist_ok=True)
        self.created_dirs.append(dir_path)
        return dir_path
    
    def cleanup(self):
        """Clean up created files and directories"""
        for file_path in self.created_files:
            if file_path.exists():
                file_path.unlink()
        
        for dir_path in reversed(self.created_dirs):
            if dir_path.exists() and not any(dir_path.iterdir()):
                dir_path.rmdir()


class PerformanceTimer:
    """Timer for performance measurements"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start timer"""
        import time
        self.start_time = time.perf_counter()
    
    def stop(self):
        """Stop timer"""
        import time
        self.end_time = time.perf_counter()
    
    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds"""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.perf_counter()
        return end - self.start_time
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class NetworkMocker:
    """Network request mocker for testing"""
    
    def __init__(self):
        self.responses = {}
        self.request_log = []
    
    def add_response(self, url_pattern: str, response_data: Dict[str, Any]):
        """Add mock response for URL pattern"""
        self.responses[url_pattern] = response_data
    
    def get_response(self, url: str) -> Optional[Dict[str, Any]]:
        """Get mock response for URL"""
        for pattern, response in self.responses.items():
            if pattern in url:
                self.request_log.append(url)
                return response
        return None
    
    def clear_log(self):
        """Clear request log"""
        self.request_log.clear()
    
    def get_request_count(self, url_pattern: str) -> int:
        """Get number of requests matching pattern"""
        return sum(1 for url in self.request_log if url_pattern in url)