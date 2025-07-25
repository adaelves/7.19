"""
Tests for download manager functionality.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.core.downloader.download_manager import DownloadManager
from app.core.downloader.task_queue import TaskQueue
from app.core.downloader.thread_pool import ThreadPool
from app.core.downloader.progress_tracker import ProgressTracker
from app.data.models.core import DownloadTask, TaskStatus, DownloadOptions
from tests.utils.test_helpers import TestDataFactory, MockDownloadManager


class TestDownloadManager:
    """Test download manager core functionality"""
    
    @pytest.fixture
    def download_manager(self):
        """Create download manager instance"""
        return DownloadManager(max_concurrent=3)
    
    @pytest.fixture
    def sample_options(self):
        """Sample download options"""
        return TestDataFactory.create_download_options()
    
    @pytest.mark.asyncio
    async def test_initialization(self, download_manager):
        """Test download manager initialization"""
        await download_manager.initialize()
        
        assert download_manager.is_initialized
        assert download_manager.task_queue is not None
        assert download_manager.thread_pool is not None
        assert download_manager.progress_tracker is not None
    
    @pytest.mark.asyncio
    async def test_add_download_task(self, download_manager, sample_options):
        """Test adding download task"""
        await download_manager.initialize()
        
        url = "https://youtube.com/watch?v=test123"
        task_id = await download_manager.add_download(url, sample_options)
        
        assert task_id is not None
        assert len(task_id) > 0
        
        # Verify task was added to queue
        task = download_manager.get_task(task_id)
        assert task is not None
        assert task.url == url
        assert task.status == TaskStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_start_download(self, download_manager, sample_options):
        """Test starting download"""
        await download_manager.initialize()
        
        # Mock the actual download process
        with patch.object(download_manager, '_download_task', new_callable=AsyncMock) as mock_download:
            mock_download.return_value = True
            
            url = "https://youtube.com/watch?v=test123"
            task_id = await download_manager.add_download(url, sample_options)
            
            success = await download_manager.start_download(task_id)
            assert success
            
            # Verify download was called
            mock_download.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_pause_download(self, download_manager, sample_options):
        """Test pausing download"""
        await download_manager.initialize()
        
        url = "https://youtube.com/watch?v=test123"
        task_id = await download_manager.add_download(url, sample_options)
        
        # Start download first
        with patch.object(download_manager, '_download_task', new_callable=AsyncMock):
            await download_manager.start_download(task_id)
            
            # Pause download
            success = await download_manager.pause_download(task_id)
            assert success
            
            task = download_manager.get_task(task_id)
            assert task.status == TaskStatus.PAUSED
    
    @pytest.mark.asyncio
    async def test_cancel_download(self, download_manager, sample_options):
        """Test canceling download"""
        await download_manager.initialize()
        
        url = "https://youtube.com/watch?v=test123"
        task_id = await download_manager.add_download(url, sample_options)
        
        success = await download_manager.cancel_download(task_id)
        assert success
        
        task = download_manager.get_task(task_id)
        assert task.status == TaskStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_batch_download(self, download_manager, sample_options):
        """Test batch download functionality"""
        await download_manager.initialize()
        
        urls = [
            "https://youtube.com/watch?v=test1",
            "https://youtube.com/watch?v=test2",
            "https://youtube.com/watch?v=test3"
        ]
        
        with patch.object(download_manager, '_download_task', new_callable=AsyncMock) as mock_download:
            mock_download.return_value = True
            
            task_ids = await download_manager.add_batch_download(urls, sample_options)
            
            assert len(task_ids) == 3
            assert all(task_id is not None for task_id in task_ids)
            
            # Start batch download
            success = await download_manager.start_batch_download(task_ids)
            assert success
    
    @pytest.mark.asyncio
    async def test_concurrent_downloads_limit(self, download_manager, sample_options):
        """Test concurrent downloads limit"""
        await download_manager.initialize()
        
        # Add more tasks than the concurrent limit
        urls = [f"https://youtube.com/watch?v=test{i}" for i in range(5)]
        
        with patch.object(download_manager, '_download_task', new_callable=AsyncMock) as mock_download:
            # Simulate slow downloads
            mock_download.side_effect = lambda task: asyncio.sleep(0.1)
            
            task_ids = await download_manager.add_batch_download(urls, sample_options)
            
            # Start all downloads
            await download_manager.start_batch_download(task_ids)
            
            # Check that only max_concurrent downloads are active
            active_count = len(download_manager.get_active_downloads())
            assert active_count <= download_manager.max_concurrent
    
    @pytest.mark.asyncio
    async def test_progress_tracking(self, download_manager, sample_options):
        """Test progress tracking"""
        await download_manager.initialize()
        
        url = "https://youtube.com/watch?v=test123"
        task_id = await download_manager.add_download(url, sample_options)
        
        progress_updates = []
        
        def progress_callback(task_id, progress):
            progress_updates.append((task_id, progress))
        
        download_manager.add_progress_callback(progress_callback)
        
        # Simulate download with progress updates
        with patch.object(download_manager, '_download_task', new_callable=AsyncMock) as mock_download:
            async def simulate_progress(task):
                for progress in [25, 50, 75, 100]:
                    await download_manager.progress_tracker.update_progress(task.id, progress)
                    await asyncio.sleep(0.01)
                return True
            
            mock_download.side_effect = simulate_progress
            
            await download_manager.start_download(task_id)
            
            # Wait for progress updates
            await asyncio.sleep(0.1)
            
            assert len(progress_updates) > 0
            assert any(progress == 100 for _, progress in progress_updates)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, download_manager, sample_options):
        """Test error handling during download"""
        await download_manager.initialize()
        
        url = "https://youtube.com/watch?v=test123"
        task_id = await download_manager.add_download(url, sample_options)
        
        # Mock download failure
        with patch.object(download_manager, '_download_task', new_callable=AsyncMock) as mock_download:
            mock_download.side_effect = Exception("Download failed")
            
            success = await download_manager.start_download(task_id)
            assert not success
            
            task = download_manager.get_task(task_id)
            assert task.status == TaskStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, download_manager, sample_options):
        """Test retry mechanism for failed downloads"""
        await download_manager.initialize()
        
        url = "https://youtube.com/watch?v=test123"
        task_id = await download_manager.add_download(url, sample_options)
        
        call_count = 0
        
        async def failing_download(task):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return True
        
        with patch.object(download_manager, '_download_task', new_callable=AsyncMock) as mock_download:
            mock_download.side_effect = failing_download
            
            success = await download_manager.start_download(task_id)
            assert success
            assert call_count == 3  # Should retry twice before succeeding
    
    def test_get_statistics(self, download_manager):
        """Test getting download statistics"""
        # Add some mock tasks
        tasks = [
            TestDataFactory.create_download_task(status=TaskStatus.COMPLETED),
            TestDataFactory.create_download_task(status=TaskStatus.DOWNLOADING),
            TestDataFactory.create_download_task(status=TaskStatus.FAILED),
        ]
        
        for task in tasks:
            download_manager.task_queue.add_task(task)
        
        stats = download_manager.get_statistics()
        
        assert stats['total_tasks'] == 3
        assert stats['completed_tasks'] == 1
        assert stats['active_tasks'] == 1
        assert stats['failed_tasks'] == 1
    
    @pytest.mark.asyncio
    async def test_cleanup(self, download_manager):
        """Test cleanup functionality"""
        await download_manager.initialize()
        
        # Add some tasks
        for i in range(3):
            url = f"https://youtube.com/watch?v=test{i}"
            await download_manager.add_download(url, TestDataFactory.create_download_options())
        
        # Cleanup
        await download_manager.cleanup()
        
        assert not download_manager.is_initialized
        assert len(download_manager.get_all_tasks()) == 0


class TestTaskQueue:
    """Test task queue functionality"""
    
    @pytest.fixture
    def task_queue(self):
        """Create task queue instance"""
        return TaskQueue(max_size=10)
    
    def test_add_task(self, task_queue):
        """Test adding task to queue"""
        task = TestDataFactory.create_download_task()
        
        success = task_queue.add_task(task)
        assert success
        assert task_queue.size() == 1
        assert task_queue.get_task(task.id) == task
    
    def test_remove_task(self, task_queue):
        """Test removing task from queue"""
        task = TestDataFactory.create_download_task()
        task_queue.add_task(task)
        
        removed_task = task_queue.remove_task(task.id)
        assert removed_task == task
        assert task_queue.size() == 0
    
    def test_get_next_task(self, task_queue):
        """Test getting next task from queue"""
        # Add tasks with different priorities
        high_priority = TestDataFactory.create_download_task()
        high_priority.priority = 10
        
        low_priority = TestDataFactory.create_download_task()
        low_priority.priority = 1
        
        task_queue.add_task(low_priority)
        task_queue.add_task(high_priority)
        
        # Should return high priority task first
        next_task = task_queue.get_next_task()
        assert next_task == high_priority
    
    def test_queue_full(self, task_queue):
        """Test queue full condition"""
        # Fill queue to capacity
        for i in range(10):
            task = TestDataFactory.create_download_task()
            task_queue.add_task(task)
        
        # Try to add one more
        overflow_task = TestDataFactory.create_download_task()
        success = task_queue.add_task(overflow_task)
        
        assert not success
        assert task_queue.is_full()
    
    def test_clear_queue(self, task_queue):
        """Test clearing queue"""
        # Add some tasks
        for i in range(5):
            task = TestDataFactory.create_download_task()
            task_queue.add_task(task)
        
        task_queue.clear()
        assert task_queue.size() == 0
        assert task_queue.is_empty()


class TestProgressTracker:
    """Test progress tracker functionality"""
    
    @pytest.fixture
    def progress_tracker(self):
        """Create progress tracker instance"""
        return ProgressTracker()
    
    @pytest.mark.asyncio
    async def test_update_progress(self, progress_tracker):
        """Test updating task progress"""
        task_id = "test_task_123"
        
        await progress_tracker.update_progress(task_id, 50.0)
        
        progress = progress_tracker.get_progress(task_id)
        assert progress == 50.0
    
    @pytest.mark.asyncio
    async def test_progress_callbacks(self, progress_tracker):
        """Test progress callbacks"""
        task_id = "test_task_123"
        callback_called = False
        received_progress = None
        
        def progress_callback(tid, progress):
            nonlocal callback_called, received_progress
            callback_called = True
            received_progress = progress
        
        progress_tracker.add_callback(progress_callback)
        
        await progress_tracker.update_progress(task_id, 75.0)
        
        assert callback_called
        assert received_progress == 75.0
    
    def test_get_overall_progress(self, progress_tracker):
        """Test getting overall progress"""
        # Add progress for multiple tasks
        asyncio.run(progress_tracker.update_progress("task1", 100.0))
        asyncio.run(progress_tracker.update_progress("task2", 50.0))
        asyncio.run(progress_tracker.update_progress("task3", 0.0))
        
        overall = progress_tracker.get_overall_progress()
        assert overall == 50.0  # (100 + 50 + 0) / 3
    
    def test_remove_task_progress(self, progress_tracker):
        """Test removing task progress"""
        task_id = "test_task_123"
        
        asyncio.run(progress_tracker.update_progress(task_id, 50.0))
        assert progress_tracker.get_progress(task_id) == 50.0
        
        progress_tracker.remove_task(task_id)
        assert progress_tracker.get_progress(task_id) == 0.0


if __name__ == "__main__":
    pytest.main([__file__])