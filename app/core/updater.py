"""
Auto-updater core functionality for managing application updates.
"""

import asyncio
import sys
import os
import subprocess
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime, timedelta

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication, QMessageBox

from app.services.update_service import UpdateService, ReleaseInfo
from app.services.config_service import ConfigService
# UI imports moved to methods to avoid circular import


class AutoUpdater(QObject):
    """
    Auto-updater manager that handles automatic update checking and installation.
    """
    
    # Signals
    update_available = Signal(object)  # ReleaseInfo
    update_downloaded = Signal(str)    # file_path
    update_installed = Signal(bool)    # success
    error_occurred = Signal(str)       # error_message
    
    def __init__(self, config_service: ConfigService, parent=None):
        super().__init__(parent)
        
        self.config_service = config_service
        self.update_service = UpdateService(config_service)
        
        # Auto-check timer
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_for_updates)
        
        # Settings
        self.auto_check_enabled = config_service.get("update.auto_check", True)
        self.auto_download_enabled = config_service.get("update.auto_download", False)
        self.auto_install_enabled = config_service.get("update.auto_install", False)
        self.silent_mode = config_service.get("update.silent_mode", False)
        
        # State
        self.current_release_info = None
        self.is_checking = False
        self.is_downloading = False
        self.is_installing = False
        
        # Setup callbacks
        self.update_service.set_update_available_callback(self.on_update_available)
        
        # Start auto-check if enabled
        if self.auto_check_enabled:
            self.start_auto_check()
    
    def start_auto_check(self):
        """Start automatic update checking"""
        if not self.auto_check_enabled:
            return
        
        # Check immediately on startup (after a delay)
        QTimer.singleShot(30000, self.check_for_updates)  # 30 seconds delay
        
        # Setup periodic checking
        check_interval = self.config_service.get("update.check_interval", 24)  # hours
        self.check_timer.start(check_interval * 60 * 60 * 1000)  # Convert to milliseconds
    
    def stop_auto_check(self):
        """Stop automatic update checking"""
        self.check_timer.stop()
    
    def check_for_updates(self, force: bool = False):
        """Check for updates (async wrapper)"""
        if self.is_checking:
            return
        
        # Run async check in thread
        asyncio.create_task(self._async_check_for_updates(force))
    
    async def _async_check_for_updates(self, force: bool = False):
        """Async check for updates"""
        if self.is_checking:
            return
        
        self.is_checking = True
        
        try:
            release_info = await self.update_service.check_for_updates(force)
            
            if release_info:
                self.current_release_info = release_info
                self.update_available.emit(release_info)
                
                # Handle auto-download
                if self.auto_download_enabled:
                    await self._auto_download_update(release_info)
            
        except Exception as e:
            self.error_occurred.emit(f"检查更新失败: {str(e)}")
        
        finally:
            self.is_checking = False
    
    def on_update_available(self, release_info: ReleaseInfo):
        """Handle update available notification"""
        if self.silent_mode:
            return
        
        # Show notification dialog
        app = QApplication.instance()
        if app and app.activeWindow():
            # Import here to avoid circular import
            from app.ui.dialogs.update_dialog import UpdateNotificationDialog
            
            dialog = UpdateNotificationDialog(release_info, app.activeWindow())
            
            if dialog.exec() == UpdateNotificationDialog.Accepted:
                # User chose to update
                self.show_update_dialog(release_info)
    
    def show_update_dialog(self, release_info: ReleaseInfo):
        """Show full update dialog"""
        app = QApplication.instance()
        if app and app.activeWindow():
            # Import here to avoid circular import
            from app.ui.dialogs.update_dialog import UpdateDialog
            
            dialog = UpdateDialog(release_info, app.activeWindow())
            dialog.set_update_service(self.update_service)
            dialog.exec()
    
    async def _auto_download_update(self, release_info: ReleaseInfo):
        """Automatically download update"""
        if self.is_downloading:
            return
        
        self.is_downloading = True
        
        try:
            download_path = await self.update_service.download_update(release_info)
            self.update_downloaded.emit(str(download_path))
            
            # Handle auto-install
            if self.auto_install_enabled:
                await self._auto_install_update(download_path)
                
        except Exception as e:
            self.error_occurred.emit(f"自动下载失败: {str(e)}")
        
        finally:
            self.is_downloading = False
    
    async def _auto_install_update(self, download_path: Path):
        """Automatically install update"""
        if self.is_installing:
            return
        
        self.is_installing = True
        
        try:
            # Extract update
            extract_path = await self.update_service.extract_update(download_path)
            
            # Install update
            success = await self.update_service.install_update(extract_path, backup=True)
            
            self.update_installed.emit(success)
            
            if success:
                # Schedule restart
                self._schedule_restart()
                
        except Exception as e:
            self.error_occurred.emit(f"自动安装失败: {str(e)}")
        
        finally:
            self.is_installing = False
    
    def _schedule_restart(self):
        """Schedule application restart"""
        if self.silent_mode:
            # Restart immediately in silent mode
            self._restart_application()
        else:
            # Ask user for restart
            app = QApplication.instance()
            if app and app.activeWindow():
                reply = QMessageBox.question(
                    app.activeWindow(),
                    "更新完成",
                    "更新已安装完成，需要重启应用以使用新版本。\n现在重启吗？",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self._restart_application()
    
    def _restart_application(self):
        """Restart the application"""
        try:
            # Get current executable path
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                executable = sys.executable
            else:
                # Running as Python script
                executable = sys.executable
                args = [sys.argv[0]]
            
            # Start new instance
            if sys.platform == "win32":
                subprocess.Popen([executable] + sys.argv[1:])
            else:
                os.execv(executable, [executable] + sys.argv[1:])
            
            # Exit current instance
            QApplication.instance().quit()
            
        except Exception as e:
            self.error_occurred.emit(f"重启失败: {str(e)}")
    
    def get_settings(self) -> dict:
        """Get current auto-updater settings"""
        return {
            "auto_check": self.auto_check_enabled,
            "auto_download": self.auto_download_enabled,
            "auto_install": self.auto_install_enabled,
            "silent_mode": self.silent_mode,
            "check_interval": self.config_service.get("update.check_interval", 24)
        }
    
    def update_settings(self, settings: dict):
        """Update auto-updater settings"""
        if "auto_check" in settings:
            self.auto_check_enabled = settings["auto_check"]
            self.config_service.set("update.auto_check", self.auto_check_enabled)
            
            if self.auto_check_enabled:
                self.start_auto_check()
            else:
                self.stop_auto_check()
        
        if "auto_download" in settings:
            self.auto_download_enabled = settings["auto_download"]
            self.config_service.set("update.auto_download", self.auto_download_enabled)
        
        if "auto_install" in settings:
            self.auto_install_enabled = settings["auto_install"]
            self.config_service.set("update.auto_install", self.auto_install_enabled)
        
        if "silent_mode" in settings:
            self.silent_mode = settings["silent_mode"]
            self.config_service.set("update.silent_mode", self.silent_mode)
        
        if "check_interval" in settings:
            check_interval = settings["check_interval"]
            self.config_service.set("update.check_interval", check_interval)
            
            # Restart timer with new interval
            if self.auto_check_enabled:
                self.stop_auto_check()
                self.start_auto_check()
    
    def force_check_update(self):
        """Force check for updates"""
        self.check_for_updates(force=True)
    
    def get_current_version(self) -> str:
        """Get current application version"""
        return self.update_service.current_version
    
    def get_last_check_time(self) -> Optional[datetime]:
        """Get last update check time"""
        last_check = self.config_service.get("update.last_check")
        if last_check:
            return datetime.fromisoformat(last_check)
        return None
    
    def is_update_available(self) -> bool:
        """Check if update is currently available"""
        return self.current_release_info is not None
    
    def get_available_update(self) -> Optional[ReleaseInfo]:
        """Get currently available update info"""
        return self.current_release_info
    
    def clear_available_update(self):
        """Clear available update info"""
        self.current_release_info = None


class UpdateManager:
    """
    Singleton update manager for the entire application.
    """
    
    _instance = None
    
    def __new__(cls, config_service: ConfigService = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_service: ConfigService = None):
        if self._initialized:
            return
        
        if config_service is None:
            raise ValueError("ConfigService is required for first initialization")
        
        self.auto_updater = AutoUpdater(config_service)
        self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'UpdateManager':
        """Get singleton instance"""
        if cls._instance is None or not cls._instance._initialized:
            raise RuntimeError("UpdateManager not initialized")
        return cls._instance
    
    def get_updater(self) -> AutoUpdater:
        """Get auto-updater instance"""
        return self.auto_updater
    
    def check_for_updates(self, force: bool = False):
        """Check for updates"""
        self.auto_updater.check_for_updates(force)
    
    def show_update_dialog_if_available(self):
        """Show update dialog if update is available"""
        if self.auto_updater.is_update_available():
            release_info = self.auto_updater.get_available_update()
            self.auto_updater.show_update_dialog(release_info)
    
    def get_version_info(self) -> dict:
        """Get version information"""
        return {
            "current_version": self.auto_updater.get_current_version(),
            "last_check": self.auto_updater.get_last_check_time(),
            "update_available": self.auto_updater.is_update_available(),
            "available_version": self.auto_updater.get_available_update().version if self.auto_updater.is_update_available() else None
        }