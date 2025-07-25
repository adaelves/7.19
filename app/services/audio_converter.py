"""
Audio conversion service for converting videos to MP3
"""
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import QObject, Signal, QThread

logger = logging.getLogger(__name__)


@dataclass
class ConversionTask:
    """Audio conversion task"""
    input_file: str
    output_file: str
    progress: float = 0.0
    status: str = "pending"  # pending, converting, completed, failed
    error: str = ""
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class AudioConverterWorker(QThread):
    """Audio conversion worker thread"""
    
    progress_updated = Signal(str, float)  # input_file, progress
    conversion_completed = Signal(str, str)  # input_file, output_file
    conversion_failed = Signal(str, str)  # input_file, error
    
    def __init__(self, input_file: str, output_file: str, quality: str = "192k"):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.quality = quality
        self.is_cancelled = False
        
    def run(self):
        """Run conversion in thread"""
        try:
            # Check if input file exists
            if not os.path.exists(self.input_file):
                self.conversion_failed.emit(self.input_file, "Input file not found")
                return
                
            # Create output directory if needed
            output_dir = Path(self.output_file).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Try to use ffmpeg first, then fallback to yt-dlp
            success = self._convert_with_ffmpeg()
            if not success:
                success = self._convert_with_ytdlp()
                
            if success and os.path.exists(self.output_file):
                self.conversion_completed.emit(self.input_file, self.output_file)
            else:
                self.conversion_failed.emit(self.input_file, "Conversion failed")
                
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            self.conversion_failed.emit(self.input_file, str(e))
    
    def _convert_with_ffmpeg(self) -> bool:
        """Convert using ffmpeg"""
        try:
            # Check if ffmpeg is available
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, check=True)
            
            # Build ffmpeg command
            cmd = [
                'ffmpeg',
                '-i', self.input_file,
                '-vn',  # No video
                '-acodec', 'libmp3lame',
                '-ab', self.quality,
                '-ar', '44100',
                '-y',  # Overwrite output file
                self.output_file
            ]
            
            # Run conversion
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Monitor progress (simplified)
            while process.poll() is None:
                if self.is_cancelled:
                    process.terminate()
                    return False
                    
                # Update progress (approximate)
                self.progress_updated.emit(self.input_file, 50.0)
                self.msleep(1000)
            
            # Final progress
            self.progress_updated.emit(self.input_file, 100.0)
            
            return process.returncode == 0
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.info("ffmpeg not available, trying alternative method")
            return False
    
    def _convert_with_ytdlp(self) -> bool:
        """Convert using yt-dlp (extract audio from already downloaded file)"""
        try:
            import yt_dlp
            
            # Use yt-dlp to extract audio
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': self.output_file.replace('.mp3', '.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': self.quality.replace('k', ''),
                }],
                'progress_hooks': [self._progress_hook],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract audio from local file
                ydl.process_info({
                    'url': self.input_file,
                    'title': Path(self.input_file).stem,
                    'ext': Path(self.input_file).suffix[1:],
                })
                
            return True
            
        except Exception as e:
            logger.error(f"yt-dlp audio extraction failed: {e}")
            return False
    
    def _progress_hook(self, d):
        """Progress hook for yt-dlp"""
        if self.is_cancelled:
            raise Exception("Conversion cancelled")
            
        if d['status'] == 'processing':
            # Approximate progress for post-processing
            self.progress_updated.emit(self.input_file, 75.0)
        elif d['status'] == 'finished':
            self.progress_updated.emit(self.input_file, 100.0)
    
    def cancel(self):
        """Cancel conversion"""
        self.is_cancelled = True


class AudioConverterService(QObject):
    """Audio conversion service"""
    
    conversion_started = Signal(str)  # input_file
    conversion_progress = Signal(str, float)  # input_file, progress
    conversion_completed = Signal(str, str)  # input_file, output_file
    conversion_failed = Signal(str, str)  # input_file, error
    
    def __init__(self):
        super().__init__()
        self.tasks = {}
        self.workers = {}
        
    def convert_to_mp3(self, input_file: str, output_dir: str, 
                      quality: str = "192k") -> bool:
        """Convert video file to MP3"""
        if not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            return False
            
        # Generate output filename
        input_path = Path(input_file)
        output_filename = input_path.stem + ".mp3"
        output_file = os.path.join(output_dir, output_filename)
        
        # Check if already converting
        if input_file in self.workers:
            logger.warning(f"Already converting: {input_file}")
            return False
            
        # Create task
        task = ConversionTask(
            input_file=input_file,
            output_file=output_file
        )
        self.tasks[input_file] = task
        
        # Create worker
        worker = AudioConverterWorker(
            input_file=input_file,
            output_file=output_file,
            quality=quality
        )
        
        # Connect signals
        worker.progress_updated.connect(self._on_progress_updated)
        worker.conversion_completed.connect(self._on_conversion_completed)
        worker.conversion_failed.connect(self._on_conversion_failed)
        worker.finished.connect(lambda: self._on_worker_finished(input_file))
        
        # Store worker and start
        self.workers[input_file] = worker
        worker.start()
        
        # Emit started signal
        self.conversion_started.emit(input_file)
        
        return True
    
    def _on_progress_updated(self, input_file: str, progress: float):
        """Handle progress update"""
        if input_file in self.tasks:
            self.tasks[input_file].progress = progress
            self.conversion_progress.emit(input_file, progress)
    
    def _on_conversion_completed(self, input_file: str, output_file: str):
        """Handle conversion completion"""
        if input_file in self.tasks:
            task = self.tasks[input_file]
            task.status = "completed"
            task.progress = 100.0
            
        self.conversion_completed.emit(input_file, output_file)
        logger.info(f"Audio conversion completed: {input_file} -> {output_file}")
    
    def _on_conversion_failed(self, input_file: str, error: str):
        """Handle conversion failure"""
        if input_file in self.tasks:
            task = self.tasks[input_file]
            task.status = "failed"
            task.error = error
            
        self.conversion_failed.emit(input_file, error)
        logger.error(f"Audio conversion failed: {input_file} - {error}")
    
    def _on_worker_finished(self, input_file: str):
        """Handle worker finished"""
        if input_file in self.workers:
            worker = self.workers[input_file]
            worker.deleteLater()
            del self.workers[input_file]
    
    def cancel_conversion(self, input_file: str) -> bool:
        """Cancel a conversion"""
        if input_file in self.workers:
            worker = self.workers[input_file]
            worker.cancel()
            worker.quit()
            worker.wait(3000)
            return True
        return False
    
    def get_task(self, input_file: str) -> Optional[ConversionTask]:
        """Get conversion task"""
        return self.tasks.get(input_file)
    
    def is_converting(self, input_file: str) -> bool:
        """Check if file is being converted"""
        return input_file in self.workers and self.workers[input_file].isRunning()