"""
Thread pool management for download operations.
"""
import asyncio
import concurrent.futures
import threading
from typing import Optional, Callable, Any, Dict, List
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ThreadPoolStats:
    """Thread pool statistics"""
    max_workers: int
    active_workers: int
    queued_tasks: int
    completed_tasks: int
    failed_tasks: int
    created_at: datetime
    
    @property
    def utilization_percentage(self) -> float:
        """Calculate thread pool utilization percentage"""
        if self.max_workers == 0:
            return 0.0
        return (self.active_workers / self.max_workers) * 100


class ThreadPoolManager:
    """
    Manages thread pools for download operations.
    Provides configurable thread pools with monitoring and dynamic scaling.
    """
    
    def __init__(self, max_workers: int = 4, thread_name_prefix: str = "DownloadWorker"):
        self.max_workers = max_workers
        self.thread_name_prefix = thread_name_prefix
        self._executor: Optional[concurrent.futures.ThreadPoolExecutor] = None
        self._active_tasks: Dict[str, concurrent.futures.Future] = {}
        self._completed_tasks = 0
        self._failed_tasks = 0
        self._created_at = datetime.now()
        self._lock = threading.Lock()
        self._shutdown = False
        
        # Initialize the thread pool
        self._create_executor()
    
    def _create_executor(self) -> None:
        """Create the thread pool executor"""
        if self._executor is not None:
            self._executor.shutdown(wait=False)
        
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix=self.thread_name_prefix
        )
        
        logger.info(f"Created thread pool with {self.max_workers} workers")
    
    async def submit_task(self, 
                         task_id: str, 
                         func: Callable, 
                         *args, 
                         **kwargs) -> concurrent.futures.Future:
        """
        Submit a task to the thread pool.
        
        Args:
            task_id: Unique identifier for the task
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Future object representing the task
        """
        if self._shutdown:
            raise RuntimeError("Thread pool is shut down")
        
        if self._executor is None:
            raise RuntimeError("Thread pool not initialized")
        
        with self._lock:
            if task_id in self._active_tasks:
                raise ValueError(f"Task {task_id} is already active")
            
            # Submit the task
            future = self._executor.submit(self._wrap_task, task_id, func, *args, **kwargs)
            self._active_tasks[task_id] = future
            
            logger.debug(f"Submitted task {task_id} to thread pool")
            return future
    
    def _wrap_task(self, task_id: str, func: Callable, *args, **kwargs) -> Any:
        """Wrapper for tasks to handle completion tracking"""
        try:
            logger.debug(f"Starting task {task_id} in thread {threading.current_thread().name}")
            result = func(*args, **kwargs)
            
            # Don't remove from active_tasks here - let wait_for_task handle it
            with self._lock:
                self._completed_tasks += 1
            
            logger.debug(f"Completed task {task_id}")
            return result
            
        except Exception as e:
            # Don't remove from active_tasks here - let wait_for_task handle it
            with self._lock:
                self._failed_tasks += 1
            
            logger.error(f"Task {task_id} failed: {e}")
            raise e
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if task was cancelled, False if not found or already completed
        """
        with self._lock:
            if task_id not in self._active_tasks:
                return False
            
            future = self._active_tasks[task_id]
            cancelled = future.cancel()
            
            if cancelled:
                del self._active_tasks[task_id]
                logger.info(f"Cancelled task {task_id}")
            
            return cancelled
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Wait for a specific task to complete.
        
        Args:
            task_id: ID of the task to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            Task result
            
        Raises:
            KeyError: If task not found
            TimeoutError: If timeout exceeded
            Exception: If task failed
        """
        with self._lock:
            if task_id not in self._active_tasks:
                raise KeyError(f"Task {task_id} not found")
            
            future = self._active_tasks[task_id]
        
        # Wait for completion
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None, 
                lambda: future.result(timeout=timeout)
            )
            
            # Clean up completed task
            with self._lock:
                if task_id in self._active_tasks:
                    del self._active_tasks[task_id]
            
            return result
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"Task {task_id} timed out after {timeout} seconds")
        except Exception as e:
            # Clean up failed task
            with self._lock:
                if task_id in self._active_tasks:
                    del self._active_tasks[task_id]
            raise e
    
    async def wait_for_all(self, timeout: Optional[float] = None) -> List[Any]:
        """
        Wait for all active tasks to complete.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            List of task results
        """
        with self._lock:
            futures = list(self._active_tasks.values())
        
        if not futures:
            return []
        
        loop = asyncio.get_event_loop()
        try:
            done, pending = await loop.run_in_executor(
                None,
                lambda: concurrent.futures.wait(futures, timeout=timeout)
            )
            
            results = []
            for future in done:
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.error(f"Task failed: {e}")
                    results.append(e)
            
            return results
            
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"Not all tasks completed within {timeout} seconds")
    
    def get_stats(self) -> ThreadPoolStats:
        """Get thread pool statistics"""
        with self._lock:
            return ThreadPoolStats(
                max_workers=self.max_workers,
                active_workers=len(self._active_tasks),
                queued_tasks=self._get_queued_task_count(),
                completed_tasks=self._completed_tasks,
                failed_tasks=self._failed_tasks,
                created_at=self._created_at
            )
    
    def _get_queued_task_count(self) -> int:
        """Get number of queued tasks (approximation)"""
        if self._executor is None:
            return 0
        
        # This is an approximation since ThreadPoolExecutor doesn't expose queue size
        # We can estimate based on submitted vs active tasks
        return max(0, len(self._active_tasks) - self.max_workers)
    
    def resize_pool(self, new_max_workers: int) -> None:
        """
        Resize the thread pool.
        
        Args:
            new_max_workers: New maximum number of workers
        """
        if new_max_workers <= 0:
            raise ValueError("max_workers must be positive")
        
        if new_max_workers == self.max_workers:
            return
        
        old_max_workers = self.max_workers
        self.max_workers = new_max_workers
        
        # Recreate the executor with new size
        self._create_executor()
        
        logger.info(f"Resized thread pool from {old_max_workers} to {new_max_workers} workers")
    
    def is_task_active(self, task_id: str) -> bool:
        """Check if a task is currently active"""
        with self._lock:
            return task_id in self._active_tasks
    
    def get_active_task_ids(self) -> List[str]:
        """Get list of active task IDs"""
        with self._lock:
            return list(self._active_tasks.keys())
    
    async def shutdown(self, wait: bool = True, timeout: Optional[float] = None) -> None:
        """
        Shutdown the thread pool.
        
        Args:
            wait: Whether to wait for active tasks to complete
            timeout: Maximum time to wait for shutdown
        """
        self._shutdown = True
        
        if self._executor is None:
            return
        
        logger.info("Shutting down thread pool...")
        
        if wait:
            # Wait for active tasks to complete
            try:
                await self.wait_for_all(timeout=timeout)
            except TimeoutError:
                logger.warning("Some tasks did not complete before shutdown timeout")
        
        # Shutdown the executor
        self._executor.shutdown(wait=wait)
        self._executor = None
        
        with self._lock:
            self._active_tasks.clear()
        
        logger.info("Thread pool shut down")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Note: This is synchronous, so we can't use await
        if self._executor:
            self._executor.shutdown(wait=True)


class AdaptiveThreadPoolManager(ThreadPoolManager):
    """
    Thread pool manager with adaptive scaling based on workload.
    Automatically adjusts the number of workers based on queue size and performance.
    """
    
    def __init__(self, 
                 initial_workers: int = 2,
                 min_workers: int = 1,
                 max_workers: int = 8,
                 scale_up_threshold: int = 5,
                 scale_down_threshold: int = 2,
                 thread_name_prefix: str = "AdaptiveWorker"):
        
        self.min_workers = min_workers
        self.max_workers_limit = max_workers
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        self._last_scale_time = datetime.now()
        self._scale_cooldown = 30  # seconds
        
        super().__init__(initial_workers, thread_name_prefix)
        
        # Start adaptive scaling task
        self._scaling_task = None
        self._scaling_enabled = True
    
    async def start_adaptive_scaling(self) -> None:
        """Start the adaptive scaling background task"""
        if self._scaling_task is None:
            self._scaling_task = asyncio.create_task(self._adaptive_scaling_loop())
            logger.info("Started adaptive thread pool scaling")
    
    async def stop_adaptive_scaling(self) -> None:
        """Stop the adaptive scaling background task"""
        self._scaling_enabled = False
        if self._scaling_task:
            self._scaling_task.cancel()
            try:
                await self._scaling_task
            except asyncio.CancelledError:
                pass
            self._scaling_task = None
        logger.info("Stopped adaptive thread pool scaling")
    
    async def _adaptive_scaling_loop(self) -> None:
        """Background loop for adaptive scaling"""
        while self._scaling_enabled:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                await self._check_and_scale()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in adaptive scaling: {e}")
    
    async def _check_and_scale(self) -> None:
        """Check if scaling is needed and perform it"""
        now = datetime.now()
        time_since_last_scale = (now - self._last_scale_time).total_seconds()
        
        # Don't scale too frequently
        if time_since_last_scale < self._scale_cooldown:
            return
        
        stats = self.get_stats()
        
        # Scale up if queue is building up
        if (stats.queued_tasks >= self.scale_up_threshold and 
            stats.max_workers < self.max_workers_limit):
            
            new_workers = min(stats.max_workers + 1, self.max_workers_limit)
            self.resize_pool(new_workers)
            self._last_scale_time = now
            logger.info(f"Scaled up to {new_workers} workers (queue: {stats.queued_tasks})")
        
        # Scale down if utilization is low
        elif (stats.active_workers <= self.scale_down_threshold and 
              stats.max_workers > self.min_workers):
            
            new_workers = max(stats.max_workers - 1, self.min_workers)
            self.resize_pool(new_workers)
            self._last_scale_time = now
            logger.info(f"Scaled down to {new_workers} workers (active: {stats.active_workers})")
    
    async def shutdown(self, wait: bool = True, timeout: Optional[float] = None) -> None:
        """Shutdown with adaptive scaling cleanup"""
        await self.stop_adaptive_scaling()
        await super().shutdown(wait, timeout)
# Backward compatibility alias
ThreadPool = ThreadPoolManager