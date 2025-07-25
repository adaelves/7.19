"""
Real download service implementation using yt-dlp
"""
import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from datetime import datetime

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

from PySide6.QtCore import QObject, Signal, QThread, QTimer
from app.core.portable import get_portable_manager
# FFmpeg已集成在yt-dlp中，无需额外的音频转换器

logger = logging.getLogger(__name__)


@dataclass
class DownloadTask:
    """Download task data class"""
    url: str
    title: str = ""
    filename: str = ""
    progress: float = 0.0
    status: str = "pending"  # pending, downloading, completed, failed
    error: str = ""
    file_size: int = 0
    downloaded_size: int = 0
    speed: str = ""
    eta: str = ""
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class DownloadWorker(QThread):
    """Download worker thread"""
    
    progress_updated = Signal(str, float, dict)  # url, progress, info
    download_completed = Signal(str, str)  # url, filepath
    download_failed = Signal(str, str)  # url, error
    
    def __init__(self, url: str, download_path: str, options: Dict[str, Any] = None):
        super().__init__()
        self.url = url
        self.download_path = download_path
        self.options = options or {}
        self.is_cancelled = False
        
    def run(self):
        """Run download in thread"""
        if not yt_dlp:
            self.download_failed.emit(self.url, "yt-dlp not available")
            return
            
        try:
            # Prepare download options
            ydl_opts = {
                'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                'format': self.options.get('quality', 'best'),
                'noplaylist': True,
                'progress_hooks': [self._progress_hook],
            }
            
            # Add additional options
            if 'proxy' in self.options:
                ydl_opts['proxy'] = self.options['proxy']
                
            if 'rate_limit' in self.options:
                ydl_opts['ratelimit'] = self.options['rate_limit']
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first
                info = ydl.extract_info(self.url, download=False)
                title = info.get('title', 'Unknown')
                
                if self.is_cancelled:
                    return
                    
                # Start download
                ydl.download([self.url])
                
                # Find downloaded file
                downloaded_file = self._find_downloaded_file(title)
                if downloaded_file:
                    self.download_completed.emit(self.url, downloaded_file)
                else:
                    self.download_failed.emit(self.url, "Downloaded file not found")
                    
        except Exception as e:
            logger.error(f"Download failed for {self.url}: {e}")
            self.download_failed.emit(self.url, str(e))
    
    def _progress_hook(self, d):
        """Progress hook for yt-dlp"""
        if self.is_cancelled:
            raise Exception("Download cancelled")
            
        if d['status'] == 'downloading':
            progress = 0
            if d.get('total_bytes'):
                progress = (d.get('downloaded_bytes', 0) / d['total_bytes']) * 100
            elif d.get('total_bytes_estimate'):
                progress = (d.get('downloaded_bytes', 0) / d['total_bytes_estimate']) * 100
                
            info = {
                'downloaded_bytes': d.get('downloaded_bytes', 0),
                'total_bytes': d.get('total_bytes') or d.get('total_bytes_estimate', 0),
                'speed': d.get('speed', 0),
                'eta': d.get('eta', 0),
                'filename': d.get('filename', ''),
            }
            
            self.progress_updated.emit(self.url, progress, info)
            
    def _find_downloaded_file(self, title: str) -> Optional[str]:
        """Find the downloaded file"""
        download_dir = Path(self.download_path)
        
        # Look for files with similar names
        for file_path in download_dir.glob("*"):
            if title.lower() in file_path.name.lower():
                return str(file_path)
                
        return None
    
    def cancel(self):
        """Cancel download"""
        self.is_cancelled = True


class DownloadService(QObject):
    """Main download service"""
    
    task_added = Signal(str)  # url
    task_updated = Signal(str, dict)  # url, task_data
    task_completed = Signal(str, str)  # url, filepath
    task_failed = Signal(str, str)  # url, error
    
    def __init__(self):
        super().__init__()
        self.portable_manager = get_portable_manager()
        self.tasks: Dict[str, DownloadTask] = {}
        self.workers: Dict[str, DownloadWorker] = {}
        self.settings = self._load_settings()
        
        # FFmpeg已集成在yt-dlp中，用于视频处理
        
    def _load_settings(self) -> Dict[str, Any]:
        """Load download settings"""
        return {
            'download_path': str(self.portable_manager.get_downloads_directory()),
            'quality': 'best',
            'max_concurrent': 3,
            'rate_limit': None,
            'proxy': None,
        }
    
    def update_settings(self, settings: Dict[str, Any]):
        """Update download settings"""
        self.settings.update(settings)
        
    def add_download(self, url: str) -> bool:
        """Add a download task"""
        if url in self.tasks:
            logger.warning(f"URL already in download queue: {url}")
            return False
            
        # Create task
        task = DownloadTask(url=url)
        self.tasks[url] = task
        
        # Emit signal
        self.task_added.emit(url)
        
        # Start download if not too many concurrent downloads
        active_downloads = sum(1 for w in self.workers.values() if w.isRunning())
        if active_downloads < self.settings['max_concurrent']:
            self._start_download(url)
            
        return True
    
    def _start_download(self, url: str):
        """Start downloading a URL"""
        if url not in self.tasks:
            return
            
        task = self.tasks[url]
        task.status = "downloading"
        
        # Create download directory
        download_path = Path(self.settings['download_path'])
        download_path.mkdir(parents=True, exist_ok=True)
        
        # Create worker
        worker = DownloadWorker(
            url=url,
            download_path=str(download_path),
            options={
                'quality': self.settings['quality'],
                'rate_limit': self.settings['rate_limit'],
                'proxy': self.settings['proxy'],
            }
        )
        
        # Connect signals
        worker.progress_updated.connect(self._on_progress_updated)
        worker.download_completed.connect(self._on_download_completed)
        worker.download_failed.connect(self._on_download_failed)
        worker.finished.connect(lambda: self._on_worker_finished(url))
        
        # Store worker and start
        self.workers[url] = worker
        worker.start()
        
        # Update task
        self._update_task(url)
    
    def _on_progress_updated(self, url: str, progress: float, info: Dict):
        """Handle progress update"""
        if url in self.tasks:
            task = self.tasks[url]
            task.progress = progress
            task.downloaded_size = info.get('downloaded_bytes', 0)
            task.file_size = info.get('total_bytes', 0)
            
            # Format speed and ETA
            speed = info.get('speed', 0)
            if speed:
                if speed > 1024 * 1024:
                    task.speed = f"{speed / (1024 * 1024):.1f} MB/s"
                elif speed > 1024:
                    task.speed = f"{speed / 1024:.1f} KB/s"
                else:
                    task.speed = f"{speed:.0f} B/s"
            
            eta = info.get('eta', 0)
            if eta:
                task.eta = f"{eta // 60}:{eta % 60:02d}"
                
            filename = info.get('filename', '')
            if filename and not task.filename:
                task.filename = Path(filename).name
                
            self._update_task(url)
    
    def _on_download_completed(self, url: str, filepath: str):
        """Handle download completion"""
        if url in self.tasks:
            task = self.tasks[url]
            task.status = "completed"
            task.progress = 100.0
            task.filename = Path(filepath).name
            
            self._update_task(url)
            
            # 直接完成下载任务
            self.task_completed.emit(url, filepath)
            
            logger.info(f"Download completed: {url} -> {filepath}")
    
    def _on_download_failed(self, url: str, error: str):
        """Handle download failure"""
        if url in self.tasks:
            task = self.tasks[url]
            task.status = "failed"
            task.error = error
            
            self._update_task(url)
            self.task_failed.emit(url, error)
            
            logger.error(f"Download failed: {url} - {error}")
    
    def _on_worker_finished(self, url: str):
        """Handle worker finished"""
        if url in self.workers:
            worker = self.workers[url]
            worker.deleteLater()
            del self.workers[url]
            
        # Start next download if any pending
        self._start_next_download()
    
    def _start_next_download(self):
        """Start next pending download"""
        pending_tasks = [url for url, task in self.tasks.items() 
                        if task.status == "pending"]
        
        active_downloads = sum(1 for w in self.workers.values() if w.isRunning())
        
        if pending_tasks and active_downloads < self.settings['max_concurrent']:
            self._start_download(pending_tasks[0])
    
    def _update_task(self, url: str):
        """Update task and emit signal"""
        if url in self.tasks:
            task = self.tasks[url]
            task_data = {
                'title': task.title,
                'filename': task.filename,
                'progress': task.progress,
                'status': task.status,
                'error': task.error,
                'speed': task.speed,
                'eta': task.eta,
                'file_size': task.file_size,
                'downloaded_size': task.downloaded_size,
            }
            self.task_updated.emit(url, task_data)
    
    def get_task(self, url: str) -> Optional[DownloadTask]:
        """Get task by URL"""
        return self.tasks.get(url)
    
    def get_all_tasks(self) -> Dict[str, DownloadTask]:
        """Get all tasks"""
        return self.tasks.copy()
    
    def cancel_download(self, url: str) -> bool:
        """Cancel a download"""
        if url in self.workers:
            worker = self.workers[url]
            worker.cancel()
            worker.quit()
            worker.wait(3000)  # Wait up to 3 seconds
            return True
        return False
    
    def clear_completed(self):
        """Clear completed downloads"""
        completed_urls = [url for url, task in self.tasks.items() 
                         if task.status in ["completed", "failed"]]
        
        for url in completed_urls:
            if url not in self.workers:  # Don't remove active downloads
                del self.tasks[url]
    
    # FFmpeg已集成在yt-dlp中，用于视频处理