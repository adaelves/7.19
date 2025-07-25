"""
Portable application configuration manager.
Handles portable storage of configuration files and user data.
"""

import os
import sys
import platform
from pathlib import Path
from typing import Optional, Dict, Any
import json
import shutil
import logging

logger = logging.getLogger(__name__)


class PortableManager:
    """Manages portable application configuration and data storage."""
    
    def __init__(self):
        self.is_portable = self._detect_portable_mode()
        self.app_dir = self._get_app_directory()
        self.data_dir = self._get_data_directory()
        self.config_dir = self._get_config_directory()
        self.cache_dir = self._get_cache_directory()
        self.logs_dir = self._get_logs_directory()
        
        # Create directories if they don't exist
        self._ensure_directories()
        
        logger.info(f"Portable mode: {self.is_portable}")
        logger.info(f"App directory: {self.app_dir}")
        logger.info(f"Data directory: {self.data_dir}")
    
    def _detect_portable_mode(self) -> bool:
        """Detect if the application is running in portable mode."""
        # Check for portable marker file
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            app_dir = Path(sys.executable).parent
        else:
            # Running as script
            app_dir = Path(__file__).parent.parent.parent
        
        portable_marker = app_dir / "portable.txt"
        portable_flag = app_dir / ".portable"
        
        # Check for portable markers
        if portable_marker.exists() or portable_flag.exists():
            return True
        
        # Check for portable directory structure
        portable_data_dir = app_dir / "Data"
        if portable_data_dir.exists():
            return True
        
        # Check environment variable
        if os.environ.get('VIDEODOWNLOADER_PORTABLE', '').lower() in ('1', 'true', 'yes'):
            return True
        
        # Default to portable mode for compiled executables
        return getattr(sys, 'frozen', False)
    
    def _get_app_directory(self) -> Path:
        """Get the application directory."""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return Path(sys.executable).parent
        else:
            # Running as script
            return Path(__file__).parent.parent.parent
    
    def _get_data_directory(self) -> Path:
        """Get the data directory for user files."""
        if self.is_portable:
            return self.app_dir / "Data"
        else:
            # Use system-appropriate user data directory
            if platform.system() == "Windows":
                base_dir = Path(os.environ.get('APPDATA', Path.home() / "AppData" / "Roaming"))
            elif platform.system() == "Darwin":
                base_dir = Path.home() / "Library" / "Application Support"
            else:  # Linux
                base_dir = Path(os.environ.get('XDG_DATA_HOME', Path.home() / ".local" / "share"))
            
            return base_dir / "VideoDownloader"
    
    def _get_config_directory(self) -> Path:
        """Get the configuration directory."""
        if self.is_portable:
            return self.data_dir / "Config"
        else:
            # Use system-appropriate config directory
            if platform.system() == "Windows":
                return self.data_dir / "Config"
            elif platform.system() == "Darwin":
                return Path.home() / "Library" / "Preferences" / "VideoDownloader"
            else:  # Linux
                base_dir = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / ".config"))
                return base_dir / "VideoDownloader"
    
    def _get_cache_directory(self) -> Path:
        """Get the cache directory."""
        if self.is_portable:
            return self.data_dir / "Cache"
        else:
            # Use system-appropriate cache directory
            if platform.system() == "Windows":
                base_dir = Path(os.environ.get('LOCALAPPDATA', Path.home() / "AppData" / "Local"))
            elif platform.system() == "Darwin":
                base_dir = Path.home() / "Library" / "Caches"
            else:  # Linux
                base_dir = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / ".cache"))
            
            return base_dir / "VideoDownloader"
    
    def _get_logs_directory(self) -> Path:
        """Get the logs directory."""
        if self.is_portable:
            return self.data_dir / "Logs"
        else:
            return self.data_dir / "Logs"
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.data_dir,
            self.config_dir,
            self.cache_dir,
            self.logs_dir,
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Ensured directory exists: {directory}")
            except Exception as e:
                logger.error(f"Failed to create directory {directory}: {e}")
    
    def get_config_file(self, filename: str) -> Path:
        """Get path to a configuration file."""
        return self.config_dir / filename
    
    def get_data_file(self, filename: str) -> Path:
        """Get path to a data file."""
        return self.data_dir / filename
    
    def get_cache_file(self, filename: str) -> Path:
        """Get path to a cache file."""
        return self.cache_dir / filename
    
    def get_log_file(self, filename: str) -> Path:
        """Get path to a log file."""
        return self.logs_dir / filename
    
    def get_database_path(self) -> Path:
        """Get path to the main database file."""
        return self.get_data_file("videodownloader.db")
    
    def get_downloads_directory(self) -> Path:
        """Get the default downloads directory."""
        if self.is_portable:
            return self.data_dir / "Downloads"
        else:
            # Use system downloads directory
            downloads_dir = Path.home() / "Downloads" / "VideoDownloader"
            downloads_dir.mkdir(parents=True, exist_ok=True)
            return downloads_dir
    
    def create_portable_structure(self) -> None:
        """Create portable directory structure."""
        if not self.is_portable:
            logger.warning("Not in portable mode, skipping portable structure creation")
            return
        
        # Create portable marker
        portable_marker = self.app_dir / "portable.txt"
        if not portable_marker.exists():
            portable_marker.write_text(
                "This file indicates that the application is running in portable mode.\n"
                "All user data and configuration will be stored in the Data folder.\n"
                f"Created by VideoDownloader v1.0.0\n",
                encoding='utf-8'
            )
        
        # Create directory structure
        directories = [
            "Data",
            "Data/Config",
            "Data/Cache", 
            "Data/Logs",
            "Data/Downloads",
            "Data/Plugins",
            "Data/Backups",
        ]
        
        for dir_name in directories:
            dir_path = self.app_dir / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create README files
        readme_content = {
            "Data/README.txt": (
                "VideoDownloader Portable Data Directory\n"
                "=====================================\n\n"
                "This directory contains all user data for the portable version:\n\n"
                "- Config/: Application configuration files\n"
                "- Cache/: Temporary cache files\n"
                "- Logs/: Application log files\n"
                "- Downloads/: Default download location\n"
                "- Plugins/: User-installed plugins\n"
                "- Backups/: Configuration and data backups\n\n"
                "You can safely move this entire folder to backup your data.\n"
            ),
            "Data/Config/README.txt": (
                "Configuration Files\n"
                "==================\n\n"
                "This directory contains application configuration files:\n\n"
                "- settings.json: Main application settings\n"
                "- plugins.json: Plugin configuration\n"
                "- themes.json: UI theme settings\n"
                "- shortcuts.json: Keyboard shortcuts\n"
            ),
        }
        
        for file_path, content in readme_content.items():
            full_path = self.app_dir / file_path
            if not full_path.exists():
                full_path.write_text(content, encoding='utf-8')
        
        logger.info("Portable directory structure created")
    
    def migrate_from_installed(self, installed_data_dir: Optional[Path] = None) -> bool:
        """Migrate data from installed version to portable version."""
        if not self.is_portable:
            return False
        
        if installed_data_dir is None:
            # Try to find installed version data
            if platform.system() == "Windows":
                installed_data_dir = Path(os.environ.get('APPDATA', '')) / "VideoDownloader"
            elif platform.system() == "Darwin":
                installed_data_dir = Path.home() / "Library" / "Application Support" / "VideoDownloader"
            else:  # Linux
                installed_data_dir = Path.home() / ".local" / "share" / "VideoDownloader"
        
        if not installed_data_dir or not installed_data_dir.exists():
            logger.info("No installed version data found to migrate")
            return False
        
        try:
            # Copy configuration files
            config_files = ["settings.json", "plugins.json", "themes.json"]
            for config_file in config_files:
                src = installed_data_dir / config_file
                dst = self.get_config_file(config_file)
                if src.exists() and not dst.exists():
                    shutil.copy2(src, dst)
                    logger.info(f"Migrated config file: {config_file}")
            
            # Copy database
            src_db = installed_data_dir / "videodownloader.db"
            dst_db = self.get_database_path()
            if src_db.exists() and not dst_db.exists():
                shutil.copy2(src_db, dst_db)
                logger.info("Migrated database")
            
            logger.info(f"Migration completed from {installed_data_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    def export_portable_package(self, output_path: Path) -> bool:
        """Export current configuration as a portable package."""
        try:
            # Create temporary directory for package
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                package_dir = temp_path / "VideoDownloader_Portable"
                
                # Copy application files
                if getattr(sys, 'frozen', False):
                    # Copy executable and dependencies
                    app_files = list(self.app_dir.glob("*"))
                    for file_path in app_files:
                        if file_path.name != "Data":  # Skip existing data
                            if file_path.is_file():
                                shutil.copy2(file_path, package_dir / file_path.name)
                            elif file_path.is_dir():
                                shutil.copytree(file_path, package_dir / file_path.name)
                
                # Copy current data (if any)
                if self.data_dir.exists():
                    shutil.copytree(self.data_dir, package_dir / "Data")
                
                # Create portable marker
                (package_dir / "portable.txt").write_text(
                    "Portable VideoDownloader Package\n"
                    "Run VideoDownloader.exe to start the application.\n",
                    encoding='utf-8'
                )
                
                # Create archive
                shutil.make_archive(str(output_path.with_suffix('')), 'zip', temp_path)
                
            logger.info(f"Portable package exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export portable package: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """Get portable manager information."""
        return {
            'is_portable': self.is_portable,
            'app_directory': str(self.app_dir),
            'data_directory': str(self.data_dir),
            'config_directory': str(self.config_dir),
            'cache_directory': str(self.cache_dir),
            'logs_directory': str(self.logs_dir),
            'database_path': str(self.get_database_path()),
            'downloads_directory': str(self.get_downloads_directory()),
        }


# Global portable manager instance
_portable_manager = None

def get_portable_manager() -> PortableManager:
    """Get the global portable manager instance."""
    global _portable_manager
    if _portable_manager is None:
        _portable_manager = PortableManager()
    return _portable_manager

def is_portable() -> bool:
    """Check if the application is running in portable mode."""
    return get_portable_manager().is_portable

def get_data_dir() -> Path:
    """Get the data directory."""
    return get_portable_manager().data_dir

def get_config_dir() -> Path:
    """Get the configuration directory."""
    return get_portable_manager().config_dir

def get_cache_dir() -> Path:
    """Get the cache directory."""
    return get_portable_manager().cache_dir

def get_logs_dir() -> Path:
    """Get the logs directory."""
    return get_portable_manager().logs_dir