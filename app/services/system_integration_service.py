"""
System Integration Service - 系统集成服务
提供托盘图标、老板键、系统通知、开机启动等功能
"""
import os
import sys
import winreg
from pathlib import Path
from typing import Optional, Callable
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtCore import QObject, Signal, QTimer, QSettings
from PySide6.QtGui import QIcon, QPixmap, QKeySequence, QShortcut, QAction, QColor


class SystemIntegrationService(QObject):
    """System integration service for tray, hotkeys, notifications, etc."""
    
    # Signals
    show_window_requested = Signal()
    hide_window_requested = Signal()
    quit_requested = Signal()
    notification_clicked = Signal(str)
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.tray_icon: Optional[QSystemTrayIcon] = None
        self.boss_key_shortcut: Optional[QShortcut] = None
        self.settings = QSettings("VideoDownloader", "SystemIntegration")
        
        # Initialize components
        self.setup_tray_icon()
        self.setup_boss_key()
        
    def setup_tray_icon(self):
        """Setup system tray icon with context menu"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("System tray is not available on this system")
            return
            
        # Create tray icon
        self.tray_icon = QSystemTrayIcon()
        
        # Set icon (use a default icon for now)
        icon = self.create_default_icon()
        self.tray_icon.setIcon(icon)
        
        # Create context menu
        tray_menu = QMenu()
        
        # Show/Hide action
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show_window_requested.emit)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("隐藏到托盘", self)
        hide_action.triggered.connect(self.hide_window_requested.emit)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        # Quick actions
        add_download_action = QAction("添加下载", self)
        add_download_action.triggered.connect(self.show_add_download_dialog)
        tray_menu.addAction(add_download_action)
        
        pause_all_action = QAction("暂停所有下载", self)
        pause_all_action.triggered.connect(self.pause_all_downloads)
        tray_menu.addAction(pause_all_action)
        
        tray_menu.addSeparator()
        
        # Settings
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.show_settings)
        tray_menu.addAction(settings_action)
        
        # Quit
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_requested.emit)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # Connect double-click to show window
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        # Set tooltip
        self.tray_icon.setToolTip("多平台视频下载器")
        
    def setup_boss_key(self):
        """Setup boss key (quick hide) functionality"""
        if not self.main_window:
            return
            
        # Default boss key: Ctrl+Shift+H
        boss_key_sequence = self.settings.value("boss_key", "Ctrl+Shift+H")
        
        self.boss_key_shortcut = QShortcut(QKeySequence(boss_key_sequence), self.main_window)
        self.boss_key_shortcut.activated.connect(self.toggle_window_visibility)
        
    def create_default_icon(self) -> QIcon:
        """Create a default tray icon"""
        # Create a simple colored square as default icon
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(0, 120, 215))  # Blue color
        return QIcon(pixmap)
        
    def show_tray_icon(self):
        """Show the system tray icon"""
        if self.tray_icon:
            self.tray_icon.show()
            
    def hide_tray_icon(self):
        """Hide the system tray icon"""
        if self.tray_icon:
            self.tray_icon.hide()
            
    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window_requested.emit()
        elif reason == QSystemTrayIcon.Trigger:
            # Single click - could show a quick menu or status
            pass
            
    def toggle_window_visibility(self):
        """Toggle main window visibility (boss key function)"""
        if not self.main_window:
            return
            
        if self.main_window.isVisible() and not self.main_window.isMinimized():
            self.hide_window_requested.emit()
        else:
            self.show_window_requested.emit()
            
    def show_notification(self, title: str, message: str, duration: int = 3000):
        """Show system notification"""
        if self.tray_icon and QSystemTrayIcon.supportsMessages():
            self.tray_icon.showMessage(
                title, 
                message, 
                QSystemTrayIcon.Information, 
                duration
            )
            
    def show_download_complete_notification(self, filename: str):
        """Show notification when download completes"""
        self.show_notification(
            "下载完成",
            f"文件 {filename} 下载完成",
            5000
        )
        
    def show_download_failed_notification(self, filename: str, error: str):
        """Show notification when download fails"""
        self.show_notification(
            "下载失败",
            f"文件 {filename} 下载失败: {error}",
            5000
        )
        
    def set_boss_key(self, key_sequence: str):
        """Set new boss key sequence"""
        if self.boss_key_shortcut:
            self.boss_key_shortcut.setKey(QKeySequence(key_sequence))
            self.settings.setValue("boss_key", key_sequence)
            
    def get_boss_key(self) -> str:
        """Get current boss key sequence"""
        key = self.settings.value("boss_key", "Ctrl+Shift+H", type=str)
        return key if key else "Ctrl+Shift+H"
        
    def enable_startup(self, enable: bool = True):
        """Enable or disable application startup with Windows"""
        try:
            app_name = "VideoDownloader"
            app_path = sys.executable
            
            # Open Windows registry key for startup programs
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            if enable:
                # Add to startup
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
                self.settings.setValue("startup_enabled", True)
            else:
                # Remove from startup
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass  # Key doesn't exist, which is fine
                self.settings.setValue("startup_enabled", False)
                
            winreg.CloseKey(key)
            return True
            
        except Exception as e:
            print(f"Failed to modify startup settings: {e}")
            return False
            
    def is_startup_enabled(self) -> bool:
        """Check if startup is enabled"""
        return self.settings.value("startup_enabled", False, type=bool)
        
    def register_protocol_handler(self, protocol: str = "videodownloader"):
        """Register custom protocol handler for URL schemes"""
        try:
            app_path = sys.executable
            
            # Create registry entries for custom protocol
            protocol_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{protocol}")
            winreg.SetValueEx(protocol_key, "", 0, winreg.REG_SZ, f"URL:{protocol} Protocol")
            winreg.SetValueEx(protocol_key, "URL Protocol", 0, winreg.REG_SZ, "")
            
            # Set default icon
            icon_key = winreg.CreateKey(protocol_key, "DefaultIcon")
            winreg.SetValueEx(icon_key, "", 0, winreg.REG_SZ, f"{app_path},0")
            
            # Set command to execute
            command_key = winreg.CreateKey(protocol_key, "shell\\open\\command")
            winreg.SetValueEx(command_key, "", 0, winreg.REG_SZ, f'"{app_path}" "%1"')
            
            # Close keys
            winreg.CloseKey(command_key)
            winreg.CloseKey(icon_key)
            winreg.CloseKey(protocol_key)
            
            self.settings.setValue("protocol_registered", True)
            return True
            
        except Exception as e:
            print(f"Failed to register protocol handler: {e}")
            return False
            
    def register_file_associations(self, extensions: list = None):
        """Register file associations for supported video formats"""
        if extensions is None:
            extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
            
        try:
            app_path = sys.executable
            app_name = "VideoDownloader"
            
            for ext in extensions:
                # Create file type key
                file_type_key = winreg.CreateKey(
                    winreg.HKEY_CURRENT_USER, 
                    f"Software\\Classes\\{app_name}{ext}"
                )
                winreg.SetValueEx(file_type_key, "", 0, winreg.REG_SZ, f"{app_name} Video File")
                
                # Set default icon
                icon_key = winreg.CreateKey(file_type_key, "DefaultIcon")
                winreg.SetValueEx(icon_key, "", 0, winreg.REG_SZ, f"{app_path},0")
                
                # Set open command
                command_key = winreg.CreateKey(file_type_key, "shell\\open\\command")
                winreg.SetValueEx(command_key, "", 0, winreg.REG_SZ, f'"{app_path}" "%1"')
                
                # Associate extension with file type
                ext_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{ext}")
                winreg.SetValueEx(ext_key, "", 0, winreg.REG_SZ, f"{app_name}{ext}")
                
                # Close keys
                winreg.CloseKey(command_key)
                winreg.CloseKey(icon_key)
                winreg.CloseKey(file_type_key)
                winreg.CloseKey(ext_key)
                
            self.settings.setValue("file_associations_registered", True)
            return True
            
        except Exception as e:
            print(f"Failed to register file associations: {e}")
            return False
            
    def update_tray_tooltip(self, message: str):
        """Update tray icon tooltip"""
        if self.tray_icon:
            self.tray_icon.setToolTip(message)
            
    def update_tray_icon_with_progress(self, progress: int):
        """Update tray icon to show download progress"""
        if not self.tray_icon:
            return
            
        # Create icon with progress indicator
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(0, 120, 215))
        
        # Add progress bar overlay (simplified)
        if 0 <= progress <= 100:
            # This is a simplified version - in a real implementation,
            # you might want to draw a proper progress indicator
            color = QColor(0, 255, 0) if progress == 100 else QColor(255, 255, 0)
            # Draw progress indicator (simplified)
            
        self.tray_icon.setIcon(QIcon(pixmap))
        
    # Slot methods for tray menu actions
    def show_add_download_dialog(self):
        """Show add download dialog from tray"""
        self.show_window_requested.emit()
        # Additional logic to show add download dialog
        
    def pause_all_downloads(self):
        """Pause all downloads from tray"""
        # This would connect to the download service
        pass
        
    def show_settings(self):
        """Show settings dialog from tray"""
        self.show_window_requested.emit()
        # Additional logic to show settings
        
    def cleanup(self):
        """Cleanup resources"""
        if self.tray_icon:
            self.tray_icon.hide()
        if self.boss_key_shortcut:
            self.boss_key_shortcut.setEnabled(False)