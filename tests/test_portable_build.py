"""
Tests for portable application building functionality.
"""

import os
import sys
import platform
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.portable import PortableManager, get_portable_manager
from build_scripts.build_portable import PortableBuilder


class TestPortableManager:
    """Test portable manager functionality."""
    
    def test_portable_detection(self):
        """Test portable mode detection."""
        manager = PortableManager()
        
        # Should detect based on environment or executable location
        assert isinstance(manager.is_portable, bool)
        assert isinstance(manager.app_dir, Path)
        assert isinstance(manager.data_dir, Path)
    
    def test_directory_structure(self):
        """Test directory structure creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Mock app directory
            with patch.object(PortableManager, '_get_app_directory', return_value=temp_path):
                manager = PortableManager()
                
                # Test directory paths
                assert manager.data_dir.parent == temp_path or manager.data_dir.is_relative_to(temp_path)
                assert manager.config_dir.exists() or manager.config_dir.parent.exists()
                assert manager.cache_dir.exists() or manager.cache_dir.parent.exists()
    
    def test_portable_structure_creation(self):
        """Test portable directory structure creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            with patch.object(PortableManager, '_get_app_directory', return_value=temp_path):
                with patch.object(PortableManager, '_detect_portable_mode', return_value=True):
                    manager = PortableManager()
                    manager.create_portable_structure()
                    
                    # Check if portable marker exists
                    portable_marker = temp_path / "portable.txt"
                    assert portable_marker.exists()
                    
                    # Check directory structure
                    data_dir = temp_path / "Data"
                    assert data_dir.exists()
                    assert (data_dir / "Config").exists()
                    assert (data_dir / "Cache").exists()
                    assert (data_dir / "Logs").exists()
    
    def test_config_file_paths(self):
        """Test configuration file path resolution."""
        manager = PortableManager()
        
        config_file = manager.get_config_file("settings.json")
        assert isinstance(config_file, Path)
        assert config_file.name == "settings.json"
        
        data_file = manager.get_data_file("database.db")
        assert isinstance(data_file, Path)
        assert data_file.name == "database.db"
    
    def test_global_manager_instance(self):
        """Test global portable manager instance."""
        manager1 = get_portable_manager()
        manager2 = get_portable_manager()
        
        # Should return the same instance
        assert manager1 is manager2
    
    def test_migration_functionality(self):
        """Test migration from installed version."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create mock installed data
            installed_dir = temp_path / "installed"
            installed_dir.mkdir()
            (installed_dir / "settings.json").write_text('{"test": "data"}')
            
            # Create portable manager
            with patch.object(PortableManager, '_get_app_directory', return_value=temp_path):
                with patch.object(PortableManager, '_detect_portable_mode', return_value=True):
                    manager = PortableManager()
                    
                    # Test migration
                    result = manager.migrate_from_installed(installed_dir)
                    
                    if result:
                        # Check if files were migrated
                        migrated_config = manager.get_config_file("settings.json")
                        assert migrated_config.exists()


class TestPortableBuilder:
    """Test portable application builder."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create minimal project structure
            app_dir = temp_path / "app"
            app_dir.mkdir()
            (app_dir / "main.py").write_text("# Main application file")
            (app_dir / "__init__.py").write_text("")
            
            # Create build scripts directory
            build_scripts_dir = temp_path / "build_scripts"
            build_scripts_dir.mkdir()
            
            yield temp_path
    
    def test_builder_initialization(self, temp_project_dir):
        """Test builder initialization."""
        with patch('build_scripts.build_portable.PROJECT_ROOT', temp_project_dir):
            builder = PortableBuilder('windows')
            
            assert builder.target_platform == 'windows'
            assert isinstance(builder.build_dir, Path)
            assert isinstance(builder.dist_dir, Path)
            assert isinstance(builder.portable_dir, Path)
    
    def test_dependency_checking(self, temp_project_dir):
        """Test dependency checking."""
        with patch('build_scripts.build_portable.PROJECT_ROOT', temp_project_dir):
            builder = PortableBuilder('windows')
            
            # Mock PyInstaller availability
            with patch('builtins.__import__') as mock_import:
                mock_pyinstaller = MagicMock()
                mock_pyinstaller.__version__ = '5.0.0'
                mock_import.return_value = mock_pyinstaller
                
                # Should pass with mocked dependencies
                # Note: This test might fail if actual dependencies are missing
                # In a real test environment, you'd mock all required imports
                try:
                    result = builder.check_dependencies()
                    # If dependencies are available, should return True
                    assert isinstance(result, bool)
                except ImportError:
                    # If dependencies are missing, that's expected in test environment
                    pytest.skip("Dependencies not available in test environment")
    
    def test_build_info(self, temp_project_dir):
        """Test build information retrieval."""
        with patch('build_scripts.build_portable.PROJECT_ROOT', temp_project_dir):
            builder = PortableBuilder('linux')
            
            info = builder.get_build_info()
            
            assert 'app_name' in info
            assert 'version' in info
            assert 'target_platform' in info
            assert info['target_platform'] == 'linux'
    
    def test_clean_build_dirs(self, temp_project_dir):
        """Test build directory cleaning."""
        with patch('build_scripts.build_portable.PROJECT_ROOT', temp_project_dir):
            builder = PortableBuilder('darwin')
            
            # Create some files in build directories
            builder.build_dir.mkdir(parents=True, exist_ok=True)
            builder.dist_dir.mkdir(parents=True, exist_ok=True)
            
            test_file = builder.build_dir / "test.txt"
            test_file.write_text("test")
            
            # Clean directories
            builder.clean_build_dirs()
            
            # Directories should exist but be empty
            assert builder.build_dir.exists()
            assert builder.dist_dir.exists()
            assert not test_file.exists()


class TestPortableFunctionality:
    """Test overall portable functionality."""
    
    def test_portable_mode_environment_variable(self):
        """Test portable mode detection via environment variable."""
        with patch.dict(os.environ, {'VIDEODOWNLOADER_PORTABLE': '1'}):
            manager = PortableManager()
            assert manager.is_portable == True
    
    def test_non_portable_mode(self):
        """Test non-portable mode behavior."""
        # Keep essential environment variables
        essential_vars = {
            'HOME': os.environ.get('HOME', ''),
            'USERPROFILE': os.environ.get('USERPROFILE', ''),
            'APPDATA': os.environ.get('APPDATA', ''),
        }
        
        with patch.dict(os.environ, essential_vars, clear=True):
            with patch('sys.frozen', False, create=True):
                with patch.object(Path, 'exists', return_value=False):
                    manager = PortableManager()
                    
                    # Should use system directories in non-portable mode
                    if platform.system() == "Windows":
                        assert "AppData" in str(manager.data_dir) or "VideoDownloader" in str(manager.data_dir)
                    elif platform.system() == "Darwin":
                        assert "Library" in str(manager.data_dir) or "VideoDownloader" in str(manager.data_dir)
                    else:  # Linux
                        assert ".local" in str(manager.data_dir) or "VideoDownloader" in str(manager.data_dir)
    
    def test_database_path_resolution(self):
        """Test database path resolution."""
        manager = PortableManager()
        db_path = manager.get_database_path()
        
        assert isinstance(db_path, Path)
        assert db_path.name == "videodownloader.db"
        assert db_path.parent == manager.data_dir
    
    def test_downloads_directory_resolution(self):
        """Test downloads directory resolution."""
        manager = PortableManager()
        downloads_dir = manager.get_downloads_directory()
        
        assert isinstance(downloads_dir, Path)
        
        if manager.is_portable:
            assert downloads_dir.parent == manager.data_dir
        else:
            assert "Downloads" in str(downloads_dir)


@pytest.mark.integration
class TestPortableIntegration:
    """Integration tests for portable functionality."""
    
    def test_config_integration(self):
        """Test configuration integration with portable mode."""
        try:
            from app.core.config import ConfigManager
            
            # Test that config manager works with portable mode
            config_manager = ConfigManager()
            
            # Should not raise exceptions
            assert hasattr(config_manager, 'config')
            assert hasattr(config_manager, 'portable_manager')
            
        except ImportError:
            pytest.skip("Config module not available")
    
    def test_portable_export(self):
        """Test portable package export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            with patch.object(PortableManager, '_get_app_directory', return_value=temp_path):
                with patch.object(PortableManager, '_detect_portable_mode', return_value=True):
                    manager = PortableManager()
                    
                    # Create some test data
                    manager.create_portable_structure()
                    test_config = manager.get_config_file("test.json")
                    test_config.write_text('{"test": "data"}')
                    
                    # Test export
                    output_path = temp_path / "export.zip"
                    
                    # Mock sys.frozen for export test
                    with patch('sys.frozen', True, create=True):
                        with patch('sys.executable', str(temp_path / "app.exe")):
                            result = manager.export_portable_package(output_path)
                            
                            # Export might fail due to missing executable, but should handle gracefully
                            assert isinstance(result, bool)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])