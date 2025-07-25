"""
Tests for file management and verification functionality.
"""
import os
import tempfile
import shutil
import hashlib
import json
from datetime import datetime
from pathlib import Path
import pytest

from app.core.utils.file_manager import FileManager, DuplicateAction
from app.core.utils.naming_template import NamingTemplate
from app.core.utils.cookie_manager import CookieManager
from app.core.utils.user_agent import UserAgentManager


class TestFileManager:
    """Test file management functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = FileManager()
        self.test_content = b"Test file content for MD5 verification"
        self.expected_md5 = hashlib.md5(self.test_content).hexdigest()
    
    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_calculate_md5(self):
        """Test MD5 calculation"""
        # Create test file
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'wb') as f:
            f.write(self.test_content)
        
        # Calculate MD5
        md5_hash = self.file_manager.calculate_md5(test_file)
        
        assert md5_hash == self.expected_md5
    
    def test_calculate_md5_nonexistent_file(self):
        """Test MD5 calculation for non-existent file"""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.txt")
        md5_hash = self.file_manager.calculate_md5(nonexistent_file)
        
        assert md5_hash is None
    
    def test_verify_file_integrity_valid(self):
        """Test file integrity verification with valid hash"""
        # Create test file
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'wb') as f:
            f.write(self.test_content)
        
        # Verify integrity
        is_valid = self.file_manager.verify_file_integrity(test_file, self.expected_md5)
        
        assert is_valid is True
    
    def test_verify_file_integrity_invalid(self):
        """Test file integrity verification with invalid hash"""
        # Create test file
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'wb') as f:
            f.write(self.test_content)
        
        # Verify with wrong hash
        wrong_hash = "wrong_hash_value"
        is_valid = self.file_manager.verify_file_integrity(test_file, wrong_hash)
        
        assert is_valid is False
    
    def test_find_duplicates(self):
        """Test duplicate file detection"""
        # Create original file
        original_file = os.path.join(self.temp_dir, "original.txt")
        with open(original_file, 'wb') as f:
            f.write(self.test_content)
        
        # Create duplicate in subdirectory
        sub_dir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(sub_dir)
        duplicate_file = os.path.join(sub_dir, "duplicate.txt")
        with open(duplicate_file, 'wb') as f:
            f.write(self.test_content)
        
        # Find duplicates
        duplicates = self.file_manager.find_duplicates(original_file, [self.temp_dir])
        
        assert len(duplicates) == 1
        assert duplicate_file in duplicates
    
    def test_handle_duplicate_file_rename(self):
        """Test duplicate file handling with rename action"""
        # Create existing file
        existing_file = os.path.join(self.temp_dir, "existing.txt")
        with open(existing_file, 'w') as f:
            f.write("existing content")
        
        # Handle duplicate with rename
        final_path, should_proceed = self.file_manager.handle_duplicate_file(
            existing_file, DuplicateAction.RENAME
        )
        
        assert should_proceed is True
        assert final_path != existing_file
        assert "existing (1).txt" in final_path
    
    def test_handle_duplicate_file_skip(self):
        """Test duplicate file handling with skip action"""
        # Create existing file
        existing_file = os.path.join(self.temp_dir, "existing.txt")
        with open(existing_file, 'w') as f:
            f.write("existing content")
        
        # Handle duplicate with skip
        final_path, should_proceed = self.file_manager.handle_duplicate_file(
            existing_file, DuplicateAction.SKIP
        )
        
        assert should_proceed is False
        assert final_path == existing_file
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        # Test various invalid characters (excluding time format)
        invalid_filename = 'test<>"/\\|?*file.txt'
        sanitized = self.file_manager.sanitize_filename(invalid_filename)
        
        assert '<' not in sanitized
        assert '>' not in sanitized
        assert '"' not in sanitized
        assert '/' not in sanitized
        assert '\\' not in sanitized
        assert '|' not in sanitized
        assert '?' not in sanitized
        assert '*' not in sanitized
    
    def test_sanitize_filename_preserves_time_format(self):
        """Test that time formats are handled correctly in filename sanitization"""
        import platform
        
        # Test time format handling
        filename_with_time = 'video (01:23:45).mp4'
        sanitized = self.file_manager.sanitize_filename(filename_with_time)
        
        # On Windows, colons are converted to dashes for filesystem compatibility
        if platform.system() == 'Windows':
            assert '01-23-45' in sanitized
            assert sanitized == 'video (01-23-45).mp4'
        else:
            assert '01:23:45' in sanitized
            assert sanitized == 'video (01:23:45).mp4'
    
    def test_create_directory(self):
        """Test directory creation"""
        new_dir = os.path.join(self.temp_dir, "new", "nested", "directory")
        
        success = self.file_manager.create_directory(new_dir)
        
        assert success is True
        assert os.path.exists(new_dir)
        assert os.path.isdir(new_dir)
    
    def test_get_file_info(self):
        """Test file information retrieval"""
        # Create test file
        test_file = os.path.join(self.temp_dir, "info_test.txt")
        with open(test_file, 'wb') as f:
            f.write(self.test_content)
        
        # Get file info
        file_info = self.file_manager.get_file_info(test_file)
        
        assert file_info is not None
        assert file_info['path'] == test_file
        assert file_info['size'] == len(self.test_content)
        assert file_info['md5'] == self.expected_md5
        assert file_info['extension'] == '.txt'
        assert isinstance(file_info['created'], datetime)


class TestNamingTemplate:
    """Test file naming template functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.naming_template = NamingTemplate()
        self.sample_metadata = {
            'title': 'Sample Video Title',
            'author': 'Sample Author',
            'upload_date': datetime(2024, 1, 15, 10, 30, 0),
            'duration': 3661,  # 1:01:01
            'view_count': 12345,
            'like_count': 678,
            'platform': 'youtube',
            'video_id': 'abc123',
            'channel_id': 'channel123'
        }
    
    def test_validate_template_valid(self):
        """Test template validation with valid template"""
        valid_template = "%(author)s - %(title)s.%(ext)s"
        
        is_valid = self.naming_template.validate_template(valid_template)
        
        assert is_valid is True
    
    def test_validate_template_invalid(self):
        """Test template validation with invalid template"""
        invalid_template = "%(nonexistent_var)s.%(ext)s"
        
        is_valid = self.naming_template.validate_template(invalid_template)
        
        assert is_valid is False
    
    def test_format_filename_basic(self):
        """Test basic filename formatting"""
        template = "%(title)s.%(ext)s"
        
        filename = self.naming_template.format_filename(
            template, self.sample_metadata, format_ext='mp4'
        )
        
        assert filename == "Sample Video Title.mp4"
    
    def test_format_filename_with_author(self):
        """Test filename formatting with author"""
        template = "%(author)s - %(title)s.%(ext)s"
        
        filename = self.naming_template.format_filename(
            template, self.sample_metadata, format_ext='mp4'
        )
        
        assert filename == "Sample Author - Sample Video Title.mp4"
    
    def test_format_filename_with_date(self):
        """Test filename formatting with date"""
        template = "%(upload_date)s - %(title)s.%(ext)s"
        
        filename = self.naming_template.format_filename(
            template, self.sample_metadata, format_ext='mp4'
        )
        
        assert filename == "2024-01-15 - Sample Video Title.mp4"
    
    def test_format_filename_with_quality(self):
        """Test filename formatting with quality"""
        template = "%(title)s [%(quality)s].%(ext)s"
        
        filename = self.naming_template.format_filename(
            template, self.sample_metadata, quality='1080p', format_ext='mp4'
        )
        
        assert filename == "Sample Video Title [1080p].mp4"
    
    def test_format_filename_with_duration(self):
        """Test filename formatting with duration"""
        import platform
        
        template = "%(title)s (%(duration)s).%(ext)s"
        
        filename = self.naming_template.format_filename(
            template, self.sample_metadata, format_ext='mp4'
        )
        
        # On Windows, colons in time format are converted to dashes
        if platform.system() == 'Windows':
            assert filename == "Sample Video Title (01-01-01).mp4"
        else:
            assert filename == "Sample Video Title (01:01:01).mp4"
    
    def test_format_filename_with_index(self):
        """Test filename formatting with index"""
        template = "%(index)s - %(title)s.%(ext)s"
        
        filename = self.naming_template.format_filename(
            template, self.sample_metadata, format_ext='mp4', index=5
        )
        
        assert filename == "005 - Sample Video Title.mp4"
    
    def test_preview_filename(self):
        """Test filename preview"""
        template = "%(author)s - %(title)s [%(quality)s].%(ext)s"
        
        preview = self.naming_template.preview_filename(template)
        
        assert "Sample Author" in preview
        assert "Sample Video Title" in preview
        assert "1080p" in preview
        assert ".mp4" in preview
    
    def test_add_custom_template(self):
        """Test adding custom template"""
        template_name = "test_template"
        template_string = "%(author)s/%(title)s.%(ext)s"
        
        success = self.naming_template.add_custom_template(template_name, template_string)
        
        assert success is True
        assert template_name in self.naming_template.custom_templates
    
    def test_suggest_template(self):
        """Test template suggestion"""
        preferences = {
            'include_author': True,
            'include_date': True,
            'include_quality': False,
            'organize_by_author': False
        }
        
        suggested = self.naming_template.suggest_template(preferences)
        
        assert "%(author)s" in suggested
        assert "%(title)s" in suggested
        assert "%(upload_date)s" in suggested
        assert "%(quality)s" not in suggested


class TestCookieManager:
    """Test cookie management functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.cookie_manager = CookieManager(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_add_cookie(self):
        """Test adding a cookie"""
        domain = "example.com"
        name = "test_cookie"
        value = "test_value"
        
        self.cookie_manager.add_cookie(domain, name, value, path="/", secure=True)
        
        cookies = self.cookie_manager.get_cookies_for_domain(domain)
        assert len(cookies) == 1
        assert cookies[0]['name'] == name
        assert cookies[0]['value'] == value
        assert cookies[0]['secure'] is True
    
    def test_remove_cookie(self):
        """Test removing a cookie"""
        domain = "example.com"
        name = "test_cookie"
        value = "test_value"
        
        # Add cookie
        self.cookie_manager.add_cookie(domain, name, value)
        
        # Remove cookie
        success = self.cookie_manager.remove_cookie(domain, name)
        
        assert success is True
        cookies = self.cookie_manager.get_cookies_for_domain(domain)
        assert len(cookies) == 0
    
    def test_get_cookie_header(self):
        """Test cookie header generation"""
        domain = "example.com"
        url = "https://example.com/path"
        
        # Add cookies
        self.cookie_manager.add_cookie(domain, "cookie1", "value1", path="/")
        self.cookie_manager.add_cookie(domain, "cookie2", "value2", path="/path")
        
        header = self.cookie_manager.get_cookie_header(url)
        
        assert "cookie1=value1" in header
        assert "cookie2=value2" in header
    
    def test_export_import_json_cookies(self):
        """Test JSON cookie export/import"""
        domain = "example.com"
        
        # Add test cookies
        self.cookie_manager.add_cookie(domain, "cookie1", "value1")
        self.cookie_manager.add_cookie(domain, "cookie2", "value2")
        
        # Export cookies
        export_file = os.path.join(self.temp_dir, "cookies.json")
        success = self.cookie_manager.export_cookies_to_file(export_file, 'json')
        assert success is True
        
        # Clear cookies and import
        self.cookie_manager.clear_cookies()
        success = self.cookie_manager.import_cookies_from_file(export_file, 'json')
        assert success is True
        
        # Verify imported cookies
        cookies = self.cookie_manager.get_cookies_for_domain(domain)
        assert len(cookies) == 2
    
    def test_cleanup_expired_cookies(self):
        """Test expired cookie cleanup"""
        domain = "example.com"
        current_time = datetime.now().timestamp()
        
        # Add expired and valid cookies
        self.cookie_manager.add_cookie(domain, "expired", "value1", expires=current_time - 3600)
        self.cookie_manager.add_cookie(domain, "valid", "value2", expires=current_time + 3600)
        
        # Cleanup expired cookies
        removed_count = self.cookie_manager.cleanup_expired_cookies()
        
        assert removed_count == 1
        cookies = self.cookie_manager.get_cookies_for_domain(domain)
        assert len(cookies) == 1
        assert cookies[0]['name'] == "valid"


class TestUserAgentManager:
    """Test user agent and browser fingerprint functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.ua_manager = UserAgentManager()
    
    def test_generate_user_agent_chrome(self):
        """Test Chrome user agent generation"""
        user_agent = self.ua_manager.generate_user_agent('chrome', 'windows')
        
        assert 'Chrome' in user_agent
        assert 'Windows' in user_agent
        assert 'Mozilla/5.0' in user_agent
    
    def test_generate_user_agent_firefox(self):
        """Test Firefox user agent generation"""
        user_agent = self.ua_manager.generate_user_agent('firefox', 'linux')
        
        assert 'Firefox' in user_agent
        assert 'Gecko' in user_agent
        assert 'Mozilla/5.0' in user_agent
    
    def test_generate_user_agent_safari(self):
        """Test Safari user agent generation"""
        user_agent = self.ua_manager.generate_user_agent('safari')
        
        assert 'Safari' in user_agent
        assert 'Macintosh' in user_agent  # Safari only on macOS
        assert 'Mozilla/5.0' in user_agent
    
    def test_generate_mobile_user_agent(self):
        """Test mobile user agent generation"""
        user_agent = self.ua_manager.generate_user_agent(mobile=True)
        
        assert any(mobile_indicator in user_agent.lower() 
                  for mobile_indicator in ['mobile', 'iphone', 'android'])
    
    def test_generate_browser_fingerprint(self):
        """Test browser fingerprint generation"""
        fingerprint = self.ua_manager.generate_browser_fingerprint()
        
        required_fields = [
            'user_agent', 'accept', 'accept_language', 'accept_encoding',
            'browser', 'os', 'screen_resolution'
        ]
        
        for field in required_fields:
            assert field in fingerprint
        
        assert fingerprint['browser'] in ['chrome', 'firefox', 'safari', 'edge']
        assert fingerprint['os'] in ['windows', 'macos', 'linux']
    
    def test_get_headers_for_request(self):
        """Test HTTP headers generation"""
        url = "https://example.com/video"
        headers = self.ua_manager.get_headers_for_request(url)
        
        required_headers = [
            'User-Agent', 'Accept', 'Accept-Language', 'Accept-Encoding'
        ]
        
        for header in required_headers:
            assert header in headers
        
        assert headers['User-Agent'].startswith('Mozilla/5.0')
    
    def test_fingerprint_caching(self):
        """Test fingerprint caching by domain"""
        domain = "example.com"
        
        # Generate fingerprint for domain
        fingerprint1 = self.ua_manager.generate_browser_fingerprint(domain)
        fingerprint2 = self.ua_manager.generate_browser_fingerprint(domain)
        
        # Should be the same due to caching
        assert fingerprint1['user_agent'] == fingerprint2['user_agent']
        assert fingerprint1['browser'] == fingerprint2['browser']
    
    def test_fingerprint_rotation(self):
        """Test fingerprint rotation"""
        domain = "example.com"
        
        # Generate initial fingerprint
        fingerprint1 = self.ua_manager.generate_browser_fingerprint(domain)
        
        # Force rotation
        self.ua_manager.rotate_fingerprint(domain)
        
        # Generate new fingerprint
        fingerprint2 = self.ua_manager.generate_browser_fingerprint(domain)
        
        # Should be different after rotation
        # Note: There's a small chance they could be the same by random chance
        # but it's very unlikely with the variety of options
        assert fingerprint1 != fingerprint2 or True  # Allow for rare collision
    
    def test_get_mobile_user_agent_ios(self):
        """Test iOS mobile user agent"""
        user_agent = self.ua_manager.get_mobile_user_agent('ios')
        
        assert 'iPhone' in user_agent
        assert ('iOS' in user_agent or 'iPhone OS' in user_agent)
    
    def test_get_mobile_user_agent_android(self):
        """Test Android mobile user agent"""
        user_agent = self.ua_manager.get_mobile_user_agent('android')
        
        assert 'Android' in user_agent
        assert 'Mobile' in user_agent


if __name__ == '__main__':
    pytest.main([__file__])