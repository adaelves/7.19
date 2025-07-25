"""
Tests for database functionality.
"""
import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from app.data.database import DatabaseService, get_database_service
from app.data.models.core import (
    DownloadTask, TaskStatus, VideoMetadata, CreatorProfile,
    Platform, QualityOption, DownloadOptions
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db_service = DatabaseService(db_path)
    yield db_service
    
    db_service.close()
    os.unlink(db_path)


@pytest.fixture
def sample_metadata():
    """Sample video metadata for testing"""
    return VideoMetadata(
        title="Test Video",
        author="Test Author",
        thumbnail_url="https://example.com/thumb.jpg",
        duration=300,
        view_count=1000,
        upload_date=datetime.now(),
        quality_options=[
            QualityOption(
                quality_id="720p",
                resolution="1280x720",
                format_name="mp4",
                file_size=50000000,
                bitrate=2500
            )
        ],
        platform=Platform.YOUTUBE,
        video_id="test123",
        channel_id="channel123"
    )


@pytest.fixture
def sample_task(sample_metadata):
    """Sample download task for testing"""
    return DownloadTask(
        id="task123",
        url="https://youtube.com/watch?v=test123",
        metadata=sample_metadata,
        status=TaskStatus.COMPLETED,
        progress=100.0,
        download_path="/downloads/test_video.mp4",
        created_at=datetime.now(),
        completed_at=datetime.now(),
        file_size=50000000
    )


@pytest.fixture
def sample_creator():
    """Sample creator profile for testing"""
    return CreatorProfile(
        id="creator123",
        name="Test Creator",
        platform=Platform.YOUTUBE,
        channel_url="https://youtube.com/channel/test",
        avatar_url="https://example.com/avatar.jpg",
        last_check=datetime.now(),
        auto_download=True,
        priority=8,
        description="Test creator description",
        subscriber_count=10000,
        video_count=50,
        tags=["tech", "tutorial"]
    )


class TestDatabaseConnection:
    """Test database connection and basic operations"""
    
    def test_database_initialization(self, temp_db):
        """Test database initialization"""
        assert temp_db is not None
        
        # Check database info
        info = temp_db.get_database_info()
        assert info['exists'] is True
        assert info['version'] == 1
        assert info['size'] > 0
    
    def test_database_tables_created(self, temp_db):
        """Test that all required tables are created"""
        # Test by trying to query each table
        connection = temp_db.db_manager.get_connection()
        
        # Check download_history table
        result = connection.fetchone("SELECT name FROM sqlite_master WHERE type='table' AND name='download_history'")
        assert result is not None
        
        # Check creators table
        result = connection.fetchone("SELECT name FROM sqlite_master WHERE type='table' AND name='creators'")
        assert result is not None
        
        # Check settings table
        result = connection.fetchone("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
        assert result is not None


class TestDownloadHistory:
    """Test download history operations"""
    
    def test_add_download_record(self, temp_db, sample_task, sample_metadata):
        """Test adding download record"""
        history_id = temp_db.add_download_record(sample_task, sample_metadata)
        assert history_id > 0
        
        # Verify record was added
        history = temp_db.get_download_history(limit=1)
        assert len(history) == 1
        assert history[0]['url'] == sample_task.url
        assert history[0]['title'] == sample_metadata.title
    
    def test_search_downloads(self, temp_db, sample_task, sample_metadata):
        """Test searching download history"""
        # Add a record first
        temp_db.add_download_record(sample_task, sample_metadata)
        
        # Search by title
        results = temp_db.search_downloads("Test Video")
        assert len(results) == 1
        assert results[0]['title'] == "Test Video"
        
        # Search by author
        results = temp_db.search_downloads("Test Author")
        assert len(results) == 1
        assert results[0]['author'] == "Test Author"
        
        # Search with no results
        results = temp_db.search_downloads("NonExistent")
        assert len(results) == 0
    
    def test_get_downloads_by_url(self, temp_db, sample_task, sample_metadata):
        """Test getting downloads by URL"""
        # Add a record first
        temp_db.add_download_record(sample_task, sample_metadata)
        
        results = temp_db.get_downloads_by_url(sample_task.url)
        assert len(results) == 1
        assert results[0]['url'] == sample_task.url
    
    def test_update_download_md5(self, temp_db, sample_task, sample_metadata):
        """Test updating MD5 hash"""
        history_id = temp_db.add_download_record(sample_task, sample_metadata)
        
        # Update MD5
        md5_hash = "abcdef123456"
        success = temp_db.update_download_md5(history_id, md5_hash)
        assert success is True
        
        # Verify MD5 was updated
        record = temp_db.check_duplicate_by_md5(md5_hash)
        assert record is not None
        assert record['md5_hash'] == md5_hash
    
    def test_get_download_statistics(self, temp_db, sample_task, sample_metadata):
        """Test getting download statistics"""
        # Add some records
        temp_db.add_download_record(sample_task, sample_metadata)
        
        stats = temp_db.get_download_statistics()
        assert stats['total_downloads'] == 1
        assert 'youtube' in stats['by_platform']
        assert stats['by_platform']['youtube'] == 1
        assert stats['total_size'] == sample_task.file_size


class TestCreatorManagement:
    """Test creator management operations"""
    
    def test_add_creator(self, temp_db, sample_creator):
        """Test adding creator"""
        success = temp_db.add_creator(sample_creator)
        assert success is True
        
        # Verify creator was added
        creators = temp_db.get_all_creators()
        assert len(creators) == 1
        assert creators[0].name == sample_creator.name
    
    def test_get_creator_by_id(self, temp_db, sample_creator):
        """Test getting creator by ID"""
        temp_db.add_creator(sample_creator)
        
        creator = temp_db.get_creator_by_id(sample_creator.id)
        assert creator is not None
        assert creator.name == sample_creator.name
        assert creator.platform == sample_creator.platform
    
    def test_get_creator_by_url(self, temp_db, sample_creator):
        """Test getting creator by URL"""
        temp_db.add_creator(sample_creator)
        
        creator = temp_db.get_creator_by_url(sample_creator.channel_url)
        assert creator is not None
        assert creator.name == sample_creator.name
    
    def test_update_creator(self, temp_db, sample_creator):
        """Test updating creator"""
        temp_db.add_creator(sample_creator)
        
        # Update creator
        sample_creator.name = "Updated Creator"
        sample_creator.subscriber_count = 20000
        
        success = temp_db.update_creator(sample_creator)
        assert success is True
        
        # Verify update
        creator = temp_db.get_creator_by_id(sample_creator.id)
        assert creator.name == "Updated Creator"
        assert creator.subscriber_count == 20000
    
    def test_get_creators_for_auto_download(self, temp_db, sample_creator):
        """Test getting creators with auto-download enabled"""
        # Add creator with auto-download enabled
        sample_creator.auto_download = True
        temp_db.add_creator(sample_creator)
        
        # Add another creator with auto-download disabled
        creator2 = CreatorProfile(
            id="creator456",
            name="Creator 2",
            platform=Platform.BILIBILI,
            channel_url="https://bilibili.com/user/test",
            avatar_url="https://example.com/avatar2.jpg",
            last_check=datetime.now(),
            auto_download=False,
            priority=5
        )
        temp_db.add_creator(creator2)
        
        # Get auto-download creators
        auto_creators = temp_db.get_creators_for_auto_download()
        assert len(auto_creators) == 1
        assert auto_creators[0].id == sample_creator.id
    
    def test_get_creators_needing_check(self, temp_db, sample_creator):
        """Test getting creators that need checking"""
        # Set last check to 2 hours ago
        old_time = datetime.now() - timedelta(hours=2)
        sample_creator.last_check = old_time
        temp_db.add_creator(sample_creator)
        
        # Verify the creator was stored correctly
        stored_creator = temp_db.get_creator_by_id(sample_creator.id)
        assert stored_creator is not None
        
        # Get creators needing check (1 hour interval)
        creators = temp_db.get_creators_needing_check(check_interval=3600)
        assert len(creators) == 1
        assert creators[0].id == sample_creator.id
    
    def test_update_creator_check(self, temp_db, sample_creator):
        """Test updating creator check timestamp"""
        temp_db.add_creator(sample_creator)
        
        # Update check with new video count
        success = temp_db.update_creator_check(sample_creator.id, video_count=55)
        assert success is True
        
        # Verify update
        creator = temp_db.get_creator_by_id(sample_creator.id)
        assert creator.last_video_count == 55
    
    def test_delete_creator(self, temp_db, sample_creator):
        """Test deleting creator"""
        temp_db.add_creator(sample_creator)
        
        # Delete creator
        success = temp_db.delete_creator(sample_creator.id)
        assert success is True
        
        # Verify deletion
        creator = temp_db.get_creator_by_id(sample_creator.id)
        assert creator is None


class TestSettings:
    """Test settings operations"""
    
    def test_set_and_get_string_setting(self, temp_db):
        """Test setting and getting string values"""
        key = "test_string"
        value = "test value"
        
        success = temp_db.set_setting(key, value)
        assert success is True
        
        retrieved = temp_db.get_setting(key)
        assert retrieved == value
    
    def test_set_and_get_integer_setting(self, temp_db):
        """Test setting and getting integer values"""
        key = "test_integer"
        value = 42
        
        success = temp_db.set_setting(key, value)
        assert success is True
        
        retrieved = temp_db.get_setting(key)
        assert retrieved == value
        assert isinstance(retrieved, int)
    
    def test_set_and_get_boolean_setting(self, temp_db):
        """Test setting and getting boolean values"""
        key = "test_boolean"
        value = True
        
        success = temp_db.set_setting(key, value)
        assert success is True
        
        retrieved = temp_db.get_setting(key)
        assert retrieved == value
        assert isinstance(retrieved, bool)
    
    def test_set_and_get_json_setting(self, temp_db):
        """Test setting and getting JSON values"""
        key = "test_json"
        value = {"nested": {"key": "value"}, "list": [1, 2, 3]}
        
        success = temp_db.set_setting(key, value)
        assert success is True
        
        retrieved = temp_db.get_setting(key)
        assert retrieved == value
    
    def test_get_setting_with_default(self, temp_db):
        """Test getting non-existent setting with default"""
        default_value = "default"
        retrieved = temp_db.get_setting("non_existent", default_value)
        assert retrieved == default_value
    
    def test_get_all_settings(self, temp_db):
        """Test getting all settings"""
        # Set multiple settings
        temp_db.set_setting("setting1", "value1")
        temp_db.set_setting("setting2", 42)
        temp_db.set_setting("setting3", True)
        
        all_settings = temp_db.get_all_settings()
        assert len(all_settings) == 3
        assert all_settings["setting1"] == "value1"
        assert all_settings["setting2"] == 42
        assert all_settings["setting3"] is True
    
    def test_delete_setting(self, temp_db):
        """Test deleting setting"""
        key = "test_delete"
        temp_db.set_setting(key, "value")
        
        # Verify setting exists
        assert temp_db.get_setting(key) == "value"
        
        # Delete setting
        success = temp_db.delete_setting(key)
        assert success is True
        
        # Verify setting is gone
        assert temp_db.get_setting(key) is None


class TestDatabaseUtilities:
    """Test database utility functions"""
    
    def test_backup_and_restore(self, temp_db, sample_task, sample_metadata):
        """Test database backup and restore"""
        # Add some data
        temp_db.add_download_record(sample_task, sample_metadata)
        temp_db.set_setting("test_setting", "test_value")
        
        # Create backup
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            backup_path = f.name
        
        try:
            success = temp_db.backup_database(backup_path)
            assert success is True
            assert Path(backup_path).exists()
            
            # Verify backup has data
            with DatabaseService(backup_path) as backup_db:
                history = backup_db.get_download_history()
                assert len(history) == 1
                setting = backup_db.get_setting("test_setting")
                assert setting == "test_value"
            
        finally:
            if Path(backup_path).exists():
                try:
                    os.unlink(backup_path)
                except PermissionError:
                    # On Windows, sometimes files are still locked
                    import time
                    time.sleep(0.1)
                    try:
                        os.unlink(backup_path)
                    except PermissionError:
                        pass  # Skip cleanup if still locked
    
    def test_vacuum_database(self, temp_db):
        """Test database vacuum operation"""
        success = temp_db.vacuum_database()
        assert success is True


class TestGlobalService:
    """Test global database service"""
    
    def test_get_global_service(self):
        """Test getting global database service"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            service1 = get_database_service(db_path)
            service2 = get_database_service(db_path)
            
            # Should return the same instance
            assert service1 is service2
            
        finally:
            from app.data.database.service import close_database_service
            close_database_service()
            os.unlink(db_path)


if __name__ == "__main__":
    pytest.main([__file__])