"""
Demonstration of file management and verification features.
Shows how to use MD5 verification, naming templates, cookie management, and user agent spoofing.
"""
import os
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# Add the project root to the path so we can import from app
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our file management utilities
from app.core.utils.file_manager import file_manager, DuplicateAction
from app.core.utils.naming_template import naming_template
from app.core.utils.cookie_manager import cookie_manager
from app.core.utils.user_agent import user_agent_manager


def demo_file_verification():
    """Demonstrate MD5 file verification and duplicate detection"""
    print("=== File Verification Demo ===")
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    print(f"Working in: {temp_dir}")
    
    try:
        # Create a test file
        test_content = b"This is a test video file content"
        original_file = os.path.join(temp_dir, "original_video.mp4")
        
        with open(original_file, 'wb') as f:
            f.write(test_content)
        
        # Calculate MD5 hash
        md5_hash = file_manager.calculate_md5(original_file)
        print(f"Original file MD5: {md5_hash}")
        
        # Verify file integrity
        is_valid = file_manager.verify_file_integrity(original_file, md5_hash)
        print(f"File integrity check: {'PASSED' if is_valid else 'FAILED'}")
        
        # Create a duplicate file
        duplicate_file = os.path.join(temp_dir, "duplicate_video.mp4")
        shutil.copy2(original_file, duplicate_file)
        
        # Find duplicates
        duplicates = file_manager.find_duplicates(original_file, [temp_dir])
        print(f"Found {len(duplicates)} duplicate(s): {duplicates}")
        
        # Handle duplicate with rename action
        target_path = os.path.join(temp_dir, "new_video.mp4")
        shutil.copy2(original_file, target_path)  # Create existing file
        
        final_path, should_proceed = file_manager.handle_duplicate_file(
            target_path, DuplicateAction.RENAME
        )
        print(f"Duplicate handling: {target_path} -> {final_path} (proceed: {should_proceed})")
        
        # Get file information
        file_info = file_manager.get_file_info(original_file)
        print(f"File info: {file_info['size']} bytes, created: {file_info['created']}")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print("Cleanup completed\n")


def demo_naming_templates():
    """Demonstrate file naming template system"""
    print("=== Naming Template Demo ===")
    
    # Sample video metadata
    sample_metadata = {
        'title': 'Amazing Cat Video Compilation',
        'author': 'CatLover123',
        'upload_date': datetime(2024, 1, 15, 14, 30, 0),
        'duration': 3661,  # 1:01:01
        'view_count': 1234567,
        'like_count': 98765,
        'platform': 'youtube',
        'video_id': 'abc123xyz',
        'channel_id': 'UC_CatChannel'
    }
    
    # Test different templates
    templates = {
        'Simple': '%(title)s.%(ext)s',
        'With Author': '%(author)s - %(title)s.%(ext)s',
        'With Date': '%(upload_date)s - %(title)s.%(ext)s',
        'With Quality': '%(title)s [%(quality)s].%(ext)s',
        'With Duration': '%(title)s (%(duration)s).%(ext)s',
        'Full Info': '%(author)s - %(title)s [%(quality)s] (%(upload_date)s).%(ext)s',
        'Organized': '%(author)s/%(upload_date)s - %(title)s.%(ext)s'
    }
    
    for name, template in templates.items():
        filename = naming_template.format_filename(
            template, sample_metadata, quality='1080p', format_ext='mp4'
        )
        print(f"{name:12}: {filename}")
    
    # Test template validation
    valid_template = "%(author)s - %(title)s.%(ext)s"
    invalid_template = "%(nonexistent)s.%(ext)s"
    
    print(f"\nTemplate validation:")
    print(f"'{valid_template}' is valid: {naming_template.validate_template(valid_template)}")
    print(f"'{invalid_template}' is valid: {naming_template.validate_template(invalid_template)}")
    
    # Add custom template
    custom_name = "my_template"
    custom_template = "%(platform)s_%(video_id)s_%(title)s.%(ext)s"
    success = naming_template.add_custom_template(custom_name, custom_template)
    print(f"\nAdded custom template '{custom_name}': {success}")
    
    if success:
        custom_filename = naming_template.format_filename(
            custom_template, sample_metadata, format_ext='mp4'
        )
        print(f"Custom template result: {custom_filename}")
    
    print()


def demo_cookie_management():
    """Demonstrate cookie management functionality"""
    print("=== Cookie Management Demo ===")
    
    # Create temporary directory for cookie storage
    temp_dir = tempfile.mkdtemp()
    temp_cookie_manager = cookie_manager.__class__(temp_dir)
    
    try:
        # Add some test cookies
        domains = ['youtube.com', 'bilibili.com', 'tiktok.com']
        
        for i, domain in enumerate(domains):
            temp_cookie_manager.add_cookie(
                domain, 
                f'session_id', 
                f'session_value_{i}',
                path='/',
                secure=True,
                expires=datetime.now().timestamp() + 3600  # 1 hour from now
            )
            temp_cookie_manager.add_cookie(
                domain,
                f'user_pref',
                f'pref_value_{i}',
                path='/',
                httpOnly=True
            )
        
        # Show cookie summary
        summary = temp_cookie_manager.get_cookie_summary()
        print(f"Cookie summary: {summary}")
        
        # Get cookies for specific domain
        youtube_cookies = temp_cookie_manager.get_cookies_for_domain('youtube.com')
        print(f"YouTube cookies: {len(youtube_cookies)} found")
        
        # Generate cookie header for a URL
        test_url = "https://youtube.com/watch?v=test123"
        cookie_header = temp_cookie_manager.get_cookie_header(test_url)
        print(f"Cookie header for {test_url}:")
        print(f"  {cookie_header}")
        
        # Export cookies to JSON
        export_file = os.path.join(temp_dir, "exported_cookies.json")
        success = temp_cookie_manager.export_cookies_to_file(export_file, 'json')
        print(f"\nExported cookies to JSON: {success}")
        
        if success and os.path.exists(export_file):
            file_size = os.path.getsize(export_file)
            print(f"Export file size: {file_size} bytes")
        
        # Test cookie cleanup
        removed_count = temp_cookie_manager.cleanup_expired_cookies()
        print(f"Cleaned up {removed_count} expired cookies")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print("Cookie demo cleanup completed\n")


def demo_user_agent_spoofing():
    """Demonstrate browser fingerprint spoofing"""
    print("=== User Agent Spoofing Demo ===")
    
    # Generate different types of user agents
    browsers = ['chrome', 'firefox', 'safari', 'edge']
    operating_systems = ['windows', 'macos', 'linux']
    
    print("Generated User-Agents:")
    for browser in browsers:
        for os_type in operating_systems:
            # Skip invalid combinations
            if browser == 'safari' and os_type != 'macos':
                continue
            
            user_agent = user_agent_manager.generate_user_agent(browser, os_type)
            print(f"  {browser:7} on {os_type:7}: {user_agent[:80]}...")
    
    # Generate mobile user agents
    print("\nMobile User-Agents:")
    ios_ua = user_agent_manager.get_mobile_user_agent('ios')
    android_ua = user_agent_manager.get_mobile_user_agent('android')
    print(f"  iOS:     {ios_ua[:80]}...")
    print(f"  Android: {android_ua[:80]}...")
    
    # Generate complete browser fingerprint
    print("\nBrowser Fingerprint:")
    fingerprint = user_agent_manager.generate_browser_fingerprint('example.com')
    
    important_fields = ['user_agent', 'accept_language', 'browser', 'os', 'screen_resolution']
    for field in important_fields:
        value = fingerprint.get(field, 'N/A')
        if field == 'user_agent':
            value = f"{value[:60]}..."
        print(f"  {field:16}: {value}")
    
    # Generate HTTP headers for a request
    print("\nHTTP Headers for Request:")
    test_url = "https://youtube.com/watch?v=test123"
    headers = user_agent_manager.get_headers_for_request(test_url)
    
    for header, value in headers.items():
        if len(value) > 60:
            value = f"{value[:60]}..."
        print(f"  {header:20}: {value}")
    
    # Test fingerprint caching and rotation
    print(f"\nFingerprint caching:")
    fingerprint1 = user_agent_manager.generate_browser_fingerprint('test.com')
    fingerprint2 = user_agent_manager.generate_browser_fingerprint('test.com')
    print(f"  Same fingerprint cached: {fingerprint1['user_agent'] == fingerprint2['user_agent']}")
    
    user_agent_manager.rotate_fingerprint('test.com')
    fingerprint3 = user_agent_manager.generate_browser_fingerprint('test.com')
    print(f"  Different after rotation: {fingerprint1['user_agent'] != fingerprint3['user_agent']}")
    
    print()


def demo_integration():
    """Demonstrate how all components work together"""
    print("=== Integration Demo ===")
    
    # Simulate a download scenario
    video_metadata = {
        'title': 'How to Train Your Dragon - Best Scenes',
        'author': 'MovieClips',
        'upload_date': datetime(2024, 1, 20, 16, 45, 0),
        'duration': 1847,  # 30:47
        'view_count': 5432109,
        'platform': 'youtube',
        'video_id': 'dQw4w9WgXcQ'
    }
    
    # 1. Generate appropriate filename using template
    template = "%(author)s - %(title)s [%(quality)s] (%(duration)s).%(ext)s"
    filename = naming_template.format_filename(
        template, video_metadata, quality='1080p', format_ext='mp4'
    )
    print(f"Generated filename: {filename}")
    
    # 2. Sanitize filename for filesystem
    safe_filename = file_manager.sanitize_filename(filename)
    print(f"Safe filename: {safe_filename}")
    
    # 3. Generate browser fingerprint for the download
    domain = 'youtube.com'
    fingerprint = user_agent_manager.generate_browser_fingerprint(domain)
    print(f"Browser fingerprint: {fingerprint['browser']} on {fingerprint['os']}")
    
    # 4. Get HTTP headers for the request
    video_url = f"https://youtube.com/watch?v={video_metadata['video_id']}"
    headers = user_agent_manager.get_headers_for_request(video_url)
    print(f"User-Agent: {headers['User-Agent'][:60]}...")
    
    # 5. Get cookies for the domain
    cookies = cookie_manager.get_cookies_for_domain(domain)
    cookie_header = cookie_manager.get_cookie_header(video_url)
    print(f"Cookies available: {len(cookies)} cookies")
    if cookie_header:
        print(f"Cookie header: {cookie_header[:60]}...")
    else:
        print("Cookie header: (no cookies)")
    
    # 6. Simulate file verification after download
    temp_dir = tempfile.mkdtemp()
    try:
        # Create mock downloaded file
        download_path = os.path.join(temp_dir, safe_filename)
        mock_content = b"Mock video file content for demonstration"
        
        with open(download_path, 'wb') as f:
            f.write(mock_content)
        
        # Calculate and verify MD5
        md5_hash = file_manager.calculate_md5(download_path)
        print(f"Downloaded file MD5: {md5_hash}")
        
        # Verify integrity
        is_valid = file_manager.verify_file_integrity(download_path, md5_hash)
        print(f"File integrity: {'VERIFIED' if is_valid else 'FAILED'}")
        
        # Get file info
        file_info = file_manager.get_file_info(download_path)
        print(f"File size: {file_info['size']} bytes")
        print(f"Created: {file_info['created']}")
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("Integration demo completed\n")


def main():
    """Run all demonstrations"""
    print("File Management and Verification System Demo")
    print("=" * 50)
    
    demo_file_verification()
    demo_naming_templates()
    demo_cookie_management()
    demo_user_agent_spoofing()
    demo_integration()
    
    print("All demonstrations completed successfully!")


if __name__ == '__main__':
    main()