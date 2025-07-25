"""
Demo script for the history system functionality.
"""
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.history_service import HistoryService
from app.data.database.connection import DatabaseManager
from app.data.models.core import DownloadTask, TaskStatus, VideoMetadata, Platform


def create_sample_data(history_service):
    """Create sample download history data"""
    print("Creating sample download history data...")
    
    # Sample data
    sample_downloads = [
        {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "Rick Astley - Never Gonna Give You Up",
            "author": "Rick Astley",
            "platform": Platform.YOUTUBE,
            "duration": 213,
            "view_count": 1000000000,
            "file_size": 15728640  # 15MB
        },
        {
            "url": "https://www.bilibili.com/video/BV1xx411c7mD",
            "title": "【技术分享】Python爬虫入门教程",
            "author": "技术UP主",
            "platform": Platform.BILIBILI,
            "duration": 1800,
            "view_count": 50000,
            "file_size": 104857600  # 100MB
        },
        {
            "url": "https://www.tiktok.com/@user/video/123456789",
            "title": "搞笑短视频合集",
            "author": "搞笑博主",
            "platform": Platform.TIKTOK,
            "duration": 60,
            "view_count": 100000,
            "file_size": 5242880  # 5MB
        },
        {
            "url": "https://www.instagram.com/p/ABC123/",
            "title": "美食制作过程",
            "author": "美食达人",
            "platform": Platform.INSTAGRAM,
            "duration": 120,
            "view_count": 25000,
            "file_size": 8388608  # 8MB
        }
    ]
    
    for i, data in enumerate(sample_downloads):
        # Create download task
        task = DownloadTask(
            id=f"demo-task-{i}",
            url=data["url"],
            metadata=None,
            status=TaskStatus.COMPLETED,
            progress=100.0,
            download_path=f"downloads/{data['title']}.mp4",
            created_at=datetime.now() - timedelta(days=i),
            completed_at=datetime.now() - timedelta(days=i),
            file_size=data["file_size"]
        )
        
        # Create metadata
        metadata = VideoMetadata(
            title=data["title"],
            author=data["author"],
            thumbnail_url=f"https://example.com/thumb{i}.jpg",
            duration=data["duration"],
            view_count=data["view_count"],
            upload_date=datetime.now() - timedelta(days=i+1),
            quality_options=[],
            platform=data["platform"]
        )
        
        # Add to history
        record_id = history_service.add_download_record(task, metadata)
        print(f"  Added record {record_id}: {data['title']}")
    
    print(f"Created {len(sample_downloads)} sample records\n")


def demo_basic_operations(history_service):
    """Demonstrate basic history operations"""
    print("=== Basic History Operations ===")
    
    # Get all history
    all_records = history_service.get_history(limit=10)
    print(f"Total records: {len(all_records)}")
    
    # Show recent downloads
    print("\nRecent downloads:")
    for record in all_records[:3]:
        print(f"  - {record['title']} ({record['platform']})")
    
    # Search functionality
    print("\nSearch results for 'Python':")
    search_results = history_service.search_history("Python")
    for record in search_results:
        print(f"  - {record['title']} by {record['author']}")
    
    # Platform filtering
    print("\nYouTube downloads:")
    youtube_records = history_service.get_history_by_platform("youtube")
    for record in youtube_records:
        print(f"  - {record['title']}")
    
    print()


def demo_statistics(history_service):
    """Demonstrate statistics functionality"""
    print("=== Download Statistics ===")
    
    stats = history_service.get_statistics()
    
    print(f"Total downloads: {stats['total_downloads']}")
    print(f"Total file size: {stats['total_size_formatted']}")
    print(f"Recent downloads (7 days): {stats['recent_downloads']}")
    print(f"Supported platforms: {stats['platforms_count']}")
    
    print("\nPlatform distribution:")
    for platform, count in stats['by_platform'].items():
        print(f"  {platform}: {count} downloads")
    
    # Download trends
    trends = history_service.get_download_trends(7)
    print(f"\nDownload trends (7 days):")
    print(f"  Average per day: {trends['average_per_day']:.1f}")
    print(f"  Total recent: {trends['total_recent']}")
    
    print()


def demo_duplicate_detection(history_service):
    """Demonstrate duplicate detection"""
    print("=== Duplicate Detection ===")
    
    # Add a duplicate record
    duplicate_task = DownloadTask(
        id="duplicate-task",
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Same as first record
        metadata=None,
        status=TaskStatus.COMPLETED,
        progress=100.0,
        download_path="downloads/duplicate.mp4",
        created_at=datetime.now(),
        completed_at=datetime.now(),
        file_size=15728640
    )
    
    duplicate_metadata = VideoMetadata(
        title="Rick Astley - Never Gonna Give You Up (Duplicate)",
        author="Rick Astley",
        thumbnail_url="https://example.com/thumb_dup.jpg",
        duration=213,
        view_count=1000000000,
        upload_date=datetime.now(),
        quality_options=[],
        platform=Platform.YOUTUBE
    )
    
    history_service.add_download_record(duplicate_task, duplicate_metadata)
    print("Added duplicate record for testing")
    
    # Check for URL duplicates
    duplicate_check = history_service.check_duplicate_by_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    if duplicate_check:
        print(f"Found duplicate URL: {duplicate_check['title']}")
    
    # Detect all duplicates
    duplicates = history_service.detect_duplicates()
    print(f"Found {len(duplicates)} groups of duplicate files")
    
    print()


def demo_export_functionality(history_service):
    """Demonstrate export functionality"""
    print("=== Export Functionality ===")
    
    # Export to CSV
    csv_path = "demo_history_export.csv"
    if history_service.export_history(csv_path, 'csv'):
        print(f"Successfully exported history to {csv_path}")
        
        # Show file size
        if os.path.exists(csv_path):
            file_size = os.path.getsize(csv_path)
            print(f"  File size: {file_size} bytes")
    
    # Export to JSON
    json_path = "demo_history_export.json"
    if history_service.export_history(json_path, 'json'):
        print(f"Successfully exported history to {json_path}")
        
        # Show file size
        if os.path.exists(json_path):
            file_size = os.path.getsize(json_path)
            print(f"  File size: {file_size} bytes")
    
    print()


def demo_cleanup(history_service):
    """Demonstrate cleanup functionality"""
    print("=== Cleanup Functionality ===")
    
    # Get current count
    current_records = history_service.get_history(limit=1000)
    print(f"Records before cleanup: {len(current_records)}")
    
    # Cleanup old records (older than 2 days for demo)
    deleted_count = history_service.cleanup_old_records(2)
    print(f"Cleaned up {deleted_count} old records")
    
    # Get count after cleanup
    remaining_records = history_service.get_history(limit=1000)
    print(f"Records after cleanup: {len(remaining_records)}")
    
    print()


def main():
    """Main demo function"""
    print("🎬 History System Demo")
    print("=" * 50)
    
    # Initialize database
    db_path = "demo_history.db"
    db_manager = DatabaseManager(db_path)
    db_manager.initialize()
    
    # Create history service
    history_service = HistoryService(db_manager.get_connection())
    
    try:
        # Create sample data
        create_sample_data(history_service)
        
        # Demonstrate various features
        demo_basic_operations(history_service)
        demo_statistics(history_service)
        demo_duplicate_detection(history_service)
        demo_export_functionality(history_service)
        demo_cleanup(history_service)
        
        print("✅ Demo completed successfully!")
        print("\nGenerated files:")
        for file in ["demo_history.db", "demo_history_export.csv", "demo_history_export.json"]:
            if os.path.exists(file):
                print(f"  - {file}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        db_manager.close()


if __name__ == "__main__":
    main()