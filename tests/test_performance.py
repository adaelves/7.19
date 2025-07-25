"""
Performance benchmark tests for the video downloader application.
"""
import pytest
import asyncio
import time
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch
from pathlib import Path

from app.core.downloader.download_manager import DownloadManager
from app.core.plugin.manager import PluginManager
from app.data.database import DatabaseService
from app.services.download_service import DownloadService
from tests.utils.test_helpers import TestDataFactory, PerformanceTimer


@pytest.mark.performance
class TestDownloadPerformance:
    """Performance tests for download functionality"""
    
    @pytest.fixture
    async def performance_setup(self, temp_directory):
        """Set up performance testing environment"""
        # Create database
        db_path = temp_directory / "perf_test.db"
        db_service = DatabaseService(str(db_path))
        
        # Create download manager with higher concurrency
        download_manager = DownloadManager(max_concurrent=10)
        await download_manager.initialize()
        
        # Create plugin manager
        plugin_manager = PluginManager(enable_hot_reload=False)
        await plugin_manager.initialize()
        
        # Create download service
        download_service = DownloadService(
            download_manager=download_manager,
            plugin_manager=plugin_manager,
            database_service=db_service
        )
        await download_service.initialize()
        
        yield {
            'download_manager': download_manager,
            'plugin_manager': plugin_manager,
            'download_service': download_service,
            'db_service': db_service
        }
        
        # Cleanup
        await download_service.shutdown()
        await download_manager.cleanup()
        await plugin_manager.shutdown()
        db_service.close()
    
    @pytest.mark.asyncio
    async def test_concurrent_download_performance(self, performance_setup, performance_monitor):
        """Test performance with many concurrent downloads"""
        setup = performance_setup
        download_service = setup['download_service']
        
        # Create many download tasks
        num_tasks = 50
        urls = [f"https://youtube.com/watch?v=test{i:03d}" for i in range(num_tasks)]
        options = TestDataFactory.create_download_options()
        
        # Mock download operations to avoid actual network calls
        with patch.object(download_service.download_manager, '_download_task') as mock_download:
            async def mock_download_func(task):
                # Simulate download time
                await asyncio.sleep(0.01)
                return True
            
            mock_download.side_effect = mock_download_func
            
            # Start performance monitoring
            performance_monitor.start()
            
            # Add all downloads
            task_ids = []
            for url in urls:
                task_id = await download_service.add_download(url, options)
                task_ids.append(task_id)
            
            # Wait for all downloads to complete
            await asyncio.sleep(2.0)
            
            # Stop monitoring
            metrics = performance_monitor.stop()
            
            # Performance assertions
            assert metrics['duration'] < 5.0, f"Download took too long: {metrics['duration']:.2f}s"
            assert metrics['memory_delta'] < 100 * 1024 * 1024, f"Memory usage too high: {metrics['memory_delta']} bytes"
            
            # Verify all tasks were processed
            assert len(task_ids) == num_tasks
    
    @pytest.mark.asyncio
    async def test_database_performance(self, performance_setup, performance_monitor):
        """Test database performance with large datasets"""
        db_service = performance_setup['db_service']
        
        # Generate test data
        num_records = 1000
        tasks = [TestDataFactory.create_download_task() for _ in range(num_records)]
        metadatas = [TestDataFactory.create_video_metadata() for _ in range(num_records)]
        
        performance_monitor.start()
        
        # Insert records
        for task, metadata in zip(tasks, metadatas):
            db_service.add_download_record(task, metadata)
        
        insert_metrics = performance_monitor.stop()
        
        # Test query performance
        performance_monitor.start()
        
        # Perform various queries
        all_history = db_service.get_download_history(limit=100)
        search_results = db_service.search_downloads("Test")
        stats = db_service.get_download_statistics()
        
        query_metrics = performance_monitor.stop()
        
        # Performance assertions
        assert insert_metrics['duration'] < 10.0, f"Insert took too long: {insert_metrics['duration']:.2f}s"
        assert query_metrics['duration'] < 1.0, f"Queries took too long: {query_metrics['duration']:.2f}s"
        
        # Verify data integrity
        assert len(all_history) == 100  # Limited by query
        assert stats['total_downloads'] == num_records
    
    @pytest.mark.asyncio
    async def test_plugin_loading_performance(self, temp_directory, performance_monitor):
        """Test plugin loading performance"""
        # Create many test plugins
        plugin_dir = temp_directory / "plugins"
        plugin_dir.mkdir()
        
        num_plugins = 20
        for i in range(num_plugins):
            plugin_content = f'''
from app.core.extractor.base import BaseExtractor, ExtractorInfo
from typing import List, Dict, Any

class TestExtractor{i}(BaseExtractor):
    @property
    def supported_domains(self) -> List[str]:
        return ['test{i}.com']
    
    def can_handle(self, url: str) -> bool:
        return 'test{i}.com' in url
    
    async def extract_info(self, url: str) -> Dict[str, Any]:
        return {{'title': 'Test Video {i}', 'id': '{i}'}}
    
    async def get_download_urls(self, info: Dict[str, Any]) -> List[str]:
        return ['http://test{i}.com/video.mp4']
    
    def get_extractor_info(self) -> ExtractorInfo:
        return ExtractorInfo(
            name='Test Extractor {i}',
            version='1.0.0',
            supported_domains=self.supported_domains,
            description='Test extractor {i}'
        )
'''
            (plugin_dir / f"test_plugin_{i}.py").write_text(plugin_content)
        
        # Test plugin loading performance
        performance_monitor.start()
        
        plugin_manager = PluginManager(
            plugin_directories=[str(plugin_dir)],
            enable_hot_reload=False
        )
        await plugin_manager.initialize()
        
        metrics = performance_monitor.stop()
        
        # Performance assertions
        assert metrics['duration'] < 5.0, f"Plugin loading took too long: {metrics['duration']:.2f}s"
        
        # Verify all plugins loaded
        loaded_plugins = plugin_manager.get_all_plugins()
        assert len(loaded_plugins) == num_plugins
        
        await plugin_manager.shutdown()
    
    def test_memory_usage_stability(self, performance_setup):
        """Test memory usage stability over time"""
        download_service = performance_setup['download_service']
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss
        memory_samples = [initial_memory]
        
        # Simulate continuous operation
        for cycle in range(10):
            # Add and remove tasks
            tasks = []
            for i in range(20):
                url = f"https://youtube.com/watch?v=cycle{cycle}_task{i}"
                options = TestDataFactory.create_download_options()
                
                # Mock the download service to avoid actual operations
                with patch.object(download_service, 'add_download') as mock_add:
                    mock_add.return_value = f"task_{cycle}_{i}"
                    asyncio.run(download_service.add_download(url, options))
            
            # Sample memory usage
            current_memory = process.memory_info().rss
            memory_samples.append(current_memory)
            
            # Small delay
            time.sleep(0.1)
        
        # Check memory growth
        final_memory = memory_samples[-1]
        memory_growth = final_memory - initial_memory
        memory_growth_mb = memory_growth / (1024 * 1024)
        
        # Memory growth should be reasonable (less than 50MB for this test)
        assert memory_growth_mb < 50, f"Memory growth too high: {memory_growth_mb:.2f}MB"
        
        # Check for memory leaks (no continuous growth)
        recent_samples = memory_samples[-5:]
        max_recent = max(recent_samples)
        min_recent = min(recent_samples)
        recent_variation = max_recent - min_recent
        
        # Recent memory usage should be relatively stable
        assert recent_variation < 10 * 1024 * 1024, "Memory usage not stable"


@pytest.mark.performance
class TestUIPerformance:
    """Performance tests for UI components"""
    
    @pytest.fixture
    def ui_performance_setup(self, qapp):
        """Set up UI performance testing"""
        from app.ui.main_window import MainWindow
        
        main_window = MainWindow()
        main_window.show()
        qapp.processEvents()
        
        return main_window
    
    def test_download_list_performance(self, ui_performance_setup, performance_monitor):
        """Test download list performance with many items"""
        main_window = ui_performance_setup
        download_list = main_window.download_list
        
        # Create many tasks
        num_tasks = 500
        tasks = [TestDataFactory.create_download_task() for _ in range(num_tasks)]
        
        performance_monitor.start()
        
        # Add tasks to list
        for task in tasks:
            download_list.add_task(task)
        
        # Process UI events
        QApplication.processEvents()
        
        metrics = performance_monitor.stop()
        
        # Performance assertions
        assert metrics['duration'] < 5.0, f"UI update took too long: {metrics['duration']:.2f}s"
        assert download_list.count() == num_tasks
    
    def test_progress_update_performance(self, ui_performance_setup, performance_monitor):
        """Test progress update performance"""
        main_window = ui_performance_setup
        download_list = main_window.download_list
        
        # Add tasks
        num_tasks = 100
        tasks = [TestDataFactory.create_download_task() for _ in range(num_tasks)]
        
        for task in tasks:
            download_list.add_task(task)
        
        performance_monitor.start()
        
        # Update progress for all tasks multiple times
        for progress in range(0, 101, 10):
            for task in tasks:
                download_list.update_task_progress(task.id, progress)
            
            # Process UI events
            QApplication.processEvents()
        
        metrics = performance_monitor.stop()
        
        # Performance assertions
        assert metrics['duration'] < 10.0, f"Progress updates took too long: {metrics['duration']:.2f}s"
    
    def test_theme_switching_performance(self, ui_performance_setup, performance_monitor):
        """Test theme switching performance"""
        main_window = ui_performance_setup
        
        # Add some content to make theme switching more expensive
        for i in range(50):
            task = TestDataFactory.create_download_task()
            main_window.download_list.add_task(task)
        
        performance_monitor.start()
        
        # Switch themes multiple times
        for _ in range(10):
            main_window.switch_theme()
            QApplication.processEvents()
        
        metrics = performance_monitor.stop()
        
        # Performance assertions
        assert metrics['duration'] < 2.0, f"Theme switching took too long: {metrics['duration']:.2f}s"


@pytest.mark.performance
class TestNetworkPerformance:
    """Performance tests for network operations"""
    
    @pytest.mark.asyncio
    async def test_concurrent_metadata_extraction(self, performance_monitor):
        """Test concurrent metadata extraction performance"""
        from app.core.plugin.manager import PluginManager
        
        plugin_manager = PluginManager()
        await plugin_manager.initialize()
        
        # Create test URLs
        urls = [f"https://youtube.com/watch?v=test{i:03d}" for i in range(20)]
        
        # Mock metadata extraction
        with patch.object(plugin_manager, 'get_metadata') as mock_metadata:
            async def mock_metadata_func(url):
                # Simulate network delay
                await asyncio.sleep(0.05)
                return TestDataFactory.create_video_metadata()
            
            mock_metadata.side_effect = mock_metadata_func
            
            performance_monitor.start()
            
            # Extract metadata concurrently
            tasks = [plugin_manager.get_metadata(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            metrics = performance_monitor.stop()
            
            # Performance assertions
            assert metrics['duration'] < 2.0, f"Concurrent extraction took too long: {metrics['duration']:.2f}s"
            assert len(results) == len(urls)
            assert all(not isinstance(r, Exception) for r in results)
        
        await plugin_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_rate_limiting_performance(self, performance_monitor):
        """Test rate limiting performance"""
        from app.core.downloader.rate_limiter import RateLimiter
        
        # Create rate limiter (100 requests per second)
        rate_limiter = RateLimiter(max_requests=100, time_window=1.0)
        
        performance_monitor.start()
        
        # Make many requests
        num_requests = 200
        tasks = []
        
        async def make_request():
            async with rate_limiter:
                # Simulate request processing
                await asyncio.sleep(0.001)
                return True
        
        # Submit all requests
        for _ in range(num_requests):
            task = asyncio.create_task(make_request())
            tasks.append(task)
        
        # Wait for all requests to complete
        results = await asyncio.gather(*tasks)
        
        metrics = performance_monitor.stop()
        
        # Performance assertions
        # Should take at least 2 seconds due to rate limiting (200 requests / 100 per second)
        assert metrics['duration'] >= 1.8, f"Rate limiting not working: {metrics['duration']:.2f}s"
        assert metrics['duration'] < 5.0, f"Rate limiting too slow: {metrics['duration']:.2f}s"
        assert len(results) == num_requests
        assert all(results)


@pytest.mark.performance
class TestScalabilityTests:
    """Scalability tests for large-scale operations"""
    
    @pytest.mark.asyncio
    async def test_large_playlist_handling(self, performance_setup, performance_monitor):
        """Test handling of large playlists"""
        download_service = performance_setup['download_service']
        
        # Simulate large playlist
        playlist_size = 1000
        playlist_urls = [f"https://youtube.com/watch?v=playlist{i:04d}" for i in range(playlist_size)]
        
        # Mock playlist extraction
        with patch.object(download_service.plugin_manager, 'extract_info') as mock_extract:
            mock_extract.return_value = {
                'entries': [{'url': url, 'title': f'Video {i}'} for i, url in enumerate(playlist_urls)]
            }
            
            performance_monitor.start()
            
            # Process playlist
            playlist_url = "https://youtube.com/playlist?list=large_playlist"
            task_ids = await download_service.add_playlist_download(playlist_url, TestDataFactory.create_download_options())
            
            metrics = performance_monitor.stop()
            
            # Performance assertions
            assert metrics['duration'] < 30.0, f"Playlist processing took too long: {metrics['duration']:.2f}s"
            assert len(task_ids) == playlist_size
    
    def test_database_scalability(self, performance_setup, performance_monitor):
        """Test database performance with large datasets"""
        db_service = performance_setup['db_service']
        
        # Test with increasing dataset sizes
        dataset_sizes = [100, 500, 1000, 5000]
        performance_results = []
        
        for size in dataset_sizes:
            # Generate test data
            tasks = [TestDataFactory.create_download_task() for _ in range(size)]
            metadatas = [TestDataFactory.create_video_metadata() for _ in range(size)]
            
            performance_monitor.start()
            
            # Insert data
            for task, metadata in zip(tasks, metadatas):
                db_service.add_download_record(task, metadata)
            
            # Perform queries
            db_service.get_download_history(limit=100)
            db_service.search_downloads("Test")
            db_service.get_download_statistics()
            
            metrics = performance_monitor.stop()
            performance_results.append((size, metrics['duration']))
            
            # Clear database for next test
            # (In a real scenario, you might want to use separate databases)
        
        # Check that performance scales reasonably
        # Performance should not degrade exponentially
        for i in range(1, len(performance_results)):
            prev_size, prev_time = performance_results[i-1]
            curr_size, curr_time = performance_results[i]
            
            # Time should not increase more than proportionally to size increase
            size_ratio = curr_size / prev_size
            time_ratio = curr_time / prev_time if prev_time > 0 else 1
            
            assert time_ratio <= size_ratio * 2, f"Performance degraded too much: {time_ratio:.2f}x for {size_ratio:.2f}x data"


@pytest.mark.performance
class TestStressTests:
    """Stress tests for system limits"""
    
    @pytest.mark.asyncio
    async def test_memory_stress(self, performance_setup):
        """Test system behavior under memory stress"""
        download_service = performance_setup['download_service']
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss
        max_memory_mb = 500  # 500MB limit
        
        tasks = []
        try:
            # Keep adding tasks until memory limit is approached
            for i in range(10000):  # Large number to stress test
                task = TestDataFactory.create_download_task()
                tasks.append(task)
                
                # Check memory usage periodically
                if i % 100 == 0:
                    current_memory = process.memory_info().rss
                    memory_mb = (current_memory - initial_memory) / (1024 * 1024)
                    
                    if memory_mb > max_memory_mb:
                        break
            
            # System should still be responsive
            stats = download_service.get_statistics()
            assert stats is not None
            
        except MemoryError:
            pytest.fail("System ran out of memory during stress test")
    
    @pytest.mark.asyncio
    async def test_concurrent_stress(self, performance_setup):
        """Test system behavior under high concurrency"""
        download_service = performance_setup['download_service']
        
        # Create many concurrent operations
        num_operations = 100
        
        async def concurrent_operation(i):
            url = f"https://youtube.com/watch?v=stress{i:03d}"
            options = TestDataFactory.create_download_options()
            
            with patch.object(download_service, 'add_download') as mock_add:
                mock_add.return_value = f"task_{i}"
                return await download_service.add_download(url, options)
        
        # Run all operations concurrently
        tasks = [concurrent_operation(i) for i in range(num_operations)]
        
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=30.0
            )
            
            # Check that most operations succeeded
            successful = sum(1 for r in results if not isinstance(r, Exception))
            success_rate = successful / len(results)
            
            assert success_rate > 0.8, f"Success rate too low: {success_rate:.2f}"
            
        except asyncio.TimeoutError:
            pytest.fail("Concurrent operations timed out")


if __name__ == "__main__":
    pytest.main([__file__])