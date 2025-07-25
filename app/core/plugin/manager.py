"""
Main plugin manager that coordinates all plugin system components.
"""
import logging
import threading
from typing import Dict, List, Optional, Type, Any
from pathlib import Path
import asyncio
from dataclasses import dataclass

from app.core.extractor.base import BaseExtractor, ExtractorInfo
from app.core.plugin.loader import PluginLoader, PluginLoadResult
from app.core.plugin.registry import PluginRegistry, RegisteredPlugin, PluginStatus
from app.core.plugin.router import URLRouter, RoutingResult, URLInfo
from app.core.plugin.security import PluginSecurityManager, SecurityPolicy, SecurityViolation


@dataclass
class PluginManagerStats:
    """Plugin manager statistics"""
    total_plugins: int = 0
    active_plugins: int = 0
    failed_plugins: int = 0
    total_domains: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    security_violations: int = 0


class PluginManager:
    """
    Main plugin manager that coordinates loading, registration, routing, and security.
    """
    
    def __init__(self, plugin_directories: Optional[List[str]] = None,
                 security_policy: Optional[SecurityPolicy] = None,
                 enable_hot_reload: bool = True):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.loader = PluginLoader(plugin_directories)
        self.registry = PluginRegistry()
        self.router = URLRouter(self.registry)
        self.security_manager = PluginSecurityManager(security_policy)
        
        # Configuration
        self.enable_hot_reload = enable_hot_reload
        
        # State
        self._initialized = False
        self._lock = threading.RLock()
        
        # Event callbacks
        self._plugin_loaded_callbacks: List[callable] = []
        self._plugin_unloaded_callbacks: List[callable] = []
        self._security_violation_callbacks: List[callable] = []
    
    async def initialize(self) -> bool:
        """
        Initialize the plugin manager and load all plugins.
        
        Returns:
            True if initialization successful, False otherwise
        """
        with self._lock:
            if self._initialized:
                return True
            
            try:
                self.logger.info("Initializing plugin manager...")
                
                # Enable hot reload if requested
                if self.enable_hot_reload:
                    self.loader.enable_hot_reload()
                
                # Load all plugins
                load_results = self.loader.load_all_plugins()
                
                # Register loaded plugins
                success_count = 0
                for result in load_results:
                    if result.success and result.extractor_class:
                        if await self._register_plugin_safely(result):
                            success_count += 1
                
                self._initialized = True
                self.logger.info(f"Plugin manager initialized with {success_count} plugins")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to initialize plugin manager: {e}")
                return False
    
    async def shutdown(self):
        """Shutdown the plugin manager"""
        with self._lock:
            if not self._initialized:
                return
            
            try:
                self.logger.info("Shutting down plugin manager...")
                
                # Disable hot reload
                self.loader.disable_hot_reload()
                
                # Clear all caches
                self.registry.clear_cache()
                self.router.clear_cache()
                
                self._initialized = False
                self.logger.info("Plugin manager shut down")
                
            except Exception as e:
                self.logger.error(f"Error during plugin manager shutdown: {e}")
    
    async def load_plugin(self, plugin_name: str) -> bool:
        """
        Load a specific plugin.
        
        Args:
            plugin_name: Name of the plugin to load
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                # Load plugin
                result = self.loader.load_plugin(plugin_name)
                
                if result.success and result.extractor_class:
                    # Register plugin
                    success = await self._register_plugin_safely(result)
                    if success:
                        # Notify callbacks
                        await self._notify_plugin_loaded(plugin_name)
                    return success
                else:
                    self.logger.error(f"Failed to load plugin {plugin_name}: {result.error_message}")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Error loading plugin {plugin_name}: {e}")
                return False
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a specific plugin.
        
        Args:
            plugin_name: Name of the plugin to unload
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                # Unregister from registry
                self.registry.unregister_plugin(plugin_name)
                
                # Unload from loader
                self.loader.unload_plugin(plugin_name)
                
                # Clear security violations
                self.security_manager.clear_violations(plugin_name)
                
                # Notify callbacks
                await self._notify_plugin_unloaded(plugin_name)
                
                self.logger.info(f"Successfully unloaded plugin: {plugin_name}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error unloading plugin {plugin_name}: {e}")
                return False
    
    async def reload_plugin(self, plugin_name: str) -> bool:
        """
        Reload a specific plugin.
        
        Args:
            plugin_name: Name of the plugin to reload
            
        Returns:
            True if successful, False otherwise
        """
        # Unload first
        await self.unload_plugin(plugin_name)
        
        # Then load again
        return await self.load_plugin(plugin_name)
    
    async def route_url(self, url: str) -> RoutingResult:
        """
        Route a URL to the appropriate plugin.
        
        Args:
            url: URL to route
            
        Returns:
            RoutingResult object
        """
        return self.router.route_url(url)
    
    async def extract_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract information from a URL using the appropriate plugin.
        
        Args:
            url: URL to extract information from
            
        Returns:
            Extracted information dictionary or None if failed
        """
        try:
            # Route URL to plugin
            routing_result = await self.route_url(url)
            
            if not routing_result.success or not routing_result.plugin:
                self.logger.warning(f"No suitable plugin found for URL: {url}")
                return None
            
            # Create extractor instance
            plugin = routing_result.plugin
            extractor = plugin.extractor_class()
            
            # Execute extraction with security monitoring
            def extract_func():
                return asyncio.run(extractor.extract_info(url))
            
            info = self.security_manager.monitor_plugin_execution(
                plugin.name, extract_func
            )
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error extracting info from {url}: {e}")
            return None
    
    async def get_metadata(self, url: str):
        """
        Get metadata from a URL using the appropriate plugin.
        
        Args:
            url: URL to get metadata from
            
        Returns:
            VideoMetadata object or None if failed
        """
        try:
            # Route URL to plugin
            routing_result = await self.route_url(url)
            
            if not routing_result.success or not routing_result.plugin:
                return None
            
            # Create extractor instance
            plugin = routing_result.plugin
            extractor = plugin.extractor_class()
            
            # Execute metadata extraction with security monitoring
            def metadata_func():
                return asyncio.run(extractor.get_metadata(url))
            
            metadata = self.security_manager.monitor_plugin_execution(
                plugin.name, metadata_func
            )
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error getting metadata from {url}: {e}")
            return None
    
    def get_plugin_info(self, plugin_name: str) -> Optional[RegisteredPlugin]:
        """
        Get information about a specific plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            RegisteredPlugin object or None if not found
        """
        return self.registry.get_plugin(plugin_name)
    
    def get_all_plugins(self) -> Dict[str, RegisteredPlugin]:
        """
        Get information about all plugins.
        
        Returns:
            Dictionary mapping plugin names to RegisteredPlugin objects
        """
        return self.registry.get_all_plugins()
    
    def get_active_plugins(self) -> Dict[str, RegisteredPlugin]:
        """
        Get all active plugins.
        
        Returns:
            Dictionary mapping plugin names to active RegisteredPlugin objects
        """
        return self.registry.get_active_plugins()
    
    def get_supported_domains(self) -> List[str]:
        """
        Get all supported domains.
        
        Returns:
            List of supported domain names
        """
        return sorted(list(self.registry.get_supported_domains()))
    
    def get_supported_platforms(self) -> List[str]:
        """
        Get all supported platforms.
        
        Returns:
            List of platform names
        """
        return self.router.get_supported_platforms()
    
    def is_url_supported(self, url: str) -> bool:
        """
        Check if a URL is supported.
        
        Args:
            url: URL to check
            
        Returns:
            True if supported, False otherwise
        """
        return self.router.is_supported_url(url)
    
    def get_url_info(self, url: str) -> Optional[URLInfo]:
        """
        Get URL information without routing to plugin.
        
        Args:
            url: URL to analyze
            
        Returns:
            URLInfo object or None if analysis failed
        """
        return self.router.get_url_info(url)
    
    def get_security_violations(self, plugin_name: Optional[str] = None) -> Dict[str, List[SecurityViolation]]:
        """
        Get security violations.
        
        Args:
            plugin_name: Name of plugin to get violations for, or None for all
            
        Returns:
            Dictionary mapping plugin names to violation lists
        """
        if plugin_name:
            violations = self.security_manager.get_plugin_violations(plugin_name)
            return {plugin_name: violations} if violations else {}
        else:
            return self.security_manager.get_all_violations()
    
    def get_statistics(self) -> PluginManagerStats:
        """
        Get plugin manager statistics.
        
        Returns:
            PluginManagerStats object
        """
        registry_stats = self.registry.get_statistics()
        cache_stats = self.router.get_cache_stats()
        all_violations = self.security_manager.get_all_violations()
        
        total_violations = sum(len(violations) for violations in all_violations.values())
        
        return PluginManagerStats(
            total_plugins=registry_stats['total_plugins'],
            active_plugins=registry_stats['active_plugins'],
            failed_plugins=registry_stats['total_plugins'] - registry_stats['active_plugins'],
            total_domains=registry_stats['total_domains'],
            cache_hits=registry_stats['cache_hits'],
            cache_misses=registry_stats['cache_misses'],
            security_violations=total_violations
        )
    
    def clear_caches(self):
        """Clear all caches"""
        self.registry.clear_cache()
        self.router.clear_cache()
        self.logger.info("All plugin caches cleared")
    
    def add_plugin_loaded_callback(self, callback: callable):
        """Add callback for plugin loaded events"""
        self._plugin_loaded_callbacks.append(callback)
    
    def add_plugin_unloaded_callback(self, callback: callable):
        """Add callback for plugin unloaded events"""
        self._plugin_unloaded_callbacks.append(callback)
    
    def add_security_violation_callback(self, callback: callable):
        """Add callback for security violation events"""
        self._security_violation_callbacks.append(callback)
    
    async def _register_plugin_safely(self, load_result: PluginLoadResult) -> bool:
        """Register a plugin with security checks"""
        try:
            plugin_name = load_result.plugin_name
            extractor_class = load_result.extractor_class
            
            # Security validation
            plugin_file = self.loader._find_plugin_file(plugin_name)
            if plugin_file:
                violations = self.security_manager.validate_plugin_file(plugin_file)
                
                # Check for critical violations
                critical_violations = [v for v in violations if v.severity == "critical"]
                if critical_violations:
                    self.logger.error(f"Plugin {plugin_name} has critical security violations")
                    await self._notify_security_violations(plugin_name, violations)
                    return False
            
            # Get plugin info
            instance = extractor_class()
            info = instance.get_extractor_info()
            
            # Register in registry
            success = self.registry.register_plugin(plugin_name, extractor_class, info)
            
            if success:
                self.logger.info(f"Successfully registered plugin: {plugin_name}")
            else:
                self.registry.set_plugin_status(plugin_name, PluginStatus.ERROR, 
                                              "Registration failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error registering plugin {load_result.plugin_name}: {e}")
            return False
    
    async def _notify_plugin_loaded(self, plugin_name: str):
        """Notify callbacks about plugin loaded event"""
        for callback in self._plugin_loaded_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(plugin_name)
                else:
                    callback(plugin_name)
            except Exception as e:
                self.logger.error(f"Error in plugin loaded callback: {e}")
    
    async def _notify_plugin_unloaded(self, plugin_name: str):
        """Notify callbacks about plugin unloaded event"""
        for callback in self._plugin_unloaded_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(plugin_name)
                else:
                    callback(plugin_name)
            except Exception as e:
                self.logger.error(f"Error in plugin unloaded callback: {e}")
    
    async def _notify_security_violations(self, plugin_name: str, violations: List[SecurityViolation]):
        """Notify callbacks about security violations"""
        for callback in self._security_violation_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(plugin_name, violations)
                else:
                    callback(plugin_name, violations)
            except Exception as e:
                self.logger.error(f"Error in security violation callback: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        asyncio.run(self.shutdown())