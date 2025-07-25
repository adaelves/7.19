"""
Download system components.
"""

from .base import BaseDownloader, DownloadStatus, ProgressInfo
from .ytdlp_downloader import YtDlpDownloader
from .task_queue import TaskQueue, TaskPriority, QueuedTask
from .progress_tracker import ProgressTracker, TaskProgress, GlobalProgress
from .thread_pool import ThreadPoolManager, AdaptiveThreadPoolManager, ThreadPoolStats
from .download_manager import DownloadManager, get_download_manager, shutdown_download_manager

__all__ = [
    # Base classes
    'BaseDownloader',
    'DownloadStatus', 
    'ProgressInfo',
    
    # Downloaders
    'YtDlpDownloader',
    
    # Task management
    'TaskQueue',
    'TaskPriority',
    'QueuedTask',
    
    # Progress tracking
    'ProgressTracker',
    'TaskProgress',
    'GlobalProgress',
    
    # Thread management
    'ThreadPoolManager',
    'AdaptiveThreadPoolManager',
    'ThreadPoolStats',
    
    # Main manager
    'DownloadManager',
    'get_download_manager',
    'shutdown_download_manager'
]