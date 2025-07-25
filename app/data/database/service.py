"""
Database service that provides high-level database operations.
"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from .connection import DatabaseManager
from .repositories import (
    DownloadHistoryRepository, 
    CreatorRepository, 
    SettingsRepository
)
from ..models.core import DownloadTask, CreatorProfile, VideoMetadata


class DatabaseService:
    """High-level database service"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default database path
            config_dir = Path.home() / ".video_downloader"
            config_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(config_dir / "database.db")
        
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.initialize()
        
        # Initialize repositories
        self.download_history = DownloadHistoryRepository(self.db_manager.get_connection())
        self.creators = CreatorRepository(self.db_manager.get_connection())
        self.settings = SettingsRepository(self.db_manager.get_connection())
    
    # Download History Methods
    def add_download_record(self, task: DownloadTask, metadata: Optional[VideoMetadata] = None) -> int:
        """Add download record to history"""
        return self.download_history.create(task, metadata)
    
    def get_download_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent download history"""
        return self.download_history.get_recent(limit)
    
    def search_downloads(self, keyword: str, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search download history"""
        return self.download_history.search(keyword, platform)
    
    def get_downloads_by_url(self, url: str) -> List[Dict[str, Any]]:
        """Get downloads by URL"""
        return self.download_history.get_by_url(url)
    
    def check_duplicate_by_md5(self, md5_hash: str) -> Optional[Dict[str, Any]]:
        """Check for duplicate download by MD5 hash"""
        return self.download_history.get_by_md5(md5_hash)
    
    def update_download_md5(self, history_id: int, md5_hash: str) -> bool:
        """Update MD5 hash for download record"""
        return self.download_history.update_md5(history_id, md5_hash)
    
    def get_download_statistics(self) -> Dict[str, Any]:
        """Get download statistics"""
        return self.download_history.get_statistics()
    
    def delete_download_record(self, history_id: int) -> bool:
        """Delete download record"""
        return self.download_history.delete(history_id)
    
    # Creator Management Methods
    def add_creator(self, creator: CreatorProfile) -> bool:
        """Add creator for monitoring"""
        return self.creators.create(creator)
    
    def get_creator_by_id(self, creator_id: str) -> Optional[CreatorProfile]:
        """Get creator by ID"""
        return self.creators.get_by_id(creator_id)
    
    def get_creator_by_url(self, channel_url: str) -> Optional[CreatorProfile]:
        """Get creator by channel URL"""
        return self.creators.get_by_url(channel_url)
    
    def get_all_creators(self) -> List[CreatorProfile]:
        """Get all creators"""
        return self.creators.get_all()
    
    def get_creators_for_auto_download(self) -> List[CreatorProfile]:
        """Get creators with auto-download enabled"""
        return self.creators.get_auto_download_enabled()
    
    def get_creators_needing_check(self, check_interval: int = 3600) -> List[CreatorProfile]:
        """Get creators that need checking for updates"""
        return self.creators.get_needs_check(check_interval)
    
    def update_creator(self, creator: CreatorProfile) -> bool:
        """Update creator profile"""
        return self.creators.update(creator)
    
    def update_creator_check(self, creator_id: str, video_count: Optional[int] = None) -> bool:
        """Update creator last check timestamp"""
        return self.creators.update_last_check(creator_id, video_count)
    
    def delete_creator(self, creator_id: str) -> bool:
        """Delete creator"""
        return self.creators.delete(creator_id)
    
    # Settings Methods
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get application setting"""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any, description: Optional[str] = None) -> bool:
        """Set application setting"""
        return self.settings.set(key, value, description)
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings"""
        return self.settings.get_all()
    
    def delete_setting(self, key: str) -> bool:
        """Delete setting"""
        return self.settings.delete(key)
    
    def get_setting_keys(self) -> List[str]:
        """Get all setting keys"""
        return self.settings.get_keys()
    
    # Utility Methods
    def backup_database(self, backup_path: str) -> bool:
        """Create database backup"""
        try:
            import shutil
            # Ensure all data is written to disk before backup
            self.db_manager.connection.execute("PRAGMA wal_checkpoint(FULL)")
            shutil.copy2(self.db_manager.db_path, backup_path)
            return True
        except Exception:
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            import shutil
            self.close()
            shutil.copy2(backup_path, self.db_manager.db_path)
            # Reinitialize after restore
            self.__init__(str(self.db_manager.db_path))
            return True
        except Exception:
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information"""
        db_path = Path(self.db_manager.db_path)
        
        info = {
            'path': str(db_path),
            'exists': db_path.exists(),
            'size': db_path.stat().st_size if db_path.exists() else 0,
            'version': self.db_manager.current_version,
            'target_version': self.db_manager.target_version
        }
        
        return info
    
    def vacuum_database(self) -> bool:
        """Vacuum database to reclaim space"""
        try:
            self.db_manager.connection.execute("VACUUM")
            return True
        except Exception:
            return False
    
    def close(self):
        """Close database connection"""
        self.db_manager.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Global database service instance
_db_service: Optional[DatabaseService] = None


def get_database_service(db_path: Optional[str] = None) -> DatabaseService:
    """Get global database service instance"""
    global _db_service
    
    if _db_service is None:
        _db_service = DatabaseService(db_path)
    
    return _db_service


def close_database_service():
    """Close global database service"""
    global _db_service
    
    if _db_service is not None:
        _db_service.close()
        _db_service = None