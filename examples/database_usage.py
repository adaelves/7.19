#!/usr/bin/env python3
"""
Example usage of the database service.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app.data.database import DatabaseService
from app.data.models.core import (
    DownloadTask, TaskStatus, VideoMetadata, CreatorProfile,
    Platform, QualityOption, DownloadOptions
)


def main():
    """Demonstrate database usage"""
    
    # Initialize database service
    with DatabaseService("example.db") as db:
        print("Database initialized successfully!")
        
        # Example 1: Add a download record
        print("\n1. Adding download record...")
        
        # Create sample metadata
        metadata = VideoMetadata(
            title="Sample Video",
            author="Sample Creator",
            thumbnail_url="https://example.com/thumb.jpg",
            duration=300,
            view_count=1000,
            upload_date=datetime.now(),
            quality_options=[
                QualityOption(
                    quality_id="720p",
                    resolution="1280x720",
                    format_name="mp4",
                    file_size=50000000
                )
            ],
            platform=Platform.YOUTUBE,
            video_id="sample123"
        )
        
        # Create download task
        task = DownloadTask(
            id="task123",
            url="https://youtube.com/watch?v=sample123",
            metadata=metadata,
            status=TaskStatus.COMPLETED,
            progress=100.0,
            download_path="/downloads/sample_video.mp4",
            created_at=datetime.now(),
            file_size=50000000
        )
        
        # Add to database
        history_id = db.add_download_record(task, metadata)
        print(f"Added download record with ID: {history_id}")
        
        # Example 2: Search download history
        print("\n2. Searching download history...")
        results = db.search_downloads("Sample")
        print(f"Found {len(results)} matching downloads")
        for result in results:
            print(f"  - {result['title']} by {result['author']}")
        
        # Example 3: Add a creator for monitoring
        print("\n3. Adding creator for monitoring...")
        
        creator = CreatorProfile(
            id="creator123",
            name="Sample Creator",
            platform=Platform.YOUTUBE,
            channel_url="https://youtube.com/channel/sample",
            avatar_url="https://example.com/avatar.jpg",
            last_check=datetime.now(),
            auto_download=True,
            priority=8,
            description="A sample creator for demonstration"
        )
        
        success = db.add_creator(creator)
        print(f"Creator added successfully: {success}")
        
        # Example 4: Get creators needing check
        print("\n4. Getting creators needing check...")
        creators_to_check = db.get_creators_needing_check(check_interval=0)  # Check all
        print(f"Found {len(creators_to_check)} creators needing check")
        for creator in creators_to_check:
            print(f"  - {creator.name} ({creator.platform.value})")
        
        # Example 5: Settings management
        print("\n5. Managing settings...")
        
        # Set various types of settings
        db.set_setting("app_theme", "dark")
        db.set_setting("max_downloads", 5)
        db.set_setting("auto_update", True)
        db.set_setting("quality_preferences", {"default": "720p", "fallback": "480p"})
        
        # Get settings
        theme = db.get_setting("app_theme")
        max_downloads = db.get_setting("max_downloads")
        auto_update = db.get_setting("auto_update")
        quality_prefs = db.get_setting("quality_preferences")
        
        print(f"Theme: {theme}")
        print(f"Max downloads: {max_downloads}")
        print(f"Auto update: {auto_update}")
        print(f"Quality preferences: {quality_prefs}")
        
        # Example 6: Get statistics
        print("\n6. Database statistics...")
        stats = db.get_download_statistics()
        print(f"Total downloads: {stats['total_downloads']}")
        print(f"Total size: {stats['total_size']} bytes")
        print(f"Downloads by platform: {stats['by_platform']}")
        
        # Example 7: Database info
        print("\n7. Database information...")
        info = db.get_database_info()
        print(f"Database path: {info['path']}")
        print(f"Database size: {info['size']} bytes")
        print(f"Database version: {info['version']}")
        
        print("\nDatabase operations completed successfully!")


if __name__ == "__main__":
    main()