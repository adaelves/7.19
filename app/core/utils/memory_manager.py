"""
Memory management utilities for performance optimization
"""
import gc
import threading
import weakref
from typing import Dict, List, Any, Optional, Type, TypeVar
from collections import defaultdict
import psutil
import os

T = TypeVar('T')


class ObjectPool:
    """Generic object pool for reusing objects"""
    
    def __init__(self, factory_func, max_size: int = 100):
        self.factory_func = factory_func
        self.max_size = max_size
        self.pool = []
        self.lock = threading.Lock()
        self.created_count = 0
        self.reused_count = 0
    
    def acquire(self):
        """Get an object from the pool"""
        with self.lock:
            if self.pool:
                obj = self.pool.pop()
                self.reused_count += 1
                return obj
            else:
                obj = self.factory_func()
                self.created_count += 1
                return obj
    
    def release(self, obj):
        """Return an object to the pool"""
        with self.lock:
            if len(self.pool) < self.max_size:
                # Reset object state if it has a reset method
                if hasattr(obj, 'reset'):
                    obj.reset()
                self.pool.append(obj)
    
    def get_stats(self) -> Dict[str, int]:
        """Get pool statistics"""
        return {
            'pool_size': len(self.pool),
            'created_count': self.created_count,
            'reused_count': self.reused_count,
            'hit_rate': self.reused_count / max(1, self.created_count + self.reused_count)
        }


class LRUCache:
    """LRU Cache implementation for metadata caching"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = {}
        self.access_order = []
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.access_order.remove(key)
                self.access_order.append(key)
                self.hits += 1
                return self.cache[key]
            else:
                self.misses += 1
                return None
    
    def put(self, key: str, value: Any):
        """Put value into cache"""
        with self.lock:
            if key in self.cache:
                # Update existing
                self.access_order.remove(key)
            elif len(self.cache) >= self.max_size:
                # Remove least recently used
                lru_key = self.access_order.pop(0)
                del self.cache[lru_key]
            
            self.cache[key] = value
            self.access_order.append(key)
    
    def clear(self):
        """Clear cache"""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hits / max(1, total_requests),
            'usage_rate': len(self.cache) / self.max_size
        }


class WeakReferenceManager:
    """Manage weak references to prevent memory leaks"""
    
    def __init__(self):
        self.references = defaultdict(list)
        self.lock = threading.Lock()
    
    def add_reference(self, category: str, obj: Any, callback=None):
        """Add a weak reference"""
        with self.lock:
            weak_ref = weakref.ref(obj, callback)
            self.references[category].append(weak_ref)
    
    def cleanup_category(self, category: str):
        """Clean up dead references in a category"""
        with self.lock:
            if category in self.references:
                alive_refs = [ref for ref in self.references[category] if ref() is not None]
                dead_count = len(self.references[category]) - len(alive_refs)
                self.references[category] = alive_refs
                return dead_count
            return 0
    
    def cleanup_all(self):
        """Clean up all dead references"""
        total_cleaned = 0
        with self.lock:
            for category in list(self.references.keys()):
                total_cleaned += self.cleanup_category(category)
        return total_cleaned
    
    def get_stats(self) -> Dict[str, int]:
        """Get reference statistics"""
        with self.lock:
            stats = {}
            for category, refs in self.references.items():
                alive_count = sum(1 for ref in refs if ref() is not None)
                stats[category] = {
                    'total': len(refs),
                    'alive': alive_count,
                    'dead': len(refs) - alive_count
                }
            return stats


class MemoryManager:
    """Central memory management system"""
    
    def __init__(self):
        self.object_pools = {}
        self.lru_cache = LRUCache(max_size=2000)
        self.weak_ref_manager = WeakReferenceManager()
        self.gc_threshold = 0.8  # Trigger GC when memory usage > 80%
        self.monitoring_enabled = True
        self.lock = threading.Lock()
    
    def create_object_pool(self, name: str, factory_func, max_size: int = 100) -> ObjectPool:
        """Create a new object pool"""
        with self.lock:
            pool = ObjectPool(factory_func, max_size)
            self.object_pools[name] = pool
            return pool
    
    def get_object_pool(self, name: str) -> Optional[ObjectPool]:
        """Get an existing object pool"""
        return self.object_pools.get(name)
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage statistics"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            'rss': memory_info.rss,  # Resident Set Size
            'vms': memory_info.vms,  # Virtual Memory Size
            'percent': process.memory_percent(),
            'available': psutil.virtual_memory().available,
            'total': psutil.virtual_memory().total
        }
    
    def should_trigger_gc(self) -> bool:
        """Check if garbage collection should be triggered"""
        if not self.monitoring_enabled:
            return False
        
        memory_usage = self.get_memory_usage()
        memory_percent = memory_usage['percent']
        
        return memory_percent > self.gc_threshold * 100
    
    def force_garbage_collection(self) -> Dict[str, int]:
        """Force garbage collection and return statistics"""
        # Clean up weak references first
        cleaned_refs = self.weak_ref_manager.cleanup_all()
        
        # Run garbage collection
        collected = []
        for generation in range(3):
            collected.append(gc.collect(generation))
        
        return {
            'cleaned_weak_refs': cleaned_refs,
            'collected_gen0': collected[0],
            'collected_gen1': collected[1],
            'collected_gen2': collected[2],
            'total_collected': sum(collected)
        }
    
    def optimize_memory(self) -> Dict[str, Any]:
        """Perform memory optimization"""
        stats = {}
        
        # Check if optimization is needed
        if self.should_trigger_gc():
            stats['gc_stats'] = self.force_garbage_collection()
            stats['triggered_gc'] = True
        else:
            stats['triggered_gc'] = False
        
        # Clear cache if memory pressure is high
        memory_usage = self.get_memory_usage()
        if memory_usage['percent'] > 90:
            self.lru_cache.clear()
            stats['cleared_cache'] = True
        else:
            stats['cleared_cache'] = False
        
        stats['memory_usage'] = memory_usage
        return stats
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory and performance statistics"""
        stats = {
            'memory_usage': self.get_memory_usage(),
            'cache_stats': self.lru_cache.get_stats(),
            'weak_ref_stats': self.weak_ref_manager.get_stats(),
            'object_pools': {}
        }
        
        # Get object pool statistics
        for name, pool in self.object_pools.items():
            stats['object_pools'][name] = pool.get_stats()
        
        return stats
    
    def set_monitoring_enabled(self, enabled: bool):
        """Enable or disable memory monitoring"""
        self.monitoring_enabled = enabled
    
    def set_gc_threshold(self, threshold: float):
        """Set garbage collection threshold (0.0 - 1.0)"""
        if 0.0 <= threshold <= 1.0:
            self.gc_threshold = threshold


# Global memory manager instance
memory_manager = MemoryManager()