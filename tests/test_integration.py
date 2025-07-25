"""
Integration tests for the video downloader application.
"""
import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock

from app.core.downloader.download_manager import DownloadManager
from app.core.plugin.manager import PluginManager
from app.services.download_service import DownloadService
from app.services.creator_monitor_service import CreatorMonitorService
from app.data.database import DatabaseService
from app.data.models.core import Platform, TaskStatus
from tests.utils.test_helpers import TestDataFactory


@pytest.mark.integration
class TestDownloadIntegration:
    """Integration tests for download functionality"""
    
    @pytest.fixture
    async def integrated_system(self, temp_directory):
        """Set up integrated system for testing"""
        # Create temporary database
        db_path = temp_directory / "test.db"
        db_service = DatabaseService(str(db_path))
        
        # Create plugin manager
        plugin_manager = PluginManager(
            plugin_directories=[str(Path(__file__).parent.parent / "app" / "plugins")],
            enable_hot_reload=False
        )
        await plugin_manager.initialize()
        
        # Create download manager
        download_manager = DownloadManager(max_concurrent=2)
        await download_manager.initialize()
        
        # Create download service
        download_service = DownloadService(
            download_manager=download_manager,
            plugin_manager=plugin_manager,
            database_service=db_service
        )
        await download_service.initialize()
        
        yield {
            'db_service': db_service,
            'plugin_manager': plugin_manager,
            'download_manager': download_manager,
            'download_service': download_service
        }
        
        # Cleanup
        await download_service.shutdown()
        await download_manager.cleanup()
        await plugin_manager.shutdown()
        db_service.close()
    
    @pytest.mark.asyncio
    async def test_end_to_end_download(self, integrated_system, mock_yt_dlp):
        """Test complete download flow from URL to file"""
        system = integrated_system
        download_service = system['download_service']
        
        # Mock file system operations
        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'), \
             patch('builtins.open', create=True), \
             patch('shutil.move'):
            
            url = "https://youtube.com/watch?v=test123"
            options = TestDataFactory.create_download_options(
                output_path=str(Path.cwd() / "test_downloads")
            )
            
            # Start download
            task_id = await download_service.add_download(url, options)
            assert task_id is not None
            
            # Wait for download to complete (mocked)
            await asyncio.sleep(0.1)
            
            # Verify task was created and processed
            task = download_service.get_task(task_id)
            assert task is not None
            assert task.url == url
    
    @pytest.mark.asyncio
    async def test_plugin_system_integration(self, integrated_system):
        """Test plugin system integration with download service"""
        system = integrated_system
        plugin_manager = system['plugin_manager']
        download_service = system['download_service']
        
        # Test URL routing
        youtube_url = "https://youtube.com/watch?v=test123"
        bilibili_url = "https://bilibili.com/video/BV1234567890"
        
        # Check if URLs are supported
        assert plugin_manager.is_url_supported(youtube_url)
        
        # Test metadata extraction
        with patch.object(plugin_manager, 'get_metadata') as mock_metadata:
            mock_metadata.return_value = TestDataFactory.create_video_metadata()
            
            metadata = await download_service.get_video_metadata(youtube_url)
            assert metadata is not None
            assert metadata.title is not None
    
    @pytest.mark.asyncio
    async def test_database_integration(self, integrated_system):
        """Test database integration with download service"""
        system = integrated_system
        db_service = system['db_service']
        download_service = system['download_service']
        
        # Create test data
        task = TestDataFactory.create_download_task(status=TaskStatus.COMPLETED)
        metadata = TestDataFactory.create_video_metadata()
        
        # Add download record
        history_id = db_service.add_download_record(task, metadata)
        assert history_id > 0
        
        # Verify record can be retrieved
        history = db_service.get_download_history(limit=1)
        assert len(history) == 1
        assert history[0]['url'] == task.url
    
    @pytest.mark.asyncio
    async def test_concurrent_downloads(self, integrated_system, mock_yt_dlp):
        """Test concurrent download handling"""
        system = integrated_system
        download_service = system['download_service']
        
        urls = [
            "https://youtube.com/watch?v=test1",
            "https://youtube.com/watch?v=test2",
            "https://youtube.com/watch?v=test3",
            "https://youtube.com/watch?v=test4"
        ]
        
        options = TestDataFactory.create_download_options()
        
        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'), \
             patch('builtins.open', create=True), \
             patch('shutil.move'):
            
            # Start multiple downloads
            task_ids = []
            for url in urls:
                task_id = await download_service.add_download(url, options)
                task_ids.append(task_id)
            
            # Wait for processing
            await asyncio.sleep(0.2)
            
            # Verify all tasks were created
            assert len(task_ids) == 4
            assert all(task_id is not None for task_id in task_ids)
            
            # Check concurrent limit is respected
            active_downloads = download_service.get_active_downloads()
            assert len(active_downloads) <= 2  # max_concurrent = 2


@pytest.mark.integration
class TestCreatorMonitoringIntegration:
    """Integration tests for creator monitoring"""
    
    @pytest.fixture
    async def monitoring_system(self, temp_directory):
        """Set up monitoring system for testing"""
        # Create temporary database
        db_path = temp_directory / "test.db"
        db_service = DatabaseService(str(db_path))
        
        # Create plugin manager
        plugin_manager = PluginManager(
            plugin_directories=[str(Path(__file__).parent.parent / "app" / "plugins")],
            enable_hot_reload=False
        )
        await plugin_manager.initialize()
        
        # Create creator monitor service
        monitor_service = CreatorMonitorService(
            plugin_manager=plugin_manager,
            database_service=db_service
        )
        await monitor_service.initialize()
        
        yield {
            'db_service': db_service,
            'plugin_manager': plugin_manager,
            'monitor_service': monitor_service
        }
        
        # Cleanup
        await monitor_service.shutdown()
        await plugin_manager.shutdown()
        db_service.close()
    
    @pytest.mark.asyncio
    async def test_creator_monitoring_flow(self, monitoring_system):
        """Test complete creator monitoring flow"""
        system = monitoring_system
        monitor_service = system['monitor_service']
        db_service = system['db_service']
        
        # Add creator to monitor
        creator = TestDataFactory.create_creator_profile(
            name="Test Creator",
            platform=Platform.YOUTUBE,
            auto_download=True
        )
        
        success = db_service.add_creator(creator)
        assert success
        
        # Mock video list extraction
        with patch.object(system['plugin_manager'], 'extract_info') as mock_extract:
            mock_extract.return_value = {
                'entries': [
                    {'title': 'Video 1', 'id': 'vid1'},
                    {'title': 'Video 2', 'id': 'vid2'},
                    {'title': 'Video 3', 'id': 'vid3'}
                ]
            }
            
            # Check for updates
            new_videos = await monitor_service.check_creator_updates(creator.id)
            
            # Should detect new videos (since this is first check)
            assert len(new_videos) > 0
    
    @pytest.mark.asyncio
    async def test_auto_download_integration(self, monitoring_system):
        """Test auto-download integration with creator monitoring"""
        system = monitoring_system
        monitor_service = system['monitor_service']
        db_service = system['db_service']
        
        # Add creator with auto-download enabled
        creator = TestDataFactory.create_creator_profile(
            auto_download=True,
            priority=8
        )
        db_service.add_creator(creator)
        
        # Mock new video detection
        with patch.object(monitor_service, 'check_creator_updates') as mock_check:
            mock_check.return_value = [
                {'title': 'New Video', 'url': 'https://youtube.com/watch?v=new123'}
            ]
            
            # Mock download service
            with patch.object(monitor_service, 'download_service') as mock_download_service:
                mock_download_service.add_download = Mock(return_value="task123")
                
                # Run monitoring check
                await monitor_service.run_monitoring_cycle()
                
                # Verify download was triggered
                mock_download_service.add_download.assert_called()


@pytest.mark.integration
class TestSystemIntegration:
    """System-wide integration tests"""
    
    @pytest.mark.asyncio
    async def test_application_startup_shutdown(self, temp_directory):
        """Test complete application startup and shutdown"""
        from app.main import create_application
        
        # Mock Qt application
        with patch('PySide6.QtWidgets.QApplication') as mock_app:
            mock_app_instance = Mock()
            mock_app.return_value = mock_app_instance
            
            # Create application
            app = await create_application(
                config_dir=str(temp_directory),
                data_dir=str(temp_directory / "data")
            )
            
            assert app is not None
            
            # Test shutdown
            await app.shutdown()
    
    @pytest.mark.asyncio
    async def test_configuration_persistence(self, temp_directory):
        """Test configuration loading and saving"""
        from app.services.config_service import ConfigService
        
        config_file = temp_directory / "config.json"
        config_service = ConfigService(str(config_file))
        
        # Set some configuration values
        test_config = {
            'download_path': '/test/downloads',
            'max_concurrent': 5,
            'theme': 'dark'
        }
        
        for key, value in test_config.items():
            config_service.set(key, value)
        
        # Save configuration
        config_service.save()
        
        # Create new config service instance
        new_config_service = ConfigService(str(config_file))
        
        # Verify configuration was persisted
        for key, expected_value in test_config.items():
            actual_value = new_config_service.get(key)
            assert actual_value == expected_value
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, temp_directory):
        """Test system error recovery"""
        # Create system with invalid configuration
        db_path = temp_directory / "test.db"
        db_service = DatabaseService(str(db_path))
        
        # Simulate database corruption
        with patch.object(db_service.db_manager, 'get_connection') as mock_conn:
            mock_conn.side_effect = Exception("Database corrupted")
            
            # System should handle the error gracefully
            try:
                db_service.get_download_history()
                assert False, "Should have raised exception"
            except Exception as e:
                assert "Database corrupted" in str(e)
        
        # System should recover after fixing the issue
        db_service.db_manager.get_connection = Mock()
        mock_connection = Mock()
        mock_connection.fetchall.return_value = []
        db_service.db_manager.get_connection.return_value = mock_connection
        
        # Should work now
        history = db_service.get_download_history()
        assert isinstance(history, list)


@pytest.mark.integration
@pytest.mark.network
class TestNetworkIntegration:
    """Network-dependent integration tests"""
    
    @pytest.mark.asyncio
    async def test_real_url_validation(self):
        """Test URL validation with real network requests"""
        from app.core.plugin.manager import PluginManager
        
        plugin_manager = PluginManager()
        await plugin_manager.initialize()
        
        # Test with known working URLs (if network is available)
        test_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll - should always exist
        ]
        
        for url in test_urls:
            try:
                is_supported = plugin_manager.is_url_supported(url)
                # Just verify the method doesn't crash
                assert isinstance(is_supported, bool)
            except Exception as e:
                pytest.skip(f"Network test failed: {e}")
        
        await plugin_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_metadata_extraction_real(self):
        """Test metadata extraction with real URLs"""
        # This test requires network access and may be slow
        pytest.skip("Skipping real network test in automated testing")


if __name__ == "__main__":
    pytest.main([__file__])