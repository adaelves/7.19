"""
Tests for the update system functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
from datetime import datetime

from app.services.update_service import UpdateService, ReleaseInfo, UpdateProgress
from app.services.config_service import ConfigService
from app.core.updater import AutoUpdater, UpdateManager


class TestUpdateService:
    """Test cases for UpdateService"""
    
    @pytest.fixture
    def config_service(self):
        """Mock config service"""
        config = Mock(spec=ConfigService)
        config.get.return_value = True
        config.set.return_value = None
        return config
    
    @pytest.fixture
    def update_service(self, config_service):
        """Create UpdateService instance"""
        service = UpdateService(config_service)
        service.github_repo = "test-user/test-repo"
        return service
    
    def test_get_current_version(self, update_service):
        """Test getting current version"""
        # Test with version file
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.read_text', return_value="1.2.3\n"):
                version = update_service._get_current_version()
                assert version == "1.2.3"
    
    def test_get_platform_name(self, update_service):
        """Test platform name detection"""
        with patch('platform.system', return_value='Windows'):
            assert update_service._get_platform_name() == "windows"
        
        with patch('platform.system', return_value='Darwin'):
            assert update_service._get_platform_name() == "macos"
        
        with patch('platform.system', return_value='Linux'):
            assert update_service._get_platform_name() == "linux"
    
    def test_is_newer_version(self, update_service):
        """Test version comparison"""
        assert update_service._is_newer_version("1.2.0", "1.1.0") == True
        assert update_service._is_newer_version("1.1.0", "1.2.0") == False
        assert update_service._is_newer_version("1.1.0", "1.1.0") == False
        assert update_service._is_newer_version("2.0.0", "1.9.9") == True
    
    @pytest.mark.asyncio
    async def test_check_for_updates_no_update(self, update_service):
        """Test checking for updates when no update available"""
        mock_response_data = {
            "tag_name": "v1.0.0",
            "published_at": "2025-01-21T10:00:00Z",
            "body": "Test release",
            "assets": [
                {
                    "name": "test-windows.zip",
                    "browser_download_url": "https://example.com/test.zip",
                    "size": 1024
                }
            ],
            "prerelease": False
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            # Mock current version to be same as remote
            update_service.current_version = "1.0.0"
            
            result = await update_service.check_for_updates(force=True)
            assert result is None
    
    @pytest.mark.asyncio
    async def test_check_for_updates_with_update(self, update_service):
        """Test checking for updates when update is available"""
        mock_response_data = {
            "tag_name": "v1.1.0",
            "published_at": "2025-01-21T10:00:00Z",
            "body": "New release with improvements",
            "assets": [
                {
                    "name": "test-windows.zip",
                    "browser_download_url": "https://example.com/test.zip",
                    "size": 2048
                }
            ],
            "prerelease": False
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            # Mock current version to be older
            update_service.current_version = "1.0.0"
            
            result = await update_service.check_for_updates(force=True)
            
            assert result is not None
            assert isinstance(result, ReleaseInfo)
            assert result.version == "1.1.0"
            assert result.download_url == "https://example.com/test.zip"
    
    def test_progress_callback(self, update_service):
        """Test progress callback functionality"""
        progress_updates = []
        
        def progress_callback(progress):
            progress_updates.append(progress)
        
        update_service.set_progress_callback(progress_callback)
        update_service._notify_progress("downloading", 0.5, "Downloading...")
        
        assert len(progress_updates) == 1
        assert progress_updates[0].stage == "downloading"
        assert progress_updates[0].progress == 0.5
        assert progress_updates[0].message == "Downloading..."


class TestAutoUpdater:
    """Test cases for AutoUpdater"""
    
    @pytest.fixture
    def config_service(self):
        """Mock config service"""
        config = Mock(spec=ConfigService)
        config.get.side_effect = lambda key, default=None: {
            "update.auto_check": True,
            "update.check_interval": 24,
            "update.include_prereleases": False
        }.get(key, default)
        config.set.return_value = None
        return config
    
    @pytest.fixture
    def auto_updater(self, config_service):
        """Create AutoUpdater instance"""
        return AutoUpdater(config_service)
    
    def test_initialization(self, auto_updater):
        """Test AutoUpdater initialization"""
        assert auto_updater.auto_check_enabled == True
        assert auto_updater.is_checking == False
        assert auto_updater.is_downloading == False
        assert auto_updater.is_installing == False
    
    def test_settings_update(self, auto_updater):
        """Test updating settings"""
        new_settings = {
            "auto_check": False,
            "check_interval": 12,
            "silent_mode": True
        }
        
        auto_updater.update_settings(new_settings)
        
        assert auto_updater.auto_check_enabled == False
        assert auto_updater.silent_mode == True
    
    def test_get_settings(self, auto_updater):
        """Test getting current settings"""
        settings = auto_updater.get_settings()
        
        assert "auto_check" in settings
        assert "auto_download" in settings
        assert "auto_install" in settings
        assert "silent_mode" in settings
        assert "check_interval" in settings


class TestUpdateManager:
    """Test cases for UpdateManager singleton"""
    
    @pytest.fixture
    def config_service(self):
        """Mock config service"""
        config = Mock(spec=ConfigService)
        config.get.return_value = True
        config.set.return_value = None
        return config
    
    def test_singleton_pattern(self, config_service):
        """Test UpdateManager singleton pattern"""
        # Clear any existing instance
        UpdateManager._instance = None
        
        manager1 = UpdateManager(config_service)
        manager2 = UpdateManager()
        
        assert manager1 is manager2
        assert manager1._initialized == True
    
    def test_get_instance_without_init(self):
        """Test getting instance without initialization"""
        UpdateManager._instance = None
        
        with pytest.raises(RuntimeError):
            UpdateManager.get_instance()
    
    def test_version_info(self, config_service):
        """Test getting version information"""
        UpdateManager._instance = None
        manager = UpdateManager(config_service)
        
        version_info = manager.get_version_info()
        
        assert "current_version" in version_info
        assert "last_check" in version_info
        assert "update_available" in version_info
        assert "available_version" in version_info


class TestReleaseInfo:
    """Test cases for ReleaseInfo data class"""
    
    def test_release_info_creation(self):
        """Test creating ReleaseInfo instance"""
        release_date = datetime.now()
        
        release_info = ReleaseInfo(
            version="1.2.0",
            tag_name="v1.2.0",
            release_date=release_date,
            changelog="Test changelog",
            download_url="https://example.com/download.zip",
            file_size=1024,
            is_prerelease=False
        )
        
        assert release_info.version == "1.2.0"
        assert release_info.tag_name == "v1.2.0"
        assert release_info.release_date == release_date
        assert release_info.changelog == "Test changelog"
        assert release_info.download_url == "https://example.com/download.zip"
        assert release_info.file_size == 1024
        assert release_info.is_prerelease == False


class TestUpdateProgress:
    """Test cases for UpdateProgress data class"""
    
    def test_update_progress_creation(self):
        """Test creating UpdateProgress instance"""
        progress = UpdateProgress(
            stage="downloading",
            progress=0.75,
            message="Downloading update...",
            error=None
        )
        
        assert progress.stage == "downloading"
        assert progress.progress == 0.75
        assert progress.message == "Downloading update..."
        assert progress.error is None
    
    def test_update_progress_with_error(self):
        """Test creating UpdateProgress with error"""
        progress = UpdateProgress(
            stage="error",
            progress=0.0,
            message="Download failed",
            error="Network timeout"
        )
        
        assert progress.stage == "error"
        assert progress.progress == 0.0
        assert progress.message == "Download failed"
        assert progress.error == "Network timeout"


@pytest.mark.integration
class TestUpdateIntegration:
    """Integration tests for update system"""
    
    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for tests"""
        return tmp_path
    
    @pytest.fixture
    def config_service(self, temp_dir):
        """Create real config service for integration tests"""
        from app.services.config_service import ConfigService
        config_file = temp_dir / "config.json"
        return ConfigService(str(config_file))
    
    def test_full_update_workflow(self, config_service, temp_dir):
        """Test complete update workflow"""
        # This would be a more comprehensive integration test
        # that tests the entire update process end-to-end
        pass
    
    @pytest.mark.asyncio
    async def test_download_and_extract(self, config_service, temp_dir):
        """Test download and extraction process"""
        # Mock a download and extraction process
        update_service = UpdateService(config_service)
        
        # This would test actual file download and extraction
        # using mock HTTP responses and zip files
        pass


if __name__ == "__main__":
    pytest.main([__file__])