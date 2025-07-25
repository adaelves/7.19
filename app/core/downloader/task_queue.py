"""
Task queue system for managing download tasks.
"""
import asyncio
import heapq
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime
import uuid

from app.data.models.core import DownloadTask, TaskStatus

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class QueuedTask:
    """Task wrapper for queue management"""
    task: DownloadTask
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3
    
    def __lt__(self, other):
        """Comparison for priority queue (higher priority first)"""
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value
        return self.created_at < other.created_at


class TaskQueue:
    """
    Priority-based task queue for download management.
    Supports task prioritization, retry logic, and concurrent execution limits.
    """
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self._queue: List[QueuedTask] = []
        self._active_tasks: Dict[str, QueuedTask] = {}
        self._completed_tasks: List[QueuedTask] = []
        self._failed_tasks: List[QueuedTask] = []
        self._lock = asyncio.Lock()
        self._task_callbacks: Dict[str, Callable] = {}
        self._queue_callbacks: List[Callable] = []
        
    async def add_task(self, task: DownloadTask, priority: TaskPriority = TaskPriority.NORMAL) -> None:
        """Add a task to the queue"""
        async with self._lock:
            queued_task = QueuedTask(task=task, priority=priority)
            heapq.heappush(self._queue, queued_task)
            
            logger.info(f"Added task {task.id} to queue with priority {priority.name}")
            await self._notify_queue_changed()
    
    async def get_next_task(self) -> Optional[QueuedTask]:
        """Get the next task from the queue"""
        async with self._lock:
            if not self._queue:
                return None
            
            if len(self._active_tasks) >= self.max_concurrent:
                return None
            
            queued_task = heapq.heappop(self._queue)
            self._active_tasks[queued_task.task.id] = queued_task
            
            logger.info(f"Retrieved task {queued_task.task.id} from queue")
            await self._notify_queue_changed()
            
            return queued_task
    
    async def complete_task(self, task_id: str, success: bool = True) -> None:
        """Mark a task as completed"""
        async with self._lock:
            if task_id not in self._active_tasks:
                logger.warning(f"Task {task_id} not found in active tasks")
                return
            
            queued_task = self._active_tasks.pop(task_id)
            
            if success:
                queued_task.task.status = TaskStatus.COMPLETED
                self._completed_tasks.append(queued_task)
                logger.info(f"Task {task_id} completed successfully")
            else:
                # Handle retry logic
                if queued_task.retry_count < queued_task.max_retries:
                    queued_task.retry_count += 1
                    queued_task.task.status = TaskStatus.PENDING
                    heapq.heappush(self._queue, queued_task)
                    logger.info(f"Task {task_id} failed, retrying ({queued_task.retry_count}/{queued_task.max_retries})")
                else:
                    queued_task.task.status = TaskStatus.FAILED
                    self._failed_tasks.append(queued_task)
                    logger.error(f"Task {task_id} failed permanently after {queued_task.max_retries} retries")
            
            await self._notify_queue_changed()
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        async with self._lock:
            # Check if task is in queue
            for i, queued_task in enumerate(self._queue):
                if queued_task.task.id == task_id:
                    self._queue.pop(i)
                    heapq.heapify(self._queue)  # Restore heap property
                    queued_task.task.status = TaskStatus.CANCELLED
                    logger.info(f"Cancelled queued task {task_id}")
                    await self._notify_queue_changed()
                    return True
            
            # Check if task is active
            if task_id in self._active_tasks:
                queued_task = self._active_tasks.pop(task_id)
                queued_task.task.status = TaskStatus.CANCELLED
                logger.info(f"Cancelled active task {task_id}")
                await self._notify_queue_changed()
                return True
            
            logger.warning(f"Task {task_id} not found for cancellation")
            return False
    
    async def pause_task(self, task_id: str) -> bool:
        """Pause a task"""
        async with self._lock:
            if task_id in self._active_tasks:
                self._active_tasks[task_id].task.status = TaskStatus.PAUSED
                logger.info(f"Paused task {task_id}")
                await self._notify_queue_changed()
                return True
            
            logger.warning(f"Task {task_id} not found for pausing")
            return False
    
    async def resume_task(self, task_id: str) -> bool:
        """Resume a paused task"""
        async with self._lock:
            if task_id in self._active_tasks:
                task = self._active_tasks[task_id].task
                if task.status == TaskStatus.PAUSED:
                    task.status = TaskStatus.DOWNLOADING
                    logger.info(f"Resumed task {task_id}")
                    await self._notify_queue_changed()
                    return True
            
            logger.warning(f"Task {task_id} not found for resuming")
            return False
    
    async def clear_completed(self) -> None:
        """Clear completed tasks from history"""
        async with self._lock:
            cleared_count = len(self._completed_tasks)
            self._completed_tasks.clear()
            logger.info(f"Cleared {cleared_count} completed tasks")
            await self._notify_queue_changed()
    
    async def clear_failed(self) -> None:
        """Clear failed tasks from history"""
        async with self._lock:
            cleared_count = len(self._failed_tasks)
            self._failed_tasks.clear()
            logger.info(f"Cleared {cleared_count} failed tasks")
            await self._notify_queue_changed()
    
    async def retry_failed_tasks(self) -> None:
        """Retry all failed tasks"""
        async with self._lock:
            retry_count = 0
            for queued_task in self._failed_tasks[:]:  # Copy list to avoid modification during iteration
                queued_task.retry_count = 0  # Reset retry count
                queued_task.task.status = TaskStatus.PENDING
                heapq.heappush(self._queue, queued_task)
                self._failed_tasks.remove(queued_task)
                retry_count += 1
            
            logger.info(f"Retrying {retry_count} failed tasks")
            await self._notify_queue_changed()
    
    def set_max_concurrent(self, max_concurrent: int) -> None:
        """Set maximum concurrent tasks"""
        self.max_concurrent = max(1, max_concurrent)
        logger.info(f"Set max concurrent tasks to {self.max_concurrent}")
    
    def add_queue_callback(self, callback: Callable) -> None:
        """Add callback for queue state changes"""
        self._queue_callbacks.append(callback)
    
    def remove_queue_callback(self, callback: Callable) -> None:
        """Remove queue callback"""
        if callback in self._queue_callbacks:
            self._queue_callbacks.remove(callback)
    
    async def _notify_queue_changed(self) -> None:
        """Notify all callbacks about queue changes"""
        for callback in self._queue_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self.get_queue_status())
                else:
                    callback(self.get_queue_status())
            except Exception as e:
                logger.error(f"Error in queue callback: {e}")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            'queued_count': len(self._queue),
            'active_count': len(self._active_tasks),
            'completed_count': len(self._completed_tasks),
            'failed_count': len(self._failed_tasks),
            'max_concurrent': self.max_concurrent,
            'queued_tasks': [qt.task for qt in self._queue],
            'active_tasks': [qt.task for qt in self._active_tasks.values()],
            'completed_tasks': [qt.task for qt in self._completed_tasks],
            'failed_tasks': [qt.task for qt in self._failed_tasks]
        }
    
    def get_task_by_id(self, task_id: str) -> Optional[DownloadTask]:
        """Get task by ID from any queue"""
        # Check active tasks
        if task_id in self._active_tasks:
            return self._active_tasks[task_id].task
        
        # Check queued tasks
        for queued_task in self._queue:
            if queued_task.task.id == task_id:
                return queued_task.task
        
        # Check completed tasks
        for queued_task in self._completed_tasks:
            if queued_task.task.id == task_id:
                return queued_task.task
        
        # Check failed tasks
        for queued_task in self._failed_tasks:
            if queued_task.task.id == task_id:
                return queued_task.task
        
        return None
    
    @property
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return len(self._queue) == 0 and len(self._active_tasks) == 0
    
    @property
    def has_capacity(self) -> bool:
        """Check if queue has capacity for more active tasks"""
        return len(self._active_tasks) < self.max_concurrent