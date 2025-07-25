"""
Test core data models.
"""
import pytest
from datetime import datetime
from app.data.models.core import (
    VideoMetadata, DownloadTask, CreatorProfile, 
    QualityOption, DownloadOptions, TaskStatus, Platform
)


def test_video_metadata_creation():
    """Test VideoMetadata creation"""
    quality_options = [
        QualityOption(
            quality_id="720p",
            resolution="1280x720",
            format_name="mp4",
            file_size=1024000,
            bitrate=2500
        )
    ]
    
    metadata = VideoMetadata(
        title="Test Video",
        author="Test Author",
        thumbnail_url="https://example.com/thumb.jpg",
        duration=300,
        view_count=1000,
        upload_date=datetime.now(),
        quality_options=quality_options,
        platform=Platform.YOUTUBE
    )
    
    assert metadata.title == "Test Video"
    assert metadata.author == "Test Author"
    assert metadata.platform == Platform.YOUTUBE
    assert len(metadata.quality_options) == 1
    assert metadata.quality_options[0].resolution == "1280x720"


def test_download_task_creation():
    """Test DownloadTask creation"""
    task = DownloadTask(
        id="test-123",
        url="https://example.com/video",
        metadata=None,
        status=TaskStatus.PENDING,
        progress=0.0,
        download_path="/downloads/test.mp4",
        created_at=datetime.now()
    )
    
    assert task.id == "test-123"
    assert task.status == TaskStatus.PENDING
    assert task.is_active is True
    assert task.is_completed is False
    assert task.is_failed is False


def test_creator_profile_creation():
    """Test CreatorProfile creation"""
    creator = CreatorProfile(
        id="creator-123",
        name="Test Creator",
        platform=Platform.YOUTUBE,
        channel_url="https://youtube.com/channel/test",
        avatar_url="https://example.com/avatar.jpg",
        last_check=datetime.now(),
        auto_download=True,
        priority=5
    )
    
    assert creator.name == "Test Creator"
    assert creator.platform == Platform.YOUTUBE
    assert creator.auto_download is True
    assert creator.priority == 5


def test_download_options_validation():
    """Test DownloadOptions validation"""
    options = DownloadOptions(
        output_path="/downloads",
        quality_preference="720p",
        max_threads=8
    )
    
    assert options.output_path == "/downloads"
    assert options.quality_preference == "720p"
    assert options.max_threads == 8
    
    # Test thread limit validation
    options_high = DownloadOptions(
        output_path="/downloads",
        max_threads=20  # Should be capped at 16
    )
    assert options_high.max_threads == 16
    
    options_low = DownloadOptions(
        output_path="/downloads", 
        max_threads=0  # Should be set to 1
    )
    assert options_low.max_threads == 1


if __name__ == "__main__":
    pytest.main([__file__])