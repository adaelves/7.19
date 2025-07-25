"""
Tests for advanced features including performance optimization and stability
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch

from app.core.utils.memory_manager import MemoryManager, ObjectPool, LRUCache
from app.core.utils.connection_pool import ConnectionPoolManager, ConnectionConfig
from app.core.utils.performance_optimizer import PerformanceOptimizer, PerformanceTask, TaskPriority
from app.core.utils.exception_recovery import ExceptionRecoveryManager, RecoveryStrategy
from app.core.utils.performance_monitor import PerformanceMonitor, PerformanceMetric
from app.services.advanced_features_service import AdvancedFeaturesService


class TestMemoryManager:
    """Test memory management functionality"""
    
    def test_object_pool_creation(self):
        """Test object pool creation and usage"""
        manager = MemoryManager()
        
        # Create a simple factory function
        def create_dict():
            return {'created_at': time.time()}
        
        pool = manager.create_object_pool('test_pool', create_dict, max_size=5)
        
        # Test acquiring objects
        obj1 = pool.acquire()
        obj2 = pool.acquire()
        
        assert isinstance(obj1, dict)
        assert isinstance(obj2, dict)
        assert 'created_at' in obj1
        assert 'created_at' in obj2
        
        # Test releasing objects
        pool.release(obj1)
        pool.release(obj2)
        
        # Test reuse
        obj3 = pool.acquire()
        assert obj3 in [obj1, obj2]  # Should reuse one of the released objects
        
        stats = pool.get_stats()
        assert stats['reused_count'] > 0
    
    def test_lru_cache(self):
        """Test LRU cache functionality"""
        cache = LRUCache(max_size=3)
        
        # Add items
        cache.put('key1', 'value1')
        cache.put('key2', 'value2')
        cache.put('key3', 'value3')
        
        # Test retrieval
        assert cache.get('key1') == 'value1'
        assert cache.get('key2') == 'value2'
        assert cache.get('key3') == 'value3'
        
        # Add one more item (should evict least recently used)
        cache.put('key4', 'value4')
        
        # key1 should be evicted since it was accessed first
        assert cache.get('key1') is None
        assert cache.get('key4') == 'value4'
        
        stats = cache.get_stats()
        assert stats['size'] == 3
        assert stats['hits'] > 0
        assert stats['misses'] > 0
    
    def test_memory_optimization(self):
        """Test memory optimization functionality"""
        manager = MemoryManager()
        
        # Mock memory usage to trigger optimization
        with patch.object(manager, 'get_memory_usage') as mock_usage:
            mock_usage.return_value = {'percent': 85.0}  # Above threshold
            
            result = manager.optimize_memory()
            
            assert 'triggered_gc' in result
            assert 'memory_usage' in result


class TestConnectionPool:
    """Test connection pool functionality"""
    
    @pytest.mark.asyncio
    async def test_connection_pool_creation(self):
        """Test connection pool creation"""
        config = ConnectionConfig(max_connections=10, max_connections_per_host=5)
        manager = ConnectionPoolManager(config)
        
        await manager.start()
        
        # Test session creation
        session = manager.get_session('https://example.com')
        assert session is not None
        
        # Test stats
        stats = manager.get_connection_stats()
        assert isinstance(stats, dict)
        
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_connection_stats(self):
        """Test connection statistics"""
        manager = ConnectionPoolManager()
        await manager.start()
        
        # Get session to create stats entry
        manager.get_session('https://example.com')
        
        stats = manager.get_connection_stats('https://example.com')
        assert 'requests_count' in stats
        assert 'errors_count' in stats
        assert 'timeouts_count' in stats
        
        await manager.stop()


class TestPerformanceOptimizer:
    """Test performance optimization functionality"""
    
    def test_task_creation(self):
        """Test performance task creation"""
        def sample_func(x, y):
            return x + y
        
        task = PerformanceTask(
            id='test_task',
            func=sample_func,
            args=(1, 2),
            priority=TaskPriority.HIGH
        )
        
        assert task.id == 'test_task'
        assert task.func == sample_func
        assert task.args == (1, 2)
        assert task.priority == TaskPriority.HIGH
    
    def test_batch_processor(self):
        """Test batch processing functionality"""
        from app.core.utils.performance_optimizer import BatchProcessor
        
        processor = BatchProcessor(batch_size=2, max_workers=2)
        
        def sample_func(x):
            return x * 2
        
        task1 = PerformanceTask(id='task1', func=sample_func, args=(5,))
        task2 = PerformanceTask(id='task2', func=sample_func, args=(10,))
        
        processor.add_task(task1)
        processor.add_task(task2)  # Should trigger batch processing
        
        # Wait a bit for processing
        time.sleep(0.1)
        
        stats = processor.get_stats()
        assert stats['batches'] > 0
        
        processor.shutdown()
    
    def test_adaptive_rate_limiter(self):
        """Test adaptive rate limiter"""
        from app.core.utils.performance_optimizer import AdaptiveRateLimiter
        
        limiter = AdaptiveRateLimiter(initial_rate=10.0, min_rate=1.0, max_rate=100.0)
        
        # Record successes to increase rate
        for _ in range(15):
            limiter.record_success()
        
        initial_rate = limiter.get_current_rate()
        
        # Record errors to decrease rate
        for _ in range(10):
            limiter.record_error()
        
        final_rate = limiter.get_current_rate()
        assert final_rate < initial_rate  # Rate should decrease after errors


class TestExceptionRecovery:
    """Test exception recovery functionality"""
    
    @pytest.mark.asyncio
    async def test_retry_strategy(self):
        """Test retry recovery strategy"""
        manager = ExceptionRecoveryManager()
        
        # Register handler for ValueError with retry strategy
        manager.register_handler(
            ValueError,
            RecoveryStrategy.RETRY,
            {'retry': {'max_attempts': 3, 'base_delay': 0.1}}
        )
        
        call_count = 0
        
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Test error")
            return "success"
        
        result = await manager.execute_with_recovery(failing_func)
        assert result == "success"
        assert call_count == 3  # Should have retried 3 times
    
    @pytest.mark.asyncio
    async def test_fallback_strategy(self):
        """Test fallback recovery strategy"""
        manager = ExceptionRecoveryManager()
        
        def fallback_func():
            return "fallback_result"
        
        # Register handler with fallback
        manager.register_handler(
            ValueError,
            RecoveryStrategy.FALLBACK,
            {'fallback_func': fallback_func}
        )
        
        def failing_func():
            raise ValueError("Test error")
        
        result = await manager.execute_with_recovery(failing_func)
        assert result == "fallback_result"
    
    def test_exception_stats(self):
        """Test exception statistics"""
        manager = ExceptionRecoveryManager()
        
        stats = manager.get_exception_stats()
        assert 'overall_stats' in stats
        assert 'handler_stats' in stats
        assert 'recent_exceptions' in stats


class TestPerformanceMonitor:
    """Test performance monitoring functionality"""
    
    def test_metrics_collection(self):
        """Test metrics collection"""
        monitor = PerformanceMonitor()
        
        # Add custom metric
        monitor.add_custom_metric('test_metric', 42.0, 'units', {'category': 'test'})
        
        # Get summary
        summary = monitor.get_metrics_summary('test')
        assert 'test_metric' in summary['test']
        assert summary['test']['test_metric']['latest'] == 42.0
    
    def test_performance_report(self):
        """Test performance report generation"""
        monitor = PerformanceMonitor()
        
        report = monitor.get_performance_report()
        assert 'current_state' in report
        assert 'historical_summary' in report
        assert 'uptime' in report
        assert 'monitoring_active' in report


class TestAdvancedFeaturesService:
    """Test advanced features service integration"""
    
    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test service initialization"""
        service = AdvancedFeaturesService()
        
        await service.initialize()
        assert service.initialized
        assert service.running
        
        # Test status
        status = service.get_comprehensive_status()
        assert 'service_status' in status
        assert status['service_status']['initialized']
        assert status['service_status']['running']
        
        await service.shutdown()
        assert not service.running
    
    def test_config_management(self):
        """Test configuration management"""
        service = AdvancedFeaturesService()
        
        # Test config update
        new_config = {
            'memory_management': {
                'gc_threshold': 0.9
            }
        }
        
        service.update_config(new_config)
        assert service.config['memory_management']['gc_threshold'] == 0.9
    
    @pytest.mark.asyncio
    async def test_execute_with_recovery(self):
        """Test execution with recovery"""
        service = AdvancedFeaturesService()
        await service.initialize()
        
        async def test_func():
            return "test_result"
        
        result = await service.execute_with_recovery(test_func)
        assert result == "test_result"
        
        await service.shutdown()


if __name__ == "__main__":
    pytest.main([__file__])