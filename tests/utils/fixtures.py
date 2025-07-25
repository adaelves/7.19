"""
Common test fixtures for the application.
"""
import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.data.database import DatabaseService
from app.data.models.core import (
    VideoMetadata, DownloadTask, CreatorProfile, QualityOption,
    Platform, TaskStatus
)
from tests.utils.test_helpers import TestDataFactory


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db_service = DatabaseService(db_path)
    yield db_service
    
    db_service.close()
    try:
        os.unlink(db_path)
    except (OSError, PermissionError):
        pass  # Ignore cleanup errors


@pytest.fixture
def sample_metadata():
    """Sample video metadata for testing"""
    return TestDataFactory.create_video_metadata(
        title="Sample Test Video",
        author="Test Channel",
        platform=Platform.YOUTUBE
    )


@pytest.fixture
def sample_task(sample_metadata):
    """Sample download task for testing"""
    return TestDataFactory.create_download_task(
        url="https://youtube.com/watch?v=sample123",
        status=TaskStatus.COMPLETED,
        progress=100.0,
        metadata=sample_metadata
    )


@pytest.fixture
def sample_creator():
    """Sample creator profile for testing"""
    return TestDataFactory.create_creator_profile(
        name="Sample Creator",
        platform=Platform.YOUTUBE,
        auto_download=True,
        priority=8
    )


@pytest.fixture
def multiple_tasks():
    """Multiple download tasks for testing"""
    tasks = []
    for i in range(5):
        task = TestDataFactory.create_download_task(
            url=f"https://youtube.com/watch?v=test{i:03d}",
            status=TaskStatus.COMPLETED if i % 2 == 0 else TaskStatus.PENDING
        )
        tasks.append(task)
    return tasks


@pytest.fixture
def multiple_creators():
    """Multiple creator profiles for testing"""
    creators = []
    platforms = [Platform.YOUTUBE, Platform.BILIBILI, Platform.TIKTOK]
    
    for i, platform in enumerate(platforms):
        creator = TestDataFactory.create_creator_profile(
            name=f"Creator {i+1}",
            platform=platform,
            auto_download=i % 2 == 0,
            priority=i + 5
        )
        creators.append(creator)
    
    return creators


@pytest.fixture
def mock_yt_dlp():
    """Mock yt-dlp for testing"""
    with patch('yt_dlp.YoutubeDL') as mock_ytdl:
        mock_instance = Mock()
        mock_ytdl.return_value = mock_instance
        
        # Configure default behavior
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'uploader': 'Test Channel',
            'duration': 300,
            'view_count': 1000,
            'upload_date': '20231201',
            'formats': [
                {
                    'format_id': '720p',
                    'height': 720,
                    'width': 1280,
                    'ext': 'mp4',
                    'filesize': 50000000,
                    'url': 'https://example.com/video.mp4'
                }
            ]
        }
        
        yield mock_instance


@pytest.fixture
def mock_requests():
    """Mock requests library for testing"""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post:
        
        # Configure default responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.text = ""
        mock_response.content = b""
        
        mock_get.return_value = mock_response
        mock_post.return_value = mock_response
        
        yield {
            'get': mock_get,
            'post': mock_post,
            'response': mock_response
        }


@pytest.fixture
def mock_file_system(temp_directory):
    """Mock file system operations"""
    from tests.utils.test_helpers import TestFileManager
    
    file_manager = TestFileManager(temp_directory)
    
    # Create some test files
    file_manager.create_test_file("downloads/test_video.mp4", "fake video content")
    file_manager.create_test_file("downloads/test_image.jpg", "fake image content")
    file_manager.create_test_dir("downloads/completed")
    
    yield file_manager
    
    file_manager.cleanup()


@pytest.fixture
def config_data():
    """Sample configuration data"""
    return {
        'download_path': '/downloads',
        'max_concurrent_downloads': 3,
        'default_quality': '720p',
        'enable_notifications': True,
        'theme': 'dark',
        'auto_check_updates': True,
        'proxy': {
            'enabled': False,
            'type': 'http',
            'host': '',
            'port': 8080
        },
        'advanced': {
            'rate_limit': 0,
            'retry_attempts': 3,
            'timeout': 30
        }
    }


@pytest.fixture
def mock_plugin_system():
    """Mock plugin system for testing"""
    from unittest.mock import AsyncMock
    
    mock_manager = Mock()
    mock_manager.initialize = AsyncMock(return_value=True)
    mock_manager.route_url = AsyncMock()
    mock_manager.extract_info = AsyncMock()
    mock_manager.get_metadata = AsyncMock()
    mock_manager.is_url_supported = Mock(return_value=True)
    mock_manager.get_supported_domains = Mock(return_value=['youtube.com', 'bilibili.com'])
    
    # Configure default responses
    mock_manager.extract_info.return_value = {
        'title': 'Test Video',
        'id': 'test123',
        'uploader': 'Test Channel'
    }
    
    mock_manager.get_metadata.return_value = TestDataFactory.create_video_metadata()
    
    yield mock_manager


@pytest.fixture
def performance_data():
    """Performance test data"""
    return {
        'max_memory_mb': 500,
        'max_cpu_percent': 80,
        'max_response_time_ms': 1000,
        'min_throughput_ops_per_sec': 10
    }


@pytest.fixture(scope="session")
def test_videos():
    """Test video URLs for integration testing"""
    return {
        'youtube': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'bilibili': 'https://www.bilibili.com/video/BV1xx411c7mu',
        'test_short': 'https://example.com/short_video',
        'test_long': 'https://example.com/long_video',
        'test_playlist': 'https://youtube.com/playlist?list=PLtest'
    }


@pytest.fixture
def ui_test_data():
    """UI test data"""
    return {
        'test_urls': [
            'https://youtube.com/watch?v=test1',
            'https://bilibili.com/video/test2',
            'https://tiktok.com/@user/video/test3'
        ],
        'test_settings': {
            'download_path': '/test/downloads',
            'quality': '1080p',
            'theme': 'light'
        },
        'test_creators': [
            'Test Creator 1',
            'Test Creator 2',
            'Test Creator 3'
        ]
    }