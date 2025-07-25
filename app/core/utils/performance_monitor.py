"""
Performance monitoring and logging system
"""
import time
import threading
import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import psutil
import os


@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    name: str
    value: float
    timestamp: float
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'value': self.value,
            'timestamp': self.timestamp,
            'unit': self.unit,
            'tags': self.tags
        }


class MetricsCollector:
    """Collect system and application metrics"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_time = time.time()
        self.last_cpu_times = self.process.cpu_times()
        self.last_check_time = time.time()
    
    def collect_system_metrics(self) -> List[PerformanceMetric]:
        """Collect system-level metrics"""
        metrics = []
        current_time = time.time()
        
        # Memory metrics
        memory_info = self.process.memory_info()
        metrics.append(PerformanceMetric(
            name="memory.rss",
            value=memory_info.rss,
            timestamp=current_time,
            unit="bytes"
        ))
        
        metrics.append(PerformanceMetric(
            name="memory.vms",
            value=memory_info.vms,
            timestamp=current_time,
            unit="bytes"
        ))
        
        metrics.append(PerformanceMetric(
            name="memory.percent",
            value=self.process.memory_percent(),
            timestamp=current_time,
            unit="percent"
        ))
        
        # CPU metrics
        cpu_percent = self.process.cpu_percent()
        metrics.append(PerformanceMetric(
            name="cpu.percent",
            value=cpu_percent,
            timestamp=current_time,
            unit="percent"
        ))
        
        # Thread count
        metrics.append(PerformanceMetric(
            name="threads.count",
            value=self.process.num_threads(),
            timestamp=current_time,
            unit="count"
        ))
        
        # File descriptors (on Unix systems)
        try:
            metrics.append(PerformanceMetric(
                name="files.open",
                value=self.process.num_fds(),
                timestamp=current_time,
                unit="count"
            ))
        except AttributeError:
            # Windows doesn't have num_fds
            pass
        
        return metrics
    
    def collect_network_metrics(self) -> List[PerformanceMetric]:
        """Collect network-related metrics"""
        metrics = []
        current_time = time.time()
        
        try:
            net_io = self.process.net_io_counters()
            if net_io:
                metrics.append(PerformanceMetric(
                    name="network.bytes_sent",
                    value=net_io.bytes_sent,
                    timestamp=current_time,
                    unit="bytes"
                ))
                
                metrics.append(PerformanceMetric(
                    name="network.bytes_recv",
                    value=net_io.bytes_recv,
                    timestamp=current_time,
                    unit="bytes"
                ))
        except AttributeError:
            # Some systems don't support per-process network stats
            pass
        
        return metrics


class PerformanceMonitor:
    """Central performance monitoring system"""
    
    def __init__(self, log_file: Optional[str] = None, collection_interval: float = 60.0):
        self.log_file = log_file
        self.collection_interval = collection_interval
        self.metrics_collector = MetricsCollector()
        self.custom_metrics: Dict[str, List[PerformanceMetric]] = {}
        self.running = False
        self.monitor_thread = None
        self.lock = threading.Lock()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        if log_file:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def start_monitoring(self):
        """Start performance monitoring"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        self.logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Collect system metrics
                system_metrics = self.metrics_collector.collect_system_metrics()
                network_metrics = self.metrics_collector.collect_network_metrics()
                
                all_metrics = system_metrics + network_metrics
                
                # Log metrics
                self._log_metrics(all_metrics)
                
                # Store metrics for analysis
                with self.lock:
                    timestamp = time.time()
                    if 'system' not in self.custom_metrics:
                        self.custom_metrics['system'] = []
                    
                    # Keep only last 1000 metrics to prevent memory growth
                    if len(self.custom_metrics['system']) > 1000:
                        self.custom_metrics['system'] = self.custom_metrics['system'][-500:]
                    
                    self.custom_metrics['system'].extend(all_metrics)
                
                time.sleep(self.collection_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5.0)  # Wait before retrying
    
    def _log_metrics(self, metrics: List[PerformanceMetric]):
        """Log metrics to file"""
        if self.log_file:
            try:
                log_path = Path(self.log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(log_path, 'a', encoding='utf-8') as f:
                    for metric in metrics:
                        f.write(json.dumps(metric.to_dict()) + '\n')
                        
            except Exception as e:
                self.logger.error(f"Failed to log metrics: {e}")
    
    def add_custom_metric(self, name: str, value: float, unit: str = "", tags: Optional[Dict[str, str]] = None):
        """Add a custom metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=time.time(),
            unit=unit,
            tags=tags or {}
        )
        
        with self.lock:
            category = tags.get('category', 'custom') if tags else 'custom'
            if category not in self.custom_metrics:
                self.custom_metrics[category] = []
            
            # Keep only last 1000 metrics per category
            if len(self.custom_metrics[category]) > 1000:
                self.custom_metrics[category] = self.custom_metrics[category][-500:]
            
            self.custom_metrics[category].append(metric)
    
    def get_metrics_summary(self, category: Optional[str] = None, 
                          last_minutes: Optional[int] = None) -> Dict[str, Any]:
        """Get metrics summary"""
        with self.lock:
            summary = {}
            
            categories = [category] if category else list(self.custom_metrics.keys())
            
            for cat in categories:
                if cat not in self.custom_metrics:
                    continue
                
                metrics = self.custom_metrics[cat]
                
                # Filter by time if specified
                if last_minutes:
                    cutoff_time = time.time() - (last_minutes * 60)
                    metrics = [m for m in metrics if m.timestamp > cutoff_time]
                
                if not metrics:
                    continue
                
                # Group by metric name
                by_name = {}
                for metric in metrics:
                    if metric.name not in by_name:
                        by_name[metric.name] = []
                    by_name[metric.name].append(metric.value)
                
                # Calculate statistics
                cat_summary = {}
                for name, values in by_name.items():
                    if values:
                        cat_summary[name] = {
                            'count': len(values),
                            'min': min(values),
                            'max': max(values),
                            'avg': sum(values) / len(values),
                            'latest': values[-1]
                        }
                
                summary[cat] = cat_summary
            
            return summary
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        current_metrics = self.metrics_collector.collect_system_metrics()
        current_network = self.metrics_collector.collect_network_metrics()
        
        # Current system state
        current_state = {}
        for metric in current_metrics + current_network:
            current_state[metric.name] = {
                'value': metric.value,
                'unit': metric.unit,
                'timestamp': metric.timestamp
            }
        
        # Historical summary
        historical_summary = self.get_metrics_summary(last_minutes=60)  # Last hour
        
        return {
            'current_state': current_state,
            'historical_summary': historical_summary,
            'uptime': time.time() - self.metrics_collector.start_time,
            'monitoring_active': self.running
        }


# Global performance monitor instance
performance_monitor = PerformanceMonitor(
    log_file="logs/performance.log",
    collection_interval=30.0  # Collect metrics every 30 seconds
)