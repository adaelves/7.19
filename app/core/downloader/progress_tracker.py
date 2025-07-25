"""
Progress tracking system for download operations.
"""
import asyncio
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import logging

from app.data.models.core import DownloadTask, TaskStatus
from .base import ProgressInfo

logger = logging.getLogger(__name__)


@dataclass
class SpeedSample:
    """Speed measurement sample"""
    timestamp: float
    bytes_downloaded: int


@dataclass
class TaskProgress:
    """Progress information for a single task"""
    task_id: str
    progress_info: ProgressInfo
    start_time: Optional[datetime] = None
    last_update: datetime = field(default_factory=datetime.now)
    speed_samples: deque = field(default_factory=lambda: deque(maxlen=10))
    average_speed: float = 0.0
    peak_speed: float = 0.0
    
    def update_speed(self, current_bytes: int) -> None:
        """Update speed calculation with new data"""
        now = time.time()
        self.speed_samples.append(SpeedSample(now, current_bytes))
        
        if len(self.speed_samples) >= 2:
            # Calculate average speed over recent samples
            recent_samples = list(self.speed_samples)[-5:]  # Last 5 samples
            if len(recent_samples) >= 2:
                time_diff = recent_samples[-1].timestamp - recent_samples[0].timestamp
                bytes_diff = recent_samples[-1].bytes_downloaded - recent_samples[0].bytes_downloaded
                
                if time_diff > 0:
                    current_speed = bytes_diff / time_diff
                    self.average_speed = current_speed
                    self.peak_speed = max(self.peak_speed, current_speed)
                    self.progress_info.speed = current_speed


@dataclass
class GlobalProgress:
    """Global progress statistics"""
    total_tasks: int = 0
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_bytes_downloaded: int = 0
    total_bytes_to_download: int = 0
    overall_speed: float = 0.0
    estimated_time_remaining: Optional[int] = None
    
    @property
    def completion_percentage(self) -> float:
        """Calculate overall completion percentage"""
        if self.total_bytes_to_download > 0:
            return (self.total_bytes_downloaded / self.total_bytes_to_download) * 100
        elif self.total_tasks > 0:
            return (self.completed_tasks / self.total_tasks) * 100
        return 0.0


class ProgressTracker:
    """
    Centralized progress tracking for all download tasks.
    Provides real-time statistics, speed calculations, and ETA estimates.
    """
    
    def __init__(self):
        self._task_progress: Dict[str, TaskProgress] = {}
        self._global_progress = GlobalProgress()
        self._callbacks: List[Callable] = []
        self._update_interval = 1.0  # seconds
        self._last_global_update = time.time()
        self._lock = asyncio.Lock()
        
        # Start background update task
        self._update_task = None
        self._running = False
    
    async def start(self) -> None:
        """Start the progress tracker"""
        if not self._running:
            self._running = True
            self._update_task = asyncio.create_task(self._update_loop())
            logger.info("Progress tracker started")
    
    async def stop(self) -> None:
        """Stop the progress tracker"""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        logger.info("Progress tracker stopped")
    
    async def add_task(self, task: DownloadTask) -> None:
        """Add a task to progress tracking"""
        async with self._lock:
            self._task_progress[task.id] = TaskProgress(
                task_id=task.id,
                progress_info=ProgressInfo(),
                start_time=datetime.now() if task.status == TaskStatus.DOWNLOADING else None
            )
            await self._update_global_progress()
            logger.debug(f"Added task {task.id} to progress tracking")
    
    async def remove_task(self, task_id: str) -> None:
        """Remove a task from progress tracking"""
        async with self._lock:
            if task_id in self._task_progress:
                del self._task_progress[task_id]
                await self._update_global_progress()
                logger.debug(f"Removed task {task_id} from progress tracking")
    
    async def update_task_progress(self, task_id: str, progress: ProgressInfo) -> None:
        """Update progress for a specific task"""
        async with self._lock:
            if task_id in self._task_progress:
                task_progress = self._task_progress[task_id]
                
                # Update progress info
                old_progress = task_progress.progress_info
                task_progress.progress_info = progress
                task_progress.last_update = datetime.now()
                
                # Update speed calculation
                if progress.downloaded_bytes > old_progress.downloaded_bytes:
                    task_progress.update_speed(progress.downloaded_bytes)
                
                # Set start time if task just started downloading
                if task_progress.start_time is None and progress.downloaded_bytes > 0:
                    task_progress.start_time = datetime.now()
                
                await self._update_global_progress()
    
    async def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """Update task status"""
        async with self._lock:
            if task_id in self._task_progress:
                # Update global progress based on status change
                await self._update_global_progress()
    
    async def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """Get progress for a specific task"""
        async with self._lock:
            return self._task_progress.get(task_id)
    
    async def get_global_progress(self) -> GlobalProgress:
        """Get global progress statistics"""
        async with self._lock:
            return self._global_progress
    
    async def get_all_task_progress(self) -> Dict[str, TaskProgress]:
        """Get progress for all tasks"""
        async with self._lock:
            return self._task_progress.copy()
    
    def add_callback(self, callback: Callable[[GlobalProgress], None]) -> None:
        """Add callback for progress updates"""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable) -> None:
        """Remove progress callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    async def _update_loop(self) -> None:
        """Background update loop"""
        while self._running:
            try:
                await asyncio.sleep(self._update_interval)
                async with self._lock:
                    await self._update_global_progress()
                    await self._notify_callbacks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in progress update loop: {e}")
    
    async def _update_global_progress(self) -> None:
        """Update global progress statistics"""
        total_downloaded = 0
        total_to_download = 0
        total_speed = 0.0
        active_count = 0
        completed_count = 0
        failed_count = 0
        
        for task_progress in self._task_progress.values():
            progress = task_progress.progress_info
            
            total_downloaded += progress.downloaded_bytes
            if progress.total_bytes:
                total_to_download += progress.total_bytes
            
            if progress.speed > 0:
                total_speed += progress.speed
                active_count += 1
            
            # Note: We need task status to count completed/failed
            # This would require passing task status to the tracker
        
        # Calculate ETA
        eta = None
        if total_speed > 0 and total_to_download > total_downloaded:
            remaining_bytes = total_to_download - total_downloaded
            eta = int(remaining_bytes / total_speed)
        
        self._global_progress = GlobalProgress(
            total_tasks=len(self._task_progress),
            active_tasks=active_count,
            completed_tasks=completed_count,
            failed_tasks=failed_count,
            total_bytes_downloaded=total_downloaded,
            total_bytes_to_download=total_to_download,
            overall_speed=total_speed,
            estimated_time_remaining=eta
        )
    
    async def _notify_callbacks(self) -> None:
        """Notify all callbacks about progress updates"""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self._global_progress)
                else:
                    callback(self._global_progress)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
    
    def get_task_statistics(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed statistics for a task"""
        if task_id not in self._task_progress:
            return None
        
        task_progress = self._task_progress[task_id]
        progress = task_progress.progress_info
        
        # Calculate elapsed time
        elapsed_time = None
        if task_progress.start_time:
            elapsed_time = (datetime.now() - task_progress.start_time).total_seconds()
        
        # Calculate average speed over entire download
        average_speed_overall = 0.0
        if elapsed_time and elapsed_time > 0:
            average_speed_overall = progress.downloaded_bytes / elapsed_time
        
        return {
            'task_id': task_id,
            'downloaded_bytes': progress.downloaded_bytes,
            'total_bytes': progress.total_bytes,
            'percentage': progress.percentage,
            'current_speed': progress.speed,
            'average_speed': task_progress.average_speed,
            'peak_speed': task_progress.peak_speed,
            'average_speed_overall': average_speed_overall,
            'eta': progress.eta,
            'elapsed_time': elapsed_time,
            'start_time': task_progress.start_time,
            'last_update': task_progress.last_update
        }
    
    def format_speed(self, speed: float) -> str:
        """Format speed in human-readable format"""
        if speed < 1024:
            return f"{speed:.1f} B/s"
        elif speed < 1024 * 1024:
            return f"{speed / 1024:.1f} KB/s"
        elif speed < 1024 * 1024 * 1024:
            return f"{speed / (1024 * 1024):.1f} MB/s"
        else:
            return f"{speed / (1024 * 1024 * 1024):.1f} GB/s"
    
    def format_size(self, size: int) -> str:
        """Format file size in human-readable format"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"
    
    def format_time(self, seconds: Optional[int]) -> str:
        """Format time in human-readable format"""
        if seconds is None:
            return "Unknown"
        
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"