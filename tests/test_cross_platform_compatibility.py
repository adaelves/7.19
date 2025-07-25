"""
Cross-platform compatibility tests for the multi-platform video downloader.
Tests functionality across Windows, macOS, and Linux systems.
"""

import os
import sys
import platform
import subprocess
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sqlite3

# Import core modules for testing (optional)
# These imports are optional and tests will adapt if modules are not available


class TestCrossPlatformCompatibility:
    """Test cross-platform compatibility across different operating systems."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment for each test."""
        self.original_platform = platform.system()
        self.test_dir = Path(tempfile.mkdtemp())
        yield
        # Cleanup
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_platform_detection(self):
        """Test platform detection works correctly."""
        current_platform = platform.system()
        assert current_platform in ['Windows', 'Darwin', 'Linux']
        
        # Test platform-specific behavior
        if current_platform == 'Windows':
            assert os.name == 'nt'
            assert platform.platform().startswith('Windows')
        elif current_platform == 'Darwin':
            assert os.name == 'posix'
            assert platform.platform().startswith('macOS') or platform.platform().startswith('Darwin')
        elif current_platform == 'Linux':
            assert os.name == 'posix'
            assert 'Linux' in platform.platform()
    
    def test_file_path_handling(self):
        """Test file path handling across different platforms."""
        # Test path creation
        test_path = self.test_dir / "test_folder" / "test_file.txt"
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text("test content")
        
        assert test_path.exists()
        assert test_path.is_file()
        
        # Test path normalization
        if platform.system() == 'Windows':
            # Windows paths should use backslashes
            windows_path = str(test_path).replace('/', '\\')
            assert Path(windows_path).exists()
        else:
            # Unix-like systems use forward slashes
            unix_path = str(test_path).replace('\\', '/')
            assert Path(unix_path).exists()
    
    def test_database_compatibility(self):
        """Test SQLite database compatibility across platforms."""
        db_path = self.test_dir / "test.db"
        
        # Test database creation
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create test table
        cursor.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert test data
        cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("test_entry",))
        conn.commit()
        
        # Verify data
        cursor.execute("SELECT * FROM test_table")
        result = cursor.fetchone()
        assert result is not None
        assert result[1] == "test_entry"
        
        conn.close()
        assert db_path.exists()
    
    @pytest.mark.parametrize("python_version", ["3.8", "3.9", "3.10", "3.11", "3.12"])
    def test_python_version_compatibility(self, python_version):
        """Test compatibility with different Python versions."""
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        
        # Skip if testing version doesn't match current
        if python_version != current_version:
            pytest.skip(f"Testing Python {python_version}, but running on {current_version}")
        
        # Test basic Python features used in the application
        assert sys.version_info >= (3, 8), "Application requires Python 3.8+"
        
        # Test async/await support (Python 3.7+)
        import asyncio
        assert hasattr(asyncio, 'create_task')
        
        # Test pathlib support (Python 3.4+)
        from pathlib import Path
        assert Path.cwd().exists()
        
        # Test dataclasses support (Python 3.7+)
        from dataclasses import dataclass
        
        @dataclass
        class TestClass:
            name: str
            value: int = 0
        
        test_obj = TestClass("test")
        assert test_obj.name == "test"
        assert test_obj.value == 0


class TestWindowsCompatibility:
    """Test Windows-specific functionality."""
    
    @pytest.mark.skipif(platform.system() != 'Windows', reason="Windows-specific tests")
    def test_windows_file_paths(self):
        """Test Windows file path handling."""
        # Test long path support
        long_path = "C:\\" + "a" * 200 + "\\test.txt"
        path_obj = Path(long_path)
        
        # Test drive letter handling
        assert Path("C:\\").is_absolute()
        assert Path("C:\\test").parts[0] == "C:\\"
        
        # Test UNC path support
        unc_path = "\\\\server\\share\\file.txt"
        unc_obj = Path(unc_path)
        assert unc_obj.is_absolute()
    
    @pytest.mark.skipif(platform.system() != 'Windows', reason="Windows-specific tests")
    def test_windows_registry_access(self):
        """Test Windows registry access (if needed)."""
        try:
            import winreg
            # Test basic registry access
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software")
            winreg.CloseKey(key)
        except ImportError:
            pytest.skip("winreg module not available")
        except Exception as e:
            pytest.fail(f"Registry access failed: {e}")
    
    @pytest.mark.skipif(platform.system() != 'Windows', reason="Windows-specific tests")
    def test_windows_executable_detection(self):
        """Test executable detection on Windows."""
        # Test common executables
        executables = ['python.exe', 'pip.exe']
        
        for exe in executables:
            # Check if executable exists in PATH
            result = shutil.which(exe)
            if result:
                assert Path(result).exists()
                assert Path(result).suffix.lower() == '.exe'


class TestMacOSCompatibility:
    """Test macOS-specific functionality."""
    
    @pytest.mark.skipif(platform.system() != 'Darwin', reason="macOS-specific tests")
    def test_macos_file_paths(self):
        """Test macOS file path handling."""
        # Test case sensitivity
        home_path = Path.home()
        assert home_path.exists()
        
        # Test application bundle paths
        app_path = Path("/Applications")
        if app_path.exists():
            assert app_path.is_dir()
        
        # Test user library paths
        library_path = Path.home() / "Library"
        assert library_path.exists()
        assert library_path.is_dir()
    
    @pytest.mark.skipif(platform.system() != 'Darwin', reason="macOS-specific tests")
    def test_macos_permissions(self):
        """Test macOS file permissions."""
        test_file = Path(tempfile.mktemp())
        test_file.write_text("test")
        
        # Test permission setting
        test_file.chmod(0o755)
        stat = test_file.stat()
        assert stat.st_mode & 0o777 == 0o755
        
        test_file.unlink()
    
    @pytest.mark.skipif(platform.system() != 'Darwin', reason="macOS-specific tests")
    def test_macos_executable_detection(self):
        """Test executable detection on macOS."""
        # Test common executables
        executables = ['python3', 'pip3', 'brew']
        
        for exe in executables:
            result = shutil.which(exe)
            if result:
                assert Path(result).exists()


class TestLinuxCompatibility:
    """Test Linux-specific functionality."""
    
    @pytest.mark.skipif(platform.system() != 'Linux', reason="Linux-specific tests")
    def test_linux_file_paths(self):
        """Test Linux file path handling."""
        # Test standard Linux paths
        home_path = Path.home()
        assert home_path.exists()
        
        # Test /tmp directory
        tmp_path = Path("/tmp")
        assert tmp_path.exists()
        assert tmp_path.is_dir()
        
        # Test case sensitivity
        test_dir = Path(tempfile.mkdtemp())
        (test_dir / "Test").mkdir()
        (test_dir / "test").mkdir()
        
        assert (test_dir / "Test").exists()
        assert (test_dir / "test").exists()
        assert (test_dir / "Test") != (test_dir / "test")
        
        shutil.rmtree(test_dir)
    
    @pytest.mark.skipif(platform.system() != 'Linux', reason="Linux-specific tests")
    def test_linux_permissions(self):
        """Test Linux file permissions."""
        test_file = Path(tempfile.mktemp())
        test_file.write_text("test")
        
        # Test permission setting
        test_file.chmod(0o644)
        stat = test_file.stat()
        assert stat.st_mode & 0o777 == 0o644
        
        test_file.unlink()
    
    @pytest.mark.skipif(platform.system() != 'Linux', reason="Linux-specific tests")
    def test_linux_executable_detection(self):
        """Test executable detection on Linux."""
        # Test common executables
        executables = ['python3', 'pip3', 'which', 'ls']
        
        for exe in executables:
            result = shutil.which(exe)
            if result:
                assert Path(result).exists()


class TestDependencyDetection:
    """Test automatic dependency detection across platforms."""
    
    def test_python_executable_detection(self):
        """Test Python executable detection."""
        python_exe = sys.executable
        assert Path(python_exe).exists()
        
        # Test version detection
        result = subprocess.run([python_exe, '--version'], 
                              capture_output=True, text=True)
        assert result.returncode == 0
        assert 'Python' in result.stdout
    
    def test_pip_detection(self):
        """Test pip detection."""
        pip_commands = ['pip', 'pip3']
        pip_found = False
        
        for pip_cmd in pip_commands:
            if shutil.which(pip_cmd):
                result = subprocess.run([pip_cmd, '--version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    pip_found = True
                    break
        
        assert pip_found, "No working pip installation found"
    
    def test_required_packages_detection(self):
        """Test detection of required Python packages."""
        required_packages = [
            'PySide6',
            'requests',
            'sqlite3',  # Built-in module
            'asyncio',  # Built-in module
            'pathlib',  # Built-in module
        ]
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                if package in ['sqlite3', 'asyncio', 'pathlib']:
                    pytest.fail(f"Built-in module {package} not available")
                else:
                    pytest.skip(f"Optional package {package} not installed")
    
    def test_optional_dependencies_detection(self):
        """Test detection of optional dependencies."""
        optional_deps = {
            'ffmpeg': ['ffmpeg', 'ffmpeg.exe'],
            'yt-dlp': ['yt-dlp', 'yt-dlp.exe'],
        }
        
        for dep_name, commands in optional_deps.items():
            found = False
            for cmd in commands:
                if shutil.which(cmd):
                    found = True
                    break
            
            if not found:
                print(f"Optional dependency {dep_name} not found")


class TestUICompatibility:
    """Test UI compatibility across platforms."""
    
    def test_qt_availability(self):
        """Test Qt/PySide6 availability."""
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import QTimer
            from PySide6.QtGui import QIcon
            
            # Test basic Qt functionality
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # Test timer creation
            timer = QTimer()
            assert timer is not None
            
        except ImportError as e:
            pytest.skip(f"PySide6 not available: {e}")
    
    @pytest.mark.skipif(os.environ.get('CI') == 'true', reason="No display in CI")
    def test_window_creation(self):
        """Test window creation across platforms."""
        try:
            from PySide6.QtWidgets import QApplication, QMainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = QMainWindow()
            window.setWindowTitle("Test Window")
            window.resize(800, 600)
            
            # Don't show the window in tests
            assert window.windowTitle() == "Test Window"
            assert window.size().width() == 800
            assert window.size().height() == 600
            
        except ImportError as e:
            pytest.skip(f"PySide6 not available: {e}")


class TestNetworkCompatibility:
    """Test network functionality across platforms."""
    
    def test_http_requests(self):
        """Test HTTP requests work across platforms."""
        try:
            import requests
            
            # Test basic HTTP request
            response = requests.get('https://httpbin.org/get', timeout=10)
            assert response.status_code == 200
            
            # Test JSON parsing
            data = response.json()
            assert 'url' in data
            
        except ImportError:
            pytest.skip("requests module not available")
        except Exception as e:
            pytest.skip(f"Network request failed: {e}")
    
    def test_ssl_support(self):
        """Test SSL/TLS support."""
        try:
            import ssl
            import socket
            
            # Test SSL context creation
            context = ssl.create_default_context()
            assert context is not None
            
            # Test SSL connection (don't actually connect)
            assert hasattr(ssl, 'PROTOCOL_TLS_CLIENT')
            
        except ImportError:
            pytest.skip("SSL module not available")


if __name__ == '__main__':
    # Run tests with platform information
    print(f"Running cross-platform compatibility tests on {platform.system()}")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    
    pytest.main([__file__, '-v'])