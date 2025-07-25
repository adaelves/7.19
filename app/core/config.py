"""
Application configuration management.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field

try:
    from .portable import get_portable_manager
except ImportError:
    # Fallback if portable module is not available
    def get_portable_manager():
        class FallbackPortableManager:
            def __init__(self):
                self.is_portable = False
                self.data_dir = Path.home() / ".video_downloader"
                self.config_dir = self.data_dir
                self.cache_dir = self.data_dir / "cache"
                self.logs_dir = self.data_dir / "logs"
            
            def get_config_file(self, filename):
                return self.config_dir / filename
            
            def get_data_file(self, filename):
                return self.data_dir / filename
            
            def get_downloads_directory(self):
                return Path.home() / "Downloads" / "VideoDownloader"
            
            def get_database_path(self):
                return self.data_dir / "videodownloader.db"
        
        return FallbackPortableManager()


@dataclass
class AppConfig:
    """Application configuration"""
    # Application info
    app_name: str = "Multi-platform Video Downloader"
    app_version: str = "1.0.0"
    
    # Paths
    download_path: str = str(Path.home() / "Downloads" / "VideoDownloader")
    config_path: str = str(Path.home() / ".video_downloader")
    plugin_path: str = "app/plugins"
    
    # Download settings
    max_concurrent_downloads: int = 3
    default_quality: str = "best"
    default_format: str = "mp4"
    enable_resume: bool = True
    
    # UI settings
    theme: str = "light"  # light, dark
    window_width: int = 1200
    window_height: int = 800
    
    # Network settings
    connection_timeout: int = 30
    read_timeout: int = 60
    max_retries: int = 3
    
    # Creator monitoring
    check_interval: int = 3600  # seconds
    auto_download_new: bool = False
    
    # Advanced features
    hardware_acceleration_enabled: bool = False
    hardware_acceleration_gpu_type: str = "auto"
    hardware_acceleration_encoder: str = "auto"
    hardware_acceleration_quality: str = "medium"
    optimal_download_hours: List[int] = field(default_factory=lambda: list(range(2, 8)))
    max_bandwidth_usage: float = 0.8
    post_download_action: str = "none"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """Create from dictionary"""
        return cls(**data)


class ConfigManager:
    """Configuration manager for the application"""
    
    def __init__(self, config_file: Optional[str] = None):
        # Use portable manager for path resolution
        self.portable_manager = get_portable_manager()
        
        if config_file:
            self.config_file = config_file
        else:
            self.config_file = str(self.portable_manager.get_config_file("settings.json"))
        
        self.config = AppConfig()
        self._update_config_paths()
        self._ensure_config_dir()
        self.load()
    
    def _update_config_paths(self):
        """Update configuration paths based on portable mode"""
        # Update default paths to use portable manager
        self.config.download_path = str(self.portable_manager.get_downloads_directory())
        self.config.config_path = str(self.portable_manager.config_dir)
    
    def _ensure_config_dir(self):
        """Ensure configuration directory exists"""
        config_dir = Path(self.config_file).parent
        config_dir.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> None:
        """Load configuration from file"""
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Filter out unknown keys to avoid errors
                    valid_keys = {field.name for field in AppConfig.__dataclass_fields__.values()}
                    filtered_data = {k: v for k, v in data.items() if k in valid_keys}
                    self.config = AppConfig(**filtered_data)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            # Use default configuration
            self.config = AppConfig()
    
    def save(self) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error: Could not save config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return getattr(self.config, key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        if hasattr(self.config, key):
            setattr(self.config, key, value)
            self.save()
        else:
            raise KeyError(f"Unknown configuration key: {key}")
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        self.config = AppConfig()
        self.save()


# Global configuration instance
config_manager = ConfigManager()