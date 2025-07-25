"""
Advanced features service integrating performance optimization components
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class AdvancedFeaturesService:
    """Service for managing advanced performance and stability features"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config/advanced_features.json"
        self.config = self._load_config()
        self.initialized = False
        self.running = False
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load config from {self.config_file}: {e}")
        
        # Default configuration
        return {
            "memory_management": {
                "gc_threshold": 0.8,
                "cache_size": 2000,
                "monitoring_enabled": True
            },
            "connection_pool": {
                "max_connections": 100,
                "max_connections_per_host": 30,
                "connection_timeout": 30.0,
                "read_timeout": 300.0
            },
            "performance_optimizer": {
                "batch_size": 50,
                "max_workers": 10,
                "initial_rate": 10.0,
                "failure_threshold": 5
            },
            "performance_monitor": {
                "collection_interval": 30.0,
                "log_file": "logs/performance.log"
            }
        }
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Advanced features configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    async def initialize(self):
        """Initialize all advanced features"""
        if self.initialized:
            return
        
        try:
            from app.core.utils.memory_manager import memory_manager
            from app.core.utils.connection_pool import global_connection_manager, ConnectionConfig
            from app.core.utils.performance_optimizer import performance_optimizer
            from app.core.utils.exception_recovery import exception_recovery_manager
            from app.core.utils.performance_monitor import performance_monitor
            
            # Initialize memory manager
            memory_config = self.config.get("memory_management", {})
            memory_manager.set_gc_threshold(memory_config.get("gc_threshold", 0.8))
            memory_manager.set_monitoring_enabled(memory_config.get("monitoring_enabled", True))
            
            # Initialize connection pool
            conn_config = self.config.get("connection_pool", {})
            connection_config = ConnectionConfig(
                max_connections=conn_config.get("max_connections", 100),
                max_connections_per_host=conn_config.get("max_connections_per_host", 30),
                connection_timeout=conn_config.get("connection_timeout", 30.0),
                read_timeout=conn_config.get("read_timeout", 300.0)
            )
            await global_connection_manager.initialize(connection_config)
            
            # Initialize performance optimizer
            perf_config = self.config.get("performance_optimizer", {})
            performance_optimizer.__init__(perf_config)
            performance_optimizer.start()
            
            # Setup exception recovery handlers
            exception_recovery_manager.setup_common_handlers()
            
            # Start performance monitoring
            monitor_config = self.config.get("performance_monitor", {})
            performance_monitor.__init__(
                log_file=monitor_config.get("log_file", "logs/performance.log"),
                collection_interval=monitor_config.get("collection_interval", 30.0)
            )
            performance_monitor.start_monitoring()
            
            self.initialized = True
            self.running = True
            logger.info("Advanced features service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize advanced features: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown all advanced features"""
        if not self.running:
            return
        
        try:
            from app.core.utils.memory_manager import memory_manager
            from app.core.utils.connection_pool import global_connection_manager
            from app.core.utils.performance_optimizer import performance_optimizer
            from app.core.utils.performance_monitor import performance_monitor
            
            # Stop performance monitoring
            performance_monitor.stop_monitoring()
            
            # Stop performance optimizer
            performance_optimizer.stop()
            
            # Shutdown connection manager
            await global_connection_manager.shutdown()
            
            # Force memory cleanup
            memory_manager.optimize_memory()
            
            self.running = False
            logger.info("Advanced features service shut down")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all advanced features"""
        status = {
            "service_status": {
                "initialized": self.initialized,
                "running": self.running
            }
        }
        
        if self.running:
            try:
                from app.core.utils.memory_manager import memory_manager
                from app.core.utils.connection_pool import global_connection_manager
                from app.core.utils.performance_optimizer import performance_optimizer
                from app.core.utils.exception_recovery import exception_recovery_manager
                from app.core.utils.performance_monitor import performance_monitor
                
                # Memory manager stats
                status["memory_manager"] = memory_manager.get_comprehensive_stats()
                
                # Connection pool stats
                if global_connection_manager.get_manager():
                    status["connection_pool"] = global_connection_manager.get_manager().get_connection_stats()
                
                # Performance optimizer stats
                status["performance_optimizer"] = performance_optimizer.get_comprehensive_stats()
                
                # Exception recovery stats
                status["exception_recovery"] = exception_recovery_manager.get_exception_stats()
                
                # Performance monitor report
                status["performance_monitor"] = performance_monitor.get_performance_report()
                
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                status["error"] = str(e)
        
        return status
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update configuration"""
        self.config.update(new_config)
        self._save_config()
        logger.info("Advanced features configuration updated")
    
    def add_performance_metric(self, name: str, value: float, unit: str = "", tags: Optional[Dict[str, str]] = None):
        """Add a custom performance metric"""
        if self.running:
            from app.core.utils.performance_monitor import performance_monitor
            performance_monitor.add_custom_metric(name, value, unit, tags)
    
    async def execute_with_recovery(self, func, *args, **kwargs):
        """Execute function with exception recovery"""
        if self.running:
            from app.core.utils.exception_recovery import exception_recovery_manager
            return await exception_recovery_manager.execute_with_recovery(func, *args, **kwargs)
        else:
            return await func(*args, **kwargs)


# Global advanced features service instance
advanced_features_service = AdvancedFeaturesService()