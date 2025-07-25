"""
SQLite database connection and management.
"""
import sqlite3
import threading
from pathlib import Path
from typing import Optional, Any, Dict, List, Tuple
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Thread-safe SQLite database connection manager"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._local = threading.local()
        self._lock = threading.Lock()
        self._ensure_db_directory()
    
    def _ensure_db_directory(self):
        """Ensure database directory exists"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0
            )
            # Enable foreign key constraints
            self._local.connection.execute("PRAGMA foreign_keys = ON")
            # Set WAL mode for better concurrency
            self._local.connection.execute("PRAGMA journal_mode = WAL")
            # Row factory for dict-like access
            self._local.connection.row_factory = sqlite3.Row
        
        return self._local.connection
    
    @contextmanager
    def get_cursor(self, commit: bool = True):
        """Context manager for database cursor"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()
    
    def execute(self, query: str, params: Optional[Tuple] = None) -> sqlite3.Cursor:
        """Execute a single query"""
        with self.get_cursor() as cursor:
            if params:
                return cursor.execute(query, params)
            else:
                return cursor.execute(query)
    
    def executemany(self, query: str, params_list: List[Tuple]) -> sqlite3.Cursor:
        """Execute query with multiple parameter sets"""
        with self.get_cursor() as cursor:
            return cursor.executemany(query, params_list)
    
    def fetchone(self, query: str, params: Optional[Tuple] = None) -> Optional[sqlite3.Row]:
        """Fetch single row"""
        with self.get_cursor(commit=False) as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()
    
    def fetchall(self, query: str, params: Optional[Tuple] = None) -> List[sqlite3.Row]:
        """Fetch all rows"""
        with self.get_cursor(commit=False) as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def close(self):
        """Close database connection"""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            delattr(self._local, 'connection')
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class DatabaseManager:
    """Database manager with connection pooling and migration support"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = DatabaseConnection(db_path)
        self.current_version = 0
        self.target_version = 1
        
    def initialize(self):
        """Initialize database with tables and migrations"""
        self._create_version_table()
        self.current_version = self._get_current_version()
        
        if self.current_version < self.target_version:
            self._run_migrations()
    
    def _create_version_table(self):
        """Create database version tracking table"""
        query = """
        CREATE TABLE IF NOT EXISTS db_version (
            version INTEGER PRIMARY KEY,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.connection.execute(query)
    
    def _get_current_version(self) -> int:
        """Get current database version"""
        row = self.connection.fetchone("SELECT MAX(version) as version FROM db_version")
        return row['version'] if row and row['version'] is not None else 0
    
    def _set_version(self, version: int):
        """Set database version"""
        self.connection.execute(
            "INSERT INTO db_version (version) VALUES (?)",
            (version,)
        )
        self.current_version = version
    
    def _run_migrations(self):
        """Run database migrations"""
        logger.info(f"Running migrations from version {self.current_version} to {self.target_version}")
        
        for version in range(self.current_version + 1, self.target_version + 1):
            migration_method = getattr(self, f'_migrate_to_v{version}', None)
            if migration_method:
                logger.info(f"Applying migration to version {version}")
                migration_method()
                self._set_version(version)
            else:
                logger.warning(f"No migration method found for version {version}")
    
    def _migrate_to_v1(self):
        """Migration to version 1: Create initial tables"""
        # Download history table
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS download_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                author TEXT,
                file_path TEXT,
                file_size INTEGER,
                md5_hash TEXT,
                download_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                platform TEXT,
                video_id TEXT,
                channel_id TEXT,
                duration INTEGER,
                view_count INTEGER,
                quality TEXT,
                format TEXT,
                status TEXT DEFAULT 'completed',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Creators monitoring table
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS creators (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                platform TEXT NOT NULL,
                channel_url TEXT UNIQUE NOT NULL,
                avatar_url TEXT,
                description TEXT,
                subscriber_count INTEGER,
                video_count INTEGER,
                last_video_count INTEGER,
                last_check DATETIME,
                last_video_date DATETIME,
                auto_download BOOLEAN DEFAULT 0,
                priority INTEGER DEFAULT 5,
                download_options TEXT,  -- JSON string
                tags TEXT,  -- JSON array
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Settings table
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                value_type TEXT DEFAULT 'string',  -- string, integer, boolean, json
                description TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better performance
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_download_history_url ON download_history(url)")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_download_history_date ON download_history(download_date)")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_download_history_platform ON download_history(platform)")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_creators_platform ON creators(platform)")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_creators_last_check ON creators(last_check)")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key)")
        
        logger.info("Created initial database tables and indexes")
    
    def get_connection(self) -> DatabaseConnection:
        """Get database connection"""
        return self.connection
    
    def close(self):
        """Close database connection"""
        self.connection.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()