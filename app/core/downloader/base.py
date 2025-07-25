"""
Base downloader abstract class defining the interface for all downloaders.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from app.data.models.core import VideoMetadata, DownloadOptions, DownloadResult


class DownloadStatus(Enum):
    """Download status enumeration"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProgressInfo:
    """Progress information for downloads"""
    downloaded_bytes: int = 0
    total_bytes: Optional[int] = None
    speed: float = 0.0  # bytes per second
    eta: Optional[int] = None  # estimated time remaining in seconds
    percentage: float = 0.0


class BaseDownloader(ABC):
    """
    Abstract base class for all downloaders.
    Defines the unified interface for downloading content from various platforms.
    """
    
    def __init__(self):
        self.status = DownloadStatus.PENDING
        self.progress = ProgressInfo()
        self._callbacks = {}
    
    @abstractmethod
    async def download(self, url: str, options: DownloadOptions) -> DownloadResult:
        """
        Download content from the given URL.
        
        Args:
            url: The URL to download from
            options: Download configuration options
            
        Returns:
            DownloadResult containing the result information
        """
        pass
    
    @abstractmethod
    async def get_metadata(self, url: str) -> VideoMetadata:
        """
        Extract metadata from the given URL without downloading.
        
        Args:
            url: The URL to extract metadata from
            
        Returns:
            VideoMetadata containing the extracted information
        """
        pass
    
    @abstractmethod
    async def pause(self) -> None:
        """Pause the current download operation."""
        pass
    
    @abstractmethod
    async def resume(self) -> None:
        """Resume a paused download operation."""
        pass
    
    @abstractmethod
    async def cancel(self) -> None:
        """Cancel the current download operation."""
        pass
    
    def set_progress_callback(self, callback):
        """Set callback function for progress updates"""
        self._callbacks['progress'] = callback
    
    def set_status_callback(self, callback):
        """Set callback function for status updates"""
        self._callbacks['status'] = callback
    
    def _update_progress(self, progress: ProgressInfo):
        """Update progress and notify callbacks"""
        self.progress = progress
        if 'progress' in self._callbacks:
            self._callbacks['progress'](progress)
    
    def _update_status(self, status: DownloadStatus):
        """Update status and notify callbacks"""
        self.status = status
        if 'status' in self._callbacks:
            self._callbacks['status'](status)
    
    @property
    def is_active(self) -> bool:
        """Check if download is currently active"""
        return self.status in [DownloadStatus.DOWNLOADING, DownloadStatus.PENDING]
    
    @property
    def is_completed(self) -> bool:
        """Check if download is completed"""
        return self.status == DownloadStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if download has failed"""
        return self.status == DownloadStatus.FAILED