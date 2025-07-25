"""
Performance optimization utilities for handling large-scale download tasks
"""
import asyncio
import threading
import time
import queue
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class PerformanceTask:
    """Performance-optimized task wrapper"""
    id: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    
    def __lt__(self, other):
        """For priority queue ordering"""
        return self.priority.value > other.priority.value


class BatchProcessor:
    """Batch processing for improved performance"""
    
    def __init__(self, batch_size: int = 50, max_workers: int = 10):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.pending_tasks = []
        self.lock = threading.Lock()
        self.stats = {
            'processed': 0,
            'failed': 0,
            'batches': 0,
            'avg_batch_time': 0.0
        }
    
    def add_task(self, task: PerformanceTask):
        """Add task to batch"""
        with self.lock:
            self.pending_tasks.append(task)
            
            # Process batch if full
            if len(self.pending_tasks) >= self.batch_size:
                self._process_batch()
    
    def _process_batch(self):
        """Process current batch of tasks"""
        if not self.pending_tasks:
            return
        
        batch = self.pending_tasks.copy()
        self.pending_tasks.clear()
        
        start_time = time.time()
        
        # Submit batch to thread pool
        future = self.executor.submit(self._execute_batch, batch)
        
        # Update stats
        self.stats['batches'] += 1
        
        return future
    
    def _execute_batch(self, batch: List[PerformanceTask]) -> Dict[str, Any]:
        """Execute a batch of tasks"""
        results = {'success': [], 'failed': []}
        
        for task in batch:
            try:
                if asyncio.iscoroutinefunction(task.func):
                    # Handle async functions
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(
                            asyncio.wait_for(task.func(*task.args, **task.kwargs), 
                                           timeout=task.timeout)
                        )
                        results['success'].append({'task_id': task.id, 'result': result})
                    finally:
                        loop.close()
                else:
                    # Handle sync functions
                    result = task.func(*task.args, **task.kwargs)
                    results['success'].append({'task_id': task.id, 'result': result})
                
                self.stats['processed'] += 1
                
            except Exception as e:
                logger.error(f"Task {task.id} failed: {e}")
                results['failed'].append({'task_id': task.id, 'error': str(e)})
                self.stats['failed'] += 1
        
        return results
    
    def flush(self):
        """Process remaining tasks"""
        with self.lock:
            if self.pending_tasks:
                return self._process_batch()
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return self.stats.copy()
    
    def shutdown(self):
        """Shutdown the batch processor"""
        self.flush()
        self.executor.shutdown(wait=True)


class AdaptiveRateLimiter:
    """Adaptive rate limiter that adjusts based on performance"""
    
    def __init__(self, initial_rate: float = 10.0, min_rate: float = 1.0, max_rate: float = 100.0):
        self.current_rate = initial_rate
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.last_request = 0.0
        self.success_count = 0
        self.error_count = 0
        self.adjustment_threshold = 10
        self.lock = threading.Lock()
    
    async def acquire(self):
        """Acquire permission to proceed"""
        with self.lock:
            now = time.time()
            time_since_last = now - self.last_request
            required_interval = 1.0 / self.current_rate
            
            if time_since_last < required_interval:
                sleep_time = required_interval - time_since_last
                await asyncio.sleep(sleep_time)
            
            self.last_request = time.time()
    
    def record_success(self):
        """Record a successful operation"""
        with self.lock:
            self.success_count += 1
            self._adjust_rate()
    
    def record_error(self):
        """Record a failed operation"""
        with self.lock:
            self.error_count += 1
            self._adjust_rate()
    
    def _adjust_rate(self):
        """Adjust rate based on success/error ratio"""
        total_requests = self.success_count + self.error_count
        
        if total_requests >= self.adjustment_threshold:
            success_rate = self.success_count / total_requests
            
            if success_rate > 0.9:
                # High success rate, increase rate
                self.current_rate = min(self.current_rate * 1.1, self.max_rate)
            elif success_rate < 0.7:
                # Low success rate, decrease rate
                self.current_rate = max(self.current_rate * 0.8, self.min_rate)
            
            # Reset counters
            self.success_count = 0
            self.error_count = 0
    
    def get_current_rate(self) -> float:
        """Get current rate limit"""
        return self.current_rate


class CircuitBreaker:
    """Circuit breaker for handling failures"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self.lock:
            if self.state == 'OPEN':
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = 'HALF_OPEN'
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise e
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        if self.state == 'HALF_OPEN':
            self.state = 'CLOSED'
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
    
    def get_state(self) -> str:
        """Get current circuit breaker state"""
        return self.state


class PerformanceOptimizer:
    """Main performance optimization coordinator"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        self.batch_processor = BatchProcessor(
            batch_size=config.get('batch_size', 50),
            max_workers=config.get('max_workers', 10)
        )
        
        self.rate_limiter = AdaptiveRateLimiter(
            initial_rate=config.get('initial_rate', 10.0),
            min_rate=config.get('min_rate', 1.0),
            max_rate=config.get('max_rate', 100.0)
        )
        
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.get('failure_threshold', 5),
            recovery_timeout=config.get('recovery_timeout', 60.0)
        )
        
        self.task_queue = queue.PriorityQueue()
        self.running = False
        self.worker_thread = None
        self.stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'start_time': time.time()
        }
    
    def start(self):
        """Start the performance optimizer"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop)
            self.worker_thread.start()
    
    def stop(self):
        """Stop the performance optimizer"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join()
        self.batch_processor.shutdown()
    
    def submit_task(self, task: PerformanceTask):
        """Submit a task for optimized processing"""
        self.task_queue.put(task)
        self.stats['tasks_submitted'] += 1
    
    def _worker_loop(self):
        """Main worker loop"""
        while self.running:
            try:
                # Get task with timeout
                task = self.task_queue.get(timeout=1.0)
                
                # Process task with optimizations
                self._process_task_optimized(task)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
    
    def _process_task_optimized(self, task: PerformanceTask):
        """Process task with all optimizations applied"""
        try:
            # Apply rate limiting
            if asyncio.iscoroutinefunction(task.func):
                asyncio.run(self.rate_limiter.acquire())
            
            # Use circuit breaker
            def wrapped_func():
                return self.batch_processor.add_task(task)
            
            self.circuit_breaker.call(wrapped_func)
            self.rate_limiter.record_success()
            self.stats['tasks_completed'] += 1
            
        except Exception as e:
            logger.error(f"Task processing failed: {e}")
            self.rate_limiter.record_error()
            self.stats['tasks_failed'] += 1
            
            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                self.task_queue.put(task)
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        uptime = time.time() - self.stats['start_time']
        
        return {
            'optimizer_stats': self.stats,
            'batch_processor_stats': self.batch_processor.get_stats(),
            'rate_limiter_rate': self.rate_limiter.get_current_rate(),
            'circuit_breaker_state': self.circuit_breaker.get_state(),
            'uptime': uptime,
            'tasks_per_second': self.stats['tasks_completed'] / max(1, uptime),
            'success_rate': self.stats['tasks_completed'] / max(1, self.stats['tasks_submitted'])
        }


# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()