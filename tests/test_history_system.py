"""
Tests for the history system implementation.
"""
import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from app.services.history_service import HistoryService
from app.data.database.connection import DatabaseManager
from app.data.models.core import DownloadTask, TaskStatus, VideoMetadata, Platform


class TestHistoryService:
    """Test cases for HistoryService"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Initialize database
        db_manager = DatabaseManager(db_path)
        db_manager.initialize()
        
        yield db_manager.get_connection()
        
        # Cleanup
        db_manager.close()
        os.unlink(db_path)
    
    @pytest.fixture
    def history_service(self, temp_db):
        """Create HistoryService instance with temp database"""
        return HistoryService(temp_db)
    
    @pytest.fixture
    def sample_task(self):
        """Create sample download task"""
        return DownloadTask(
            id="test-task-123",
            url="https://www.youtube.com/watch?v=test123",
            metadata=None,
            status=TaskStatus.COMPLETED,
            progress=100.0,
            download_path="test_video.mp4",
            created_at=datetime.now(),
            file_size=1024000,
            completed_at=datetime.now()
        )
    
    @pytest.fixture
    def sample_metadata(self):
        """Create sample video metadata"""
        return VideoMetadata(
            title="Test Video",
            author="Test Author",
            thumbnail_url="https://example.com/thumb.jpg",
            duration=300,
            view_count=1000,
            upload_date=datetime.now(),
            quality_options=[],
            platform=Platform.YOUTUBE,
            video_id="test123"
        )
    
    def test_add_download_record(self, history_service, sample_task, sample_metadata):
        """Test adding download record"""
        record_id = history_service.add_download_record(sample_task, sample_metadata)
        assert record_id > 0
        
        # Verify record was added
        records = history_service.get_history(limit=10)
        assert len(records) == 1
        assert records[0]['url'] == sample_task.url
        assert records[0]['title'] == sample_metadata.title
    
    def test_get_history_pagination(self, history_service, sample_task, sample_metadata):
        """Test history pagination"""
        # Add multiple records
        for i in range(15):
            task = DownloadTask(
                id=f"test-task-{i}",
                url=f"https://test.com/video{i}",
                metadata=None,
                status=TaskStatus.COMPLETED,
                progress=100.0,
                download_path=f"video{i}.mp4",
                created_at=datetime.now()
            )
            metadata = VideoMetadata(
                title=f"Video {i}",
                author="Test Author",
                thumbnail_url="",
                duration=300,
                view_count=1000,
                upload_date=datetime.now(),
                quality_options=[],
                platform=Platform.YOUTUBE
            )
            history_service.add_download_record(task, metadata)
        
        # Test pagination
        page1 = history_service.get_history(limit=10, offset=0)
        page2 = history_service.get_history(limit=10, offset=10)
        
        assert len(page1) == 10
        assert len(page2) == 5
    
    def test_search_history(self, history_service, sample_task, sample_metadata):
        """Test history search functionality"""
        # Add test record
        history_service.add_download_record(sample_task, sample_metadata)
        
        # Search by keyword
        results = history_service.search_history("Test Video")
        assert len(results) == 1
        assert results[0]['title'] == "Test Video"
        
        # Search by platform
        results = history_service.search_history("", platform="youtube")
        assert len(results) == 1
        
        # Search with no results
        results = history_service.search_history("NonExistent")
        assert len(results) == 0
    
    def test_duplicate_detection_by_url(self, history_service, sample_task, sample_metadata):
        """Test duplicate detection by URL"""
        # Add record
        history_service.add_download_record(sample_task, sample_metadata)
        
        # Check for duplicate
        duplicate = history_service.check_duplicate_by_url(sample_task.url)
        assert duplicate is not None
        assert duplicate['url'] == sample_task.url
        
        # Check non-existent URL
        no_duplicate = history_service.check_duplicate_by_url("https://nonexistent.com")
        assert no_duplicate is None
    
    def test_get_statistics(self, history_service, sample_task, sample_metadata):
        """Test statistics generation"""
        # Add test records
        for i, platform in enumerate([Platform.YOUTUBE, Platform.BILIBILI, Platform.YOUTUBE]):
            task = DownloadTask(
                id=f"test-stats-{i}",
                url=f"https://test.com/{platform.value}",
                metadata=None,
                status=TaskStatus.COMPLETED,
                progress=100.0,
                download_path="test.mp4",
                created_at=datetime.now(),
                file_size=1000000
            )
            metadata = VideoMetadata(
                title="Test",
                author="Author",
                thumbnail_url="",
                duration=300,
                view_count=1000,
                upload_date=datetime.now(),
                quality_options=[],
                platform=platform
            )
            history_service.add_download_record(task, metadata)
        
        stats = history_service.get_statistics()
        
        assert stats['total_downloads'] == 3
        assert stats['by_platform']['youtube'] == 2
        assert stats['by_platform']['bilibili'] == 1
        assert 'total_size_formatted' in stats
    
    def test_export_to_csv(self, history_service, sample_task, sample_metadata):
        """Test CSV export functionality"""
        # Add test record
        history_service.add_download_record(sample_task, sample_metadata)
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            export_path = f.name
        
        try:
            success = history_service.export_history(export_path, 'csv')
            assert success
            
            # Verify file exists and has content
            assert os.path.exists(export_path)
            with open(export_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert 'Test Video' in content
                assert sample_task.url in content
        finally:
            os.unlink(export_path)
    
    def test_export_to_json(self, history_service, sample_task, sample_metadata):
        """Test JSON export functionality"""
        # Add test record
        history_service.add_download_record(sample_task, sample_metadata)
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            export_path = f.name
        
        try:
            success = history_service.export_history(export_path, 'json')
            assert success
            
            # Verify file exists and has valid JSON
            assert os.path.exists(export_path)
            import json
            with open(export_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert 'records' in data
                assert len(data['records']) == 1
                assert data['records'][0]['title'] == 'Test Video'
        finally:
            os.unlink(export_path)
    
    def test_delete_record(self, history_service, sample_task, sample_metadata):
        """Test record deletion"""
        # Add record
        record_id = history_service.add_download_record(sample_task, sample_metadata)
        
        # Verify record exists
        records = history_service.get_history()
        assert len(records) == 1
        
        # Delete record
        success = history_service.delete_record(record_id)
        assert success
        
        # Verify record is deleted
        records = history_service.get_history()
        assert len(records) == 0
    
    def test_cleanup_old_records(self, history_service):
        """Test cleanup of old records"""
        # Add old record
        old_task = DownloadTask(
            id="old-task",
            url="https://old.com/video",
            metadata=None,
            status=TaskStatus.COMPLETED,
            progress=100.0,
            download_path="old.mp4",
            created_at=datetime.now() - timedelta(days=400),
            completed_at=datetime.now() - timedelta(days=400)
        )
        old_metadata = VideoMetadata(
            title="Old Video",
            author="Old Author",
            thumbnail_url="",
            duration=300,
            view_count=1000,
            upload_date=datetime.now() - timedelta(days=400),
            quality_options=[],
            platform=Platform.YOUTUBE
        )
        
        # Add recent record
        recent_task = DownloadTask(
            id="recent-task",
            url="https://recent.com/video",
            metadata=None,
            status=TaskStatus.COMPLETED,
            progress=100.0,
            download_path="recent.mp4",
            created_at=datetime.now(),
            completed_at=datetime.now()
        )
        recent_metadata = VideoMetadata(
            title="Recent Video",
            author="Recent Author",
            thumbnail_url="",
            duration=300,
            view_count=1000,
            upload_date=datetime.now(),
            quality_options=[],
            platform=Platform.YOUTUBE
        )
        
        history_service.add_download_record(old_task, old_metadata)
        history_service.add_download_record(recent_task, recent_metadata)
        
        # Cleanup records older than 365 days
        deleted_count = history_service.cleanup_old_records(365)
        
        # Verify old record was deleted, recent record remains
        records = history_service.get_history()
        assert len(records) == 1
        assert records[0]['title'] == "Recent Video"
    
    def test_get_download_trends(self, history_service):
        """Test download trends analysis"""
        # Add records from different dates
        for i in range(5):
            task = DownloadTask(
                id=f"trends-task-{i}",
                url=f"https://test.com/video{i}",
                metadata=None,
                status=TaskStatus.COMPLETED,
                progress=100.0,
                download_path=f"video{i}.mp4",
                created_at=datetime.now() - timedelta(days=i),
                completed_at=datetime.now() - timedelta(days=i)
            )
            metadata = VideoMetadata(
                title=f"Video {i}",
                author="Author",
                thumbnail_url="",
                duration=300,
                view_count=1000,
                upload_date=datetime.now() - timedelta(days=i),
                quality_options=[],
                platform=Platform.YOUTUBE
            )
            history_service.add_download_record(task, metadata)
        
        trends = history_service.get_download_trends(7)
        
        assert trends['total_recent'] == 5
        assert trends['average_per_day'] > 0
        assert 'daily_downloads' in trends
        assert 'platform_distribution' in trends


if __name__ == "__main__":
    pytest.main([__file__])