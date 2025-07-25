#!/usr/bin/env python3
"""
Portable application demonstration script.
Shows how the portable functionality works.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.portable import get_portable_manager


def main():
    """Demonstrate portable functionality."""
    print("VideoDownloader Portable Mode Demonstration")
    print("=" * 50)
    
    # Get portable manager
    manager = get_portable_manager()
    
    # Display portable information
    print(f"Portable Mode: {'✓ Enabled' if manager.is_portable else '✗ Disabled'}")
    print(f"Application Directory: {manager.app_dir}")
    print(f"Data Directory: {manager.data_dir}")
    print(f"Configuration Directory: {manager.config_dir}")
    print(f"Cache Directory: {manager.cache_dir}")
    print(f"Logs Directory: {manager.logs_dir}")
    print()
    
    # Show file paths
    print("File Path Examples:")
    print("-" * 20)
    print(f"Settings File: {manager.get_config_file('settings.json')}")
    print(f"Database File: {manager.get_database_path()}")
    print(f"Downloads Directory: {manager.get_downloads_directory()}")
    print(f"Log File: {manager.get_log_file('app.log')}")
    print()
    
    # Show portable info
    info = manager.get_info()
    print("Detailed Information:")
    print("-" * 20)
    for key, value in info.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    print()
    
    # Demonstrate portable structure creation
    if manager.is_portable:
        print("Creating portable directory structure...")
        try:
            manager.create_portable_structure()
            print("✓ Portable structure created successfully")
            
            # List created directories
            data_dirs = [d for d in manager.data_dir.iterdir() if d.is_dir()]
            if data_dirs:
                print("Created directories:")
                for directory in sorted(data_dirs):
                    print(f"  - {directory.name}")
            
        except Exception as e:
            print(f"✗ Failed to create portable structure: {e}")
    else:
        print("Not in portable mode - using system directories")
    
    print()
    
    # Show environment detection
    print("Environment Detection:")
    print("-" * 20)
    print(f"Frozen executable: {getattr(sys, 'frozen', False)}")
    print(f"Executable path: {sys.executable}")
    print(f"Script path: {__file__}")
    
    # Check for portable markers
    portable_markers = [
        manager.app_dir / "portable.txt",
        manager.app_dir / ".portable",
        manager.app_dir / "Data",
    ]
    
    print("\nPortable Markers:")
    for marker in portable_markers:
        exists = marker.exists()
        print(f"  {marker.name}: {'✓' if exists else '✗'}")
    
    # Environment variables
    env_vars = [
        'VIDEODOWNLOADER_PORTABLE',
        'APPDATA',
        'HOME',
        'XDG_DATA_HOME',
        'XDG_CONFIG_HOME',
    ]
    
    print("\nEnvironment Variables:")
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        print(f"  {var}: {value}")
    
    print("\n" + "=" * 50)
    print("Demonstration completed!")


if __name__ == '__main__':
    main()