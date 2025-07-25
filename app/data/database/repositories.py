"""
Repository classes for CRUD operations on data models.
"""
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from ..models.core import (
    DownloadTask, TaskStatus, VideoMetadata, CreatorProfile, 
    Platform, QualityOption, DownloadOptions
)
from .connection import DatabaseConnection


class BaseRepository(ABC):
    """Base repository class"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection


class DownloadHistoryRepository(BaseRepository):
    """Repository for download history operations"""
    
    def create(self, task: DownloadTask, metadata: Optional[VideoMetadata] = None) -> int:
        """Create download history record"""
        query = """
        INSERT INTO download_history (
            url, title, author, file_path, file_size, md5_hash,
            download_date, platform, video_id, channel_id, duration,
            view_count, quality, format, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Extract metadata if available
        title = metadata.title if metadata else None
        author = metadata.author if metadata else None
        platform = metadata.platform.value if metadata else None
        video_id = metadata.video_id if metadata else None
        channel_id = metadata.channel_id if metadata else None
        duration = metadata.duration if metadata else None
        view_count = metadata.view_count if metadata else None
        
        # Extract quality and format from options
        quality = task.options.quality_preference if task.options else None
        format_pref = task.options.format_preference if task.options else None
        
        params = (
            task.url, title, author, task.download_path, task.file_size,
            None,  # md5_hash - will be updated later
            task.completed_at or datetime.now(),
            platform, video_id, channel_id, duration, view_count,
            quality, format_pref, task.status.value
        )
        
        cursor = self.db.execute(query, params)
        return cursor.lastrowid
    
    def get_by_id(self, history_id: int) -> Optional[Dict[str, Any]]:
        """Get download history by ID"""
        query = "SELECT * FROM download_history WHERE id = ?"
        row = self.db.fetchone(query, (history_id,))
        return dict(row) if row else None
    
    def get_by_url(self, url: str) -> List[Dict[str, Any]]:
        """Get download history by URL"""
        query = "SELECT * FROM download_history WHERE url = ? ORDER BY download_date DESC"
        rows = self.db.fetchall(query, (url,))
        return [dict(row) for row in rows]
    
    def get_by_md5(self, md5_hash: str) -> Optional[Dict[str, Any]]:
        """Get download history by MD5 hash"""
        query = "SELECT * FROM download_history WHERE md5_hash = ?"
        row = self.db.fetchone(query, (md5_hash,))
        return dict(row) if row else None
    
    def search(self, keyword: str, platform: Optional[str] = None, 
               limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Search download history"""
        query = """
        SELECT * FROM download_history 
        WHERE (title LIKE ? OR author LIKE ? OR url LIKE ?)
        """
        params = [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
        
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        
        query += " ORDER BY download_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        rows = self.db.fetchall(query, tuple(params))
        return [dict(row) for row in rows]
    
    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent download history"""
        query = "SELECT * FROM download_history ORDER BY download_date DESC LIMIT ?"
        rows = self.db.fetchall(query, (limit,))
        return [dict(row) for row in rows]
    
    def get_by_platform(self, platform: str) -> List[Dict[str, Any]]:
        """Get download history by platform"""
        query = "SELECT * FROM download_history WHERE platform = ? ORDER BY download_date DESC"
        rows = self.db.fetchall(query, (platform,))
        return [dict(row) for row in rows]
    
    def update_md5(self, history_id: int, md5_hash: str) -> bool:
        """Update MD5 hash for download record"""
        query = "UPDATE download_history SET md5_hash = ?, updated_at = ? WHERE id = ?"
        cursor = self.db.execute(query, (md5_hash, datetime.now(), history_id))
        return cursor.rowcount > 0
    
    def delete(self, history_id: int) -> bool:
        """Delete download history record"""
        query = "DELETE FROM download_history WHERE id = ?"
        cursor = self.db.execute(query, (history_id,))
        return cursor.rowcount > 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get download statistics"""
        stats = {}
        
        # Total downloads
        row = self.db.fetchone("SELECT COUNT(*) as count FROM download_history")
        stats['total_downloads'] = row['count'] if row else 0
        
        # Downloads by platform
        rows = self.db.fetchall("""
            SELECT platform, COUNT(*) as count 
            FROM download_history 
            WHERE platform IS NOT NULL 
            GROUP BY platform
        """)
        stats['by_platform'] = {row['platform']: row['count'] for row in rows}
        
        # Total file size
        row = self.db.fetchone("SELECT SUM(file_size) as total_size FROM download_history")
        stats['total_size'] = row['total_size'] if row and row['total_size'] else 0
        
        return stats


class CreatorRepository(BaseRepository):
    """Repository for creator profile operations"""
    
    def create(self, creator: CreatorProfile) -> bool:
        """Create creator profile"""
        query = """
        INSERT INTO creators (
            id, name, platform, channel_url, avatar_url, description,
            subscriber_count, video_count, last_video_count, last_check,
            last_video_date, auto_download, priority, download_options, tags
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Serialize complex fields
        download_options_json = None
        if creator.download_options:
            download_options_json = json.dumps(creator.download_options.__dict__)
        
        tags_json = json.dumps(creator.tags) if creator.tags else None
        
        # Format datetime fields for SQLite
        last_check_str = creator.last_check.isoformat() if creator.last_check else None
        last_video_date_str = creator.last_video_date.isoformat() if creator.last_video_date else None
        
        params = (
            creator.id, creator.name, creator.platform.value, creator.channel_url,
            creator.avatar_url, creator.description, creator.subscriber_count,
            creator.video_count, creator.last_video_count, last_check_str,
            last_video_date_str, creator.auto_download, creator.priority,
            download_options_json, tags_json
        )
        
        try:
            self.db.execute(query, params)
            return True
        except Exception:
            return False
    
    def get_by_id(self, creator_id: str) -> Optional[CreatorProfile]:
        """Get creator by ID"""
        query = "SELECT * FROM creators WHERE id = ?"
        row = self.db.fetchone(query, (creator_id,))
        return self._row_to_creator(row) if row else None
    
    def get_by_url(self, channel_url: str) -> Optional[CreatorProfile]:
        """Get creator by channel URL"""
        query = "SELECT * FROM creators WHERE channel_url = ?"
        row = self.db.fetchone(query, (channel_url,))
        return self._row_to_creator(row) if row else None
    
    def get_all(self) -> List[CreatorProfile]:
        """Get all creators"""
        query = "SELECT * FROM creators ORDER BY priority DESC, name ASC"
        rows = self.db.fetchall(query)
        return [self._row_to_creator(row) for row in rows]
    
    def get_by_platform(self, platform: Platform) -> List[CreatorProfile]:
        """Get creators by platform"""
        query = "SELECT * FROM creators WHERE platform = ? ORDER BY priority DESC, name ASC"
        rows = self.db.fetchall(query, (platform.value,))
        return [self._row_to_creator(row) for row in rows]
    
    def get_auto_download_enabled(self) -> List[CreatorProfile]:
        """Get creators with auto-download enabled"""
        query = "SELECT * FROM creators WHERE auto_download = 1 ORDER BY priority DESC"
        rows = self.db.fetchall(query)
        return [self._row_to_creator(row) for row in rows]
    
    def get_needs_check(self, check_interval: int = 3600) -> List[CreatorProfile]:
        """Get creators that need checking for updates"""
        # Use datetime comparison instead of julianday to avoid timezone issues
        from datetime import datetime, timedelta
        cutoff_time = datetime.now() - timedelta(seconds=check_interval)
        cutoff_str = cutoff_time.isoformat()
        
        query = """
        SELECT * FROM creators 
        WHERE last_check IS NULL 
           OR last_check < ?
        ORDER BY priority DESC
        """
        
        rows = self.db.fetchall(query, (cutoff_str,))
        return [self._row_to_creator(row) for row in rows]
    
    def update(self, creator: CreatorProfile) -> bool:
        """Update creator profile"""
        query = """
        UPDATE creators SET
            name = ?, avatar_url = ?, description = ?, subscriber_count = ?,
            video_count = ?, last_video_count = ?, last_check = ?,
            last_video_date = ?, auto_download = ?, priority = ?,
            download_options = ?, tags = ?, updated_at = ?
        WHERE id = ?
        """
        
        # Serialize complex fields
        download_options_json = None
        if creator.download_options:
            download_options_json = json.dumps(creator.download_options.__dict__)
        
        tags_json = json.dumps(creator.tags) if creator.tags else None
        
        # Format datetime fields for SQLite
        last_check_str = creator.last_check.isoformat() if creator.last_check else None
        last_video_date_str = creator.last_video_date.isoformat() if creator.last_video_date else None
        
        params = (
            creator.name, creator.avatar_url, creator.description,
            creator.subscriber_count, creator.video_count, creator.last_video_count,
            last_check_str, last_video_date_str, creator.auto_download,
            creator.priority, download_options_json, tags_json, datetime.now().isoformat(),
            creator.id
        )
        
        cursor = self.db.execute(query, params)
        return cursor.rowcount > 0
    
    def update_last_check(self, creator_id: str, video_count: Optional[int] = None) -> bool:
        """Update last check timestamp and optionally video count"""
        now_str = datetime.now().isoformat()
        
        if video_count is not None:
            query = """
            UPDATE creators SET 
                last_check = ?, last_video_count = ?, updated_at = ? 
            WHERE id = ?
            """
            params = (now_str, video_count, now_str, creator_id)
        else:
            query = "UPDATE creators SET last_check = ?, updated_at = ? WHERE id = ?"
            params = (now_str, now_str, creator_id)
        
        cursor = self.db.execute(query, params)
        return cursor.rowcount > 0
    
    def delete(self, creator_id: str) -> bool:
        """Delete creator profile"""
        query = "DELETE FROM creators WHERE id = ?"
        cursor = self.db.execute(query, (creator_id,))
        return cursor.rowcount > 0
    
    def _row_to_creator(self, row) -> CreatorProfile:
        """Convert database row to CreatorProfile object"""
        # Deserialize complex fields
        download_options = None
        if row['download_options']:
            try:
                options_dict = json.loads(row['download_options'])
                download_options = DownloadOptions(**options_dict)
            except (json.JSONDecodeError, TypeError):
                pass
        
        tags = []
        if row['tags']:
            try:
                tags = json.loads(row['tags'])
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Parse datetime fields
        last_check = row['last_check']
        if isinstance(last_check, str):
            try:
                last_check = datetime.fromisoformat(last_check.replace(' ', 'T'))
            except ValueError:
                last_check = datetime.now()
        
        last_video_date = row['last_video_date']
        if isinstance(last_video_date, str):
            try:
                last_video_date = datetime.fromisoformat(last_video_date.replace(' ', 'T'))
            except ValueError:
                last_video_date = None
        
        return CreatorProfile(
            id=row['id'],
            name=row['name'],
            platform=Platform(row['platform']),
            channel_url=row['channel_url'],
            avatar_url=row['avatar_url'],
            last_check=last_check or datetime.now(),
            auto_download=bool(row['auto_download']),
            priority=row['priority'],
            description=row['description'],
            subscriber_count=row['subscriber_count'],
            video_count=row['video_count'],
            last_video_count=row['last_video_count'],
            last_video_date=last_video_date,
            download_options=download_options,
            tags=tags
        )


class SettingsRepository(BaseRepository):
    """Repository for application settings"""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value"""
        query = "SELECT value, value_type FROM settings WHERE key = ?"
        row = self.db.fetchone(query, (key,))
        
        if not row:
            return default
        
        value = row['value']
        value_type = row['value_type']
        
        # Convert value based on type
        if value_type == 'integer':
            return int(value)
        elif value_type == 'boolean':
            return value.lower() in ('true', '1', 'yes')
        elif value_type == 'json':
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return default
        else:  # string
            return value
    
    def set(self, key: str, value: Any, description: Optional[str] = None) -> bool:
        """Set setting value"""
        # Determine value type
        if isinstance(value, bool):
            value_type = 'boolean'
            value_str = str(value).lower()
        elif isinstance(value, int):
            value_type = 'integer'
            value_str = str(value)
        elif isinstance(value, (dict, list)):
            value_type = 'json'
            value_str = json.dumps(value)
        else:
            value_type = 'string'
            value_str = str(value)
        
        # Use INSERT OR REPLACE for upsert behavior
        query = """
        INSERT OR REPLACE INTO settings (key, value, value_type, description, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """
        
        params = (key, value_str, value_type, description, datetime.now())
        
        try:
            self.db.execute(query, params)
            return True
        except Exception:
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings"""
        query = "SELECT key, value, value_type FROM settings"
        rows = self.db.fetchall(query)
        
        settings = {}
        for row in rows:
            key = row['key']
            value = row['value']
            value_type = row['value_type']
            
            # Convert value based on type
            if value_type == 'integer':
                settings[key] = int(value)
            elif value_type == 'boolean':
                settings[key] = value.lower() in ('true', '1', 'yes')
            elif value_type == 'json':
                try:
                    settings[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    settings[key] = value
            else:  # string
                settings[key] = value
        
        return settings
    
    def delete(self, key: str) -> bool:
        """Delete setting"""
        query = "DELETE FROM settings WHERE key = ?"
        cursor = self.db.execute(query, (key,))
        return cursor.rowcount > 0
    
    def get_keys(self) -> List[str]:
        """Get all setting keys"""
        query = "SELECT key FROM settings ORDER BY key"
        rows = self.db.fetchall(query)
        return [row['key'] for row in rows]