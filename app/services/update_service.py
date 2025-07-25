"""
Update service for checking and downloading application updates from GitHub releases.
"""

import asyncio
import json
import platform
import re
import tempfile
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

import aiohttp
import aiofiles
from packaging import version

from app.core.config import config_manager
from app.services.config_service import ConfigService


@dataclass
class ReleaseInfo:
    """Release information from GitHub API"""
    version: str
    tag_name: str
    release_date: datetime
    changelog: str
    download_url: str
    file_size: int
    is_prerelease: bool


@dataclass
class UpdateProgress:
    """Update progress information"""
    stage: str  # 'checking', 'downloading', 'extracting', 'installing', 'complete', 'error'
    progress: float  # 0.0 to 1.0
    message: str
    error: Optional[str] = None


class UpdateService:
    """Service for handling application updates"""
    
    def __init__(self, config_service: ConfigService):
        self.config_service = config_service
        self.github_repo = "your-username/multi-platform-video-downloader"  # Replace with actual repo
        self.api_base_url = f"https://api.github.com/repos/{self.github_repo}"
        self.current_version = self._get_current_version()
        self.platform = self._get_platform_name()
        
        # Update settings
        self.auto_check_enabled = config_service.get("update.auto_check", True)
        self.check_interval_hours = config_service.get("update.check_interval", 24)
        self.include_prereleases = config_service.get("update.include_prereleases", False)
        
        # Callbacks
        self.progress_callback = None
        self.update_available_callback = None
        
    def _get_current_version(self) -> str:
        """Get current application version"""
        try:
            # Try to read from version file
            version_file = Path("version.txt")
            if version_file.exists():
                return version_file.read_text().strip()
            
            # Fallback to config
            return config_manager.config.app_version
        except Exception:
            return "1.0.0"
    
    def _get_platform_name(self) -> str:
        """Get platform name for download selection"""
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "darwin":
            return "macos"
        elif system == "linux":
            return "linux"
        else:
            return "linux"  # Default fallback
    
    def set_progress_callback(self, callback):
        """Set callback for progress updates"""
        self.progress_callback = callback
    
    def set_update_available_callback(self, callback):
        """Set callback for when update is available"""
        self.update_available_callback = callback
    
    def _notify_progress(self, stage: str, progress: float, message: str, error: str = None):
        """Notify progress to callback"""
        if self.progress_callback:
            update_progress = UpdateProgress(stage, progress, message, error)
            self.progress_callback(update_progress)
    
    async def check_for_updates(self, force: bool = False) -> Optional[ReleaseInfo]:
        """
        Check for available updates
        
        Args:
            force: Force check even if auto-check is disabled
            
        Returns:
            ReleaseInfo if update available, None otherwise
        """
        if not force and not self.auto_check_enabled:
            return None
        
        # Check if enough time has passed since last check
        if not force:
            last_check = self.config_service.get("update.last_check")
            if last_check:
                last_check_time = datetime.fromisoformat(last_check)
                hours_since_check = (datetime.now() - last_check_time).total_seconds() / 3600
                if hours_since_check < self.check_interval_hours:
                    return None
        
        self._notify_progress("checking", 0.1, "正在检查更新...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get latest release
                url = f"{self.api_base_url}/releases/latest"
                if self.include_prereleases:
                    url = f"{self.api_base_url}/releases"
                
                async with session.get(url) as response:
                    if response.status != 200:
                        self._notify_progress("error", 0.0, "检查更新失败", f"HTTP {response.status}")
                        return None
                    
                    data = await response.json()
                    
                    # Handle multiple releases (prerelease case)
                    if isinstance(data, list):
                        if not data:
                            return None
                        release_data = data[0]  # Get latest
                    else:
                        release_data = data
                    
                    # Parse release info
                    release_info = await self._parse_release_data(release_data, session)
                    
                    # Update last check time
                    self.config_service.set("update.last_check", datetime.now().isoformat())
                    
                    # Check if update is available
                    if self._is_newer_version(release_info.version, self.current_version):
                        self._notify_progress("checking", 1.0, f"发现新版本: {release_info.version}")
                        
                        # Notify callback
                        if self.update_available_callback:
                            self.update_available_callback(release_info)
                        
                        return release_info
                    else:
                        self._notify_progress("checking", 1.0, "已是最新版本")
                        return None
                        
        except Exception as e:
            self._notify_progress("error", 0.0, "检查更新失败", str(e))
            return None
    
    async def _parse_release_data(self, release_data: Dict, session: aiohttp.ClientSession) -> ReleaseInfo:
        """Parse GitHub release data into ReleaseInfo"""
        tag_name = release_data["tag_name"]
        version_str = tag_name.lstrip("v")
        
        # Find download URL for current platform
        download_url = None
        file_size = 0
        
        for asset in release_data.get("assets", []):
            asset_name = asset["name"].lower()
            if self.platform in asset_name:
                download_url = asset["browser_download_url"]
                file_size = asset["size"]
                break
        
        if not download_url:
            raise ValueError(f"No download found for platform: {self.platform}")
        
        # Get detailed changelog if available
        changelog = release_data.get("body", "")
        
        # Try to get release-info.json for better changelog
        try:
            info_url = None
            for asset in release_data.get("assets", []):
                if asset["name"] == "release-info.json":
                    info_url = asset["browser_download_url"]
                    break
            
            if info_url:
                async with session.get(info_url) as response:
                    if response.status == 200:
                        info_data = await response.json()
                        changelog = info_data.get("changelog", changelog)
        except Exception:
            pass  # Use default changelog
        
        return ReleaseInfo(
            version=version_str,
            tag_name=tag_name,
            release_date=datetime.fromisoformat(release_data["published_at"].replace("Z", "+00:00")),
            changelog=changelog,
            download_url=download_url,
            file_size=file_size,
            is_prerelease=release_data.get("prerelease", False)
        )
    
    def _is_newer_version(self, remote_version: str, current_version: str) -> bool:
        """Compare versions to check if remote is newer"""
        try:
            return version.parse(remote_version) > version.parse(current_version)
        except Exception:
            # Fallback to string comparison
            return remote_version != current_version
    
    async def download_update(self, release_info: ReleaseInfo, download_path: Optional[Path] = None) -> Path:
        """
        Download update file
        
        Args:
            release_info: Release information
            download_path: Custom download path (optional)
            
        Returns:
            Path to downloaded file
        """
        if not download_path:
            download_path = Path(tempfile.gettempdir()) / f"update_{release_info.version}"
            download_path.mkdir(exist_ok=True)
        
        # Determine file extension
        url = release_info.download_url
        if url.endswith('.zip'):
            filename = f"update_{release_info.version}.zip"
        elif url.endswith('.tar.gz'):
            filename = f"update_{release_info.version}.tar.gz"
        else:
            filename = f"update_{release_info.version}"
        
        file_path = download_path / filename
        
        self._notify_progress("downloading", 0.0, f"开始下载 {release_info.version}...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"Download failed: HTTP {response.status}")
                    
                    total_size = release_info.file_size or int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            if total_size > 0:
                                progress = downloaded / total_size
                                self._notify_progress(
                                    "downloading", 
                                    progress, 
                                    f"下载中... {downloaded // 1024}KB / {total_size // 1024}KB"
                                )
            
            self._notify_progress("downloading", 1.0, "下载完成")
            return file_path
            
        except Exception as e:
            self._notify_progress("error", 0.0, "下载失败", str(e))
            raise
    
    async def extract_update(self, archive_path: Path, extract_path: Optional[Path] = None) -> Path:
        """
        Extract update archive
        
        Args:
            archive_path: Path to downloaded archive
            extract_path: Custom extraction path (optional)
            
        Returns:
            Path to extracted directory
        """
        if not extract_path:
            extract_path = archive_path.parent / "extracted"
        
        extract_path.mkdir(exist_ok=True)
        
        self._notify_progress("extracting", 0.0, "正在解压更新文件...")
        
        try:
            if archive_path.suffix == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
            elif archive_path.name.endswith('.tar.gz'):
                with tarfile.open(archive_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(extract_path)
            else:
                raise ValueError(f"Unsupported archive format: {archive_path}")
            
            self._notify_progress("extracting", 1.0, "解压完成")
            return extract_path
            
        except Exception as e:
            self._notify_progress("error", 0.0, "解压失败", str(e))
            raise
    
    async def install_update(self, extracted_path: Path, backup: bool = True) -> bool:
        """
        Install extracted update
        
        Args:
            extracted_path: Path to extracted update files
            backup: Whether to create backup of current installation
            
        Returns:
            True if installation successful
        """
        self._notify_progress("installing", 0.0, "准备安装更新...")
        
        try:
            current_dir = Path.cwd()
            
            # Create backup if requested
            if backup:
                backup_dir = current_dir.parent / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self._notify_progress("installing", 0.2, "创建备份...")
                
                # Simple backup - copy current directory
                import shutil
                shutil.copytree(current_dir, backup_dir, ignore=shutil.ignore_patterns('*.log', '__pycache__', '*.pyc'))
                
                # Store backup path for potential rollback
                self.config_service.set("update.last_backup", str(backup_dir))
            
            # Install update files
            self._notify_progress("installing", 0.5, "安装更新文件...")
            
            # Copy files from extracted directory
            import shutil
            for item in extracted_path.iterdir():
                if item.is_file():
                    dest = current_dir / item.name
                    shutil.copy2(item, dest)
                elif item.is_dir():
                    dest = current_dir / item.name
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(item, dest)
            
            # Update version info
            version_file = current_dir / "version.txt"
            version_file.write_text(self._get_latest_version_from_extracted(extracted_path))
            
            self._notify_progress("installing", 1.0, "更新安装完成")
            return True
            
        except Exception as e:
            self._notify_progress("error", 0.0, "安装失败", str(e))
            return False
    
    def _get_latest_version_from_extracted(self, extracted_path: Path) -> str:
        """Get version from extracted files"""
        # Try to find version in extracted files
        version_file = extracted_path / "version.txt"
        if version_file.exists():
            return version_file.read_text().strip()
        
        # Fallback - increment current version
        try:
            current = version.parse(self.current_version)
            return str(current)
        except Exception:
            return "1.0.0"
    
    async def rollback_update(self) -> bool:
        """
        Rollback to previous version using backup
        
        Returns:
            True if rollback successful
        """
        backup_path = self.config_service.get("update.last_backup")
        if not backup_path or not Path(backup_path).exists():
            return False
        
        self._notify_progress("installing", 0.0, "正在回滚更新...")
        
        try:
            current_dir = Path.cwd()
            backup_dir = Path(backup_path)
            
            # Remove current files
            import shutil
            temp_dir = current_dir.parent / "temp_rollback"
            shutil.move(current_dir, temp_dir)
            
            # Restore backup
            shutil.move(backup_dir, current_dir)
            
            # Clean up
            shutil.rmtree(temp_dir)
            
            self._notify_progress("installing", 1.0, "回滚完成")
            return True
            
        except Exception as e:
            self._notify_progress("error", 0.0, "回滚失败", str(e))
            return False
    
    def get_update_settings(self) -> Dict[str, Any]:
        """Get current update settings"""
        return {
            "auto_check": self.auto_check_enabled,
            "check_interval": self.check_interval_hours,
            "include_prereleases": self.include_prereleases,
            "current_version": self.current_version,
            "last_check": self.config_service.get("update.last_check")
        }
    
    def update_settings(self, settings: Dict[str, Any]):
        """Update settings"""
        if "auto_check" in settings:
            self.auto_check_enabled = settings["auto_check"]
            self.config_service.set("update.auto_check", self.auto_check_enabled)
        
        if "check_interval" in settings:
            self.check_interval_hours = settings["check_interval"]
            self.config_service.set("update.check_interval", self.check_interval_hours)
        
        if "include_prereleases" in settings:
            self.include_prereleases = settings["include_prereleases"]
            self.config_service.set("update.include_prereleases", self.include_prereleases)