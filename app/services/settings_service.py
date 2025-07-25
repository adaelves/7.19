"""
Settings service for managing application configuration
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from PySide6.QtCore import QObject, Signal

from app.core.portable import get_portable_manager


@dataclass
class DownloadSettings:
    """Download settings"""
    download_path: str = ""
    quality: str = "best"  # best, worst, 720p, 1080p, etc.
    format: str = "mp4"
    max_concurrent: int = 3
    rate_limit: Optional[int] = None  # KB/s
    enable_resume: bool = True
    auto_retry: bool = True
    max_retries: int = 3
    # FFmpeg已集成在yt-dlp中，用于视频处理和格式转换
    filename_template: str = "%(title)s.%(ext)s"  # 文件命名格式
    
    
@dataclass 
class NetworkSettings:
    """Network settings"""
    proxy_enabled: bool = False
    proxy_type: str = "http"  # http, socks5
    proxy_host: str = ""
    proxy_port: int = 8080
    proxy_username: str = ""
    proxy_password: str = ""
    timeout: int = 30
    user_agent: str = ""
    

@dataclass
class UISettings:
    """UI settings"""
    theme: str = "auto"  # light, dark, auto
    language: str = "zh_CN"
    window_width: int = 1200
    window_height: int = 800
    window_x: int = -1
    window_y: int = -1
    show_tray_icon: bool = True
    minimize_to_tray: bool = True
    close_to_tray: bool = False
    

@dataclass
class CreatorSettings:
    """Creator monitoring settings"""
    check_interval: int = 3600  # seconds
    auto_download: bool = False
    notification_enabled: bool = True
    max_videos_per_creator: int = 50
    

@dataclass
class AppSettings:
    """Main application settings"""
    download: DownloadSettings
    network: NetworkSettings
    ui: UISettings
    creator: CreatorSettings
    
    def __init__(self):
        self.download = DownloadSettings()
        self.network = NetworkSettings()
        self.ui = UISettings()
        self.creator = CreatorSettings()


class SettingsService(QObject):
    """Settings service"""
    
    settings_changed = Signal(str, object)  # section, value
    
    def __init__(self):
        super().__init__()
        self.portable_manager = get_portable_manager()
        self.settings_file = self.portable_manager.get_config_file("settings.json")
        self.settings = AppSettings()
        self._load_settings()
        self._update_default_paths()
        
    def _update_default_paths(self):
        """Update default paths based on portable mode"""
        if not self.settings.download.download_path:
            self.settings.download.download_path = str(
                self.portable_manager.get_downloads_directory()
            )
    
    def _load_settings(self):
        """Load settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._deserialize_settings(data)
        except Exception as e:
            print(f"Failed to load settings: {e}")
            # Use default settings
            
    def _deserialize_settings(self, data: Dict[str, Any]):
        """Deserialize settings from dict"""
        if 'download' in data:
            download_data = data['download']
            self.settings.download = DownloadSettings(**download_data)
            
        if 'network' in data:
            network_data = data['network']
            self.settings.network = NetworkSettings(**network_data)
            
        if 'ui' in data:
            ui_data = data['ui']
            self.settings.ui = UISettings(**ui_data)
            
        if 'creator' in data:
            creator_data = data['creator']
            self.settings.creator = CreatorSettings(**creator_data)
    
    def save_settings(self):
        """Save settings to file"""
        try:
            # Ensure config directory exists
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'download': asdict(self.settings.download),
                'network': asdict(self.settings.network),
                'ui': asdict(self.settings.ui),
                'creator': asdict(self.settings.creator),
            }
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Failed to save settings: {e}")
    
    def get_download_settings(self) -> DownloadSettings:
        """Get download settings"""
        return self.settings.download
    
    def update_download_settings(self, **kwargs):
        """Update download settings"""
        for key, value in kwargs.items():
            if hasattr(self.settings.download, key):
                setattr(self.settings.download, key, value)
        
        self.save_settings()
        self.settings_changed.emit('download', self.settings.download)
    
    def get_network_settings(self) -> NetworkSettings:
        """Get network settings"""
        return self.settings.network
    
    def update_network_settings(self, **kwargs):
        """Update network settings"""
        for key, value in kwargs.items():
            if hasattr(self.settings.network, key):
                setattr(self.settings.network, key, value)
        
        self.save_settings()
        self.settings_changed.emit('network', self.settings.network)
    
    def get_ui_settings(self) -> UISettings:
        """Get UI settings"""
        return self.settings.ui
    
    def update_ui_settings(self, **kwargs):
        """Update UI settings"""
        for key, value in kwargs.items():
            if hasattr(self.settings.ui, key):
                setattr(self.settings.ui, key, value)
        
        self.save_settings()
        self.settings_changed.emit('ui', self.settings.ui)
    
    def get_creator_settings(self) -> CreatorSettings:
        """Get creator monitoring settings"""
        return self.settings.creator
    
    def update_creator_settings(self, **kwargs):
        """Update creator monitoring settings"""
        for key, value in kwargs.items():
            if hasattr(self.settings.creator, key):
                setattr(self.settings.creator, key, value)
        
        self.save_settings()
        self.settings_changed.emit('creator', self.settings.creator)
    
    def get_proxy_dict(self) -> Optional[str]:
        """Get proxy configuration as string for yt-dlp"""
        network = self.settings.network
        if not network.proxy_enabled or not network.proxy_host:
            return None
            
        proxy_url = f"{network.proxy_type}://"
        
        if network.proxy_username and network.proxy_password:
            proxy_url += f"{network.proxy_username}:{network.proxy_password}@"
            
        proxy_url += f"{network.proxy_host}:{network.proxy_port}"
        
        return proxy_url
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.settings = AppSettings()
        self._update_default_paths()
        self.save_settings()
        
        # Emit signals for all sections
        self.settings_changed.emit('download', self.settings.download)
        self.settings_changed.emit('network', self.settings.network)
        self.settings_changed.emit('ui', self.settings.ui)
        self.settings_changed.emit('creator', self.settings.creator)
    
    def export_settings(self, filepath: str) -> bool:
        """Export settings to file"""
        try:
            data = {
                'download': asdict(self.settings.download),
                'network': asdict(self.settings.network),
                'ui': asdict(self.settings.ui),
                'creator': asdict(self.settings.creator),
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            return True
        except Exception as e:
            print(f"Failed to export settings: {e}")
            return False
    
    def import_settings(self, filepath: str) -> bool:
        """Import settings from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self._deserialize_settings(data)
            self.save_settings()
            
            # Emit signals for all sections
            self.settings_changed.emit('download', self.settings.download)
            self.settings_changed.emit('network', self.settings.network)
            self.settings_changed.emit('ui', self.settings.ui)
            self.settings_changed.emit('creator', self.settings.creator)
            
            return True
        except Exception as e:
            print(f"Failed to import settings: {e}")
            return False