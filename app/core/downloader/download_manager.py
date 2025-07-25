"""
Download manager that orchestrates all download operations.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from pathlib import Path

from app.data.models.core import (
    DownloadTask, TaskStatus, VideoMetadata, DownloadOptions, 
    DownloadResult, Platform
)
from .base import BaseDownloader, DownloadStatus
from .ytdlp_downloader import YtDlpDownloader
from .advanced_downloader import AdvancedDownloader
from .task_queue import TaskQueue, TaskPriority
from .progress_tracker import ProgressTracker
from .thread_pool import AdaptiveThreadPoolManager
from app.core.config import config_manager

logger = logging.getLogger(__name__)


class DownloadManager:
    """
    Central download manager that coordinates all download operations.
    Manages task queuing, progress tracking, and resource allocation.
    """
    
    def __init__(self):
        # Core components
        self.task_queue = TaskQueue(max_concurrent=config_manager.get('max_concurrent_downloads', 3))
        self.progress_tracker = ProgressTracker()
        self.thread_pool = AdaptiveThreadPoolManager(
            initial_workers=2,
            min_workers=1,
            max_workers=config_manager.get('max_concurrent_downloads', 3) * 2
        )
        
        # Downloaders
        self._downloaders: Dict[str, BaseDownloader] = {}
        self._register_downloaders()
        
        # State management
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []
        self._callbacks: Dict[str, List[Callable]] = {
            'task_added': [],
            'task_started': [],
            'task_completed': [],
            'task_failed': [],
            'task_cancelled': [],
            'progress_updated': [],
            'queue_changed': []
        }
        
        # Statistics
        self._stats = {
            'total_downloads': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'cancelled_downloads': 0,
            'total_bytes_downloaded': 0,
            'start_time': None
        }
    
    def _register_downloaders(self) -> None:
        """Register available downloaders"""
        try:
            self._downloaders['ytdlp'] = YtDlpDownloader()
            logger.info("Registered yt-dlp downloader")
        except ImportError as e:
            logger.error(f"Failed to register yt-dlp downloader: {e}")
        
        # Register advanced downloader for direct downloads and M3U8
        try:
            self._downloaders['advanced'] = AdvancedDownloader(
                max_concurrent_segments=config_manager.get('max_concurrent_segments', 4)
            )
            logger.info("Registered advanced downloader")
        except Exception as e:
            logger.error(f"Failed to register advanced downloader: {e}")
    
    async def start(self) -> None:
        """Start the download manager"""
        if self._running:
            return
        
        self._running = True
        self._stats['start_time'] = datetime.now()
        
        # Start components
        await self.progress_tracker.start()
        await self.thread_pool.start_adaptive_scaling()
        
        # Start worker tasks
        num_workers = config_manager.get('max_concurrent_downloads', 3)
        for i in range(num_workers):
            worker_task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._worker_tasks.append(worker_task)
        
        # Set up queue callbacks
        self.task_queue.add_queue_callback(self._on_queue_changed)
        
        logger.info(f"Download manager started with {num_workers} workers")
    
    async def stop(self) -> None:
        """Stop the download manager"""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel all worker tasks
        for task in self._worker_tasks:
            task.cancel()
        
        # Wait for workers to finish
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        
        self._worker_tasks.clear()
        
        # Stop components
        await self.progress_tracker.stop()
        await self.thread_pool.stop_adaptive_scaling()
        await self.thread_pool.shutdown(wait=True, timeout=30)
        
        logger.info("Download manager stopped")
    
    async def add_download(self, 
                          url: str, 
                          options: Optional[DownloadOptions] = None,
                          priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """
        Add a new download task.
        
        Args:
            url: URL to download
            options: Download options
            priority: Task priority
            
        Returns:
            Task ID
        """
        if not self._running:
            raise RuntimeError("Download manager is not running")
        
        # Create default options if not provided
        if options is None:
            options = DownloadOptions(
                output_path=config_manager.get('download_path'),
                quality_preference=config_manager.get('default_quality', 'best'),
                format_preference=config_manager.get('default_format', 'mp4'),
                enable_resume=config_manager.get('enable_resume', True)
            )
        
        # Extract metadata first
        try:
            downloader = self._get_downloader_for_url(url)
            metadata = await downloader.get_metadata(url)
        except Exception as e:
            logger.error(f"Failed to extract metadata for {url}: {e}")
            # Create minimal metadata
            metadata = VideoMetadata(
                title="Unknown Title",
                author="Unknown Author",
                thumbnail_url="",
                duration=0,
                view_count=0,
                upload_date=datetime.now(),
                quality_options=[],
                platform=Platform.UNKNOWN
            )
        
        # Create download task
        task = DownloadTask(
            id="",  # Will be generated in __post_init__
            url=url,
            metadata=metadata,
            status=TaskStatus.PENDING,
            progress=0.0,
            download_path=options.output_path,
            created_at=datetime.now(),
            options=options
        )
        
        # Add to queue and progress tracker
        await self.task_queue.add_task(task, priority)
        await self.progress_tracker.add_task(task)
        
        # Update statistics
        self._stats['total_downloads'] += 1
        
        # Notify callbacks
        await self._notify_callbacks('task_added', task)
        
        logger.info(f"Added download task {task.id} for {url}")
        return task.id
    
    async def cancel_download(self, task_id: str) -> bool:
        """Cancel a download task"""
        success = await self.task_queue.cancel_task(task_id)
        if success:
            await self.progress_tracker.remove_task(task_id)
            self._stats['cancelled_downloads'] += 1
            
            # Get task for callback
            task = self.task_queue.get_task_by_id(task_id)
            if task:
                await self._notify_callbacks('task_cancelled', task)
            
            logger.info(f"Cancelled download task {task_id}")
        
        return success
    
    async def pause_download(self, task_id: str) -> bool:
        """Pause a download task"""
        return await self.task_queue.pause_task(task_id)
    
    async def resume_download(self, task_id: str) -> bool:
        """Resume a download task"""
        return await self.task_queue.resume_task(task_id)
    
    async def get_task_status(self, task_id: str) -> Optional[DownloadTask]:
        """Get status of a download task"""
        return self.task_queue.get_task_by_id(task_id)
    
    async def get_all_tasks(self) -> Dict[str, Any]:
        """Get all tasks with their current status"""
        return self.task_queue.get_queue_status()
    
    async def get_progress(self, task_id: Optional[str] = None) -> Any:
        """Get progress information"""
        if task_id:
            return await self.progress_tracker.get_task_progress(task_id)
        else:
            return await self.progress_tracker.get_global_progress()
    
    async def clear_completed_tasks(self) -> None:
        """Clear completed tasks from queue"""
        await self.task_queue.clear_completed()
    
    async def clear_failed_tasks(self) -> None:
        """Clear failed tasks from queue"""
        await self.task_queue.clear_failed()
    
    async def retry_failed_tasks(self) -> None:
        """Retry all failed tasks"""
        await self.task_queue.retry_failed_tasks()
    
    def set_max_concurrent_downloads(self, max_concurrent: int) -> None:
        """Set maximum concurrent downloads"""
        self.task_queue.set_max_concurrent(max_concurrent)
        # Also update thread pool
        self.thread_pool.max_workers_limit = max_concurrent * 2
        config_manager.set('max_concurrent_downloads', max_concurrent)
    
    def add_callback(self, event: str, callback: Callable) -> None:
        """Add event callback"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def remove_callback(self, event: str, callback: Callable) -> None:
        """Remove event callback"""
        if event in self._callbacks and callback in self._callbacks[event]:
            self._callbacks[event].remove(callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get download manager statistics"""
        stats = self._stats.copy()
        
        # Add runtime statistics
        if stats['start_time']:
            stats['uptime'] = (datetime.now() - stats['start_time']).total_seconds()
        
        # Add queue statistics
        queue_status = self.task_queue.get_queue_status()
        stats.update(queue_status)
        
        # Add thread pool statistics
        thread_stats = self.thread_pool.get_stats()
        stats['thread_pool'] = {
            'max_workers': thread_stats.max_workers,
            'active_workers': thread_stats.active_workers,
            'utilization': thread_stats.utilization_percentage
        }
        
        return stats
    
    async def _worker_loop(self, worker_name: str) -> None:
        """Main worker loop for processing download tasks"""
        logger.info(f"Started download worker: {worker_name}")
        
        while self._running:
            try:
                # Get next task from queue
                queued_task = await self.task_queue.get_next_task()
                if queued_task is None:
                    # No tasks available, wait a bit
                    await asyncio.sleep(1)
                    continue
                
                task = queued_task.task
                logger.info(f"Worker {worker_name} processing task {task.id}")
                
                # Notify task started
                await self._notify_callbacks('task_started', task)
                await self.progress_tracker.update_task_status(task.id, TaskStatus.DOWNLOADING)
                
                # Process the download
                success = await self._process_download_task(task)
                
                # Complete the task in queue
                await self.task_queue.complete_task(task.id, success)
                
                if success:
                    self._stats['successful_downloads'] += 1
                    await self._notify_callbacks('task_completed', task)
                else:
                    self._stats['failed_downloads'] += 1
                    await self._notify_callbacks('task_failed', task)
                
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Error in worker {worker_name}: {e}")
                await asyncio.sleep(5)  # Wait before retrying
        
        logger.info(f"Stopped download worker: {worker_name}")
    
    async def _process_download_task(self, task: DownloadTask) -> bool:
        """Process a single download task"""
        try:
            # Get appropriate downloader
            downloader = self._get_downloader_for_url(task.url)
            
            # Set up progress callbacks
            downloader.set_progress_callback(
                lambda progress: asyncio.create_task(
                    self.progress_tracker.update_task_progress(task.id, progress)
                )
            )
            
            # Submit download to thread pool
            future = await self.thread_pool.submit_task(
                task.id,
                self._run_download_sync,
                downloader,
                task.url,
                task.options
            )
            
            # Wait for completion
            result = await self.thread_pool.wait_for_task(task.id)
            
            if isinstance(result, DownloadResult) and result.success:
                # Update task with result
                task.status = TaskStatus.COMPLETED
                task.progress = 100.0
                task.completed_at = datetime.now()
                task.file_size = result.file_size
                
                # Update statistics
                if result.file_size:
                    self._stats['total_bytes_downloaded'] += result.file_size
                
                return True
            else:
                task.status = TaskStatus.FAILED
                if isinstance(result, DownloadResult):
                    task.error_message = result.error_message
                return False
                
        except Exception as e:
            logger.error(f"Download task {task.id} failed: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            return False
    
    def _run_download_sync(self, downloader: BaseDownloader, url: str, options: DownloadOptions) -> DownloadResult:
        """Run download synchronously (for thread pool)"""
        # This needs to be synchronous for the thread pool
        # We'll need to use asyncio.run or similar
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(downloader.download(url, options))
        finally:
            loop.close()
    
    def _get_downloader_for_url(self, url: str) -> BaseDownloader:
        """Get appropriate downloader for URL"""
        # Check if URL is a direct download or M3U8
        if self._is_direct_download_url(url) or url.lower().endswith('.m3u8'):
            # Use advanced downloader for direct downloads and M3U8
            if 'advanced' in self._downloaders:
                return self._downloaders['advanced']
        
        # Use yt-dlp for platform-specific URLs
        if 'ytdlp' in self._downloaders:
            return self._downloaders['ytdlp']
        
        # Fallback to advanced downloader if available
        if 'advanced' in self._downloaders:
            return self._downloaders['advanced']
        
        raise RuntimeError("No suitable downloader available")
    
    def _is_direct_download_url(self, url: str) -> bool:
        """Check if URL is a direct download link"""
        # Common video/audio file extensions
        direct_extensions = [
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a',
            '.ts', '.m3u8', '.mpd'
        ]
        
        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in direct_extensions)
    
    async def _on_queue_changed(self, queue_status: Dict[str, Any]) -> None:
        """Handle queue status changes"""
        await self._notify_callbacks('queue_changed', queue_status)
    
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
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


# Global download manager instance
_download_manager: Optional[DownloadManager] = None


async def get_download_manager() -> DownloadManager:
    """Get global download manager instance"""
    global _download_manager
    
    if _download_manager is None:
        _download_manager = DownloadManager()
        await _download_manager.start()
    
    return _download_manager


async def shutdown_download_manager() -> None:
    """Shutdown global download manager"""
    global _download_manager
    
    if _download_manager is not None:
        await _download_manager.stop()
        _download_manager = None