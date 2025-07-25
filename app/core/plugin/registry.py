"""
Plugin registry for managing and organizing loaded plugins.
"""
import logging
from typing import Dict, List, Optional, Set, Type
from urllib.parse import urlparse
import threading
from dataclasses import dataclass, field
from enum import Enum

from app.core.extractor.base import BaseExtractor, ExtractorInfo


class PluginStatus(Enum):
    """Plugin status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    LOADING = "loading"


@dataclass
class RegisteredPlugin:
    """Information about a registered plugin"""
    name: str
    extractor_class: Type[BaseExtractor]
    info: ExtractorInfo
    status: PluginStatus = PluginStatus.ACTIVE
    supported_domains: List[str] = field(default_factory=list)
    priority: int = 0  # Higher priority plugins are preferred
    error_message: Optional[str] = None
    load_time: Optional[float] = None
    usage_count: int = 0


class PluginRegistry:
    """
    Registry for managing loaded plugins and their metadata.
    Provides efficient lookup and management of extractor plugins.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Plugin storage
        self._plugins: Dict[str, RegisteredPlugin] = {}
        self._domain_map: Dict[str, List[str]] = {}  # domain -> plugin names
        self._url_cache: Dict[str, str] = {}  # URL -> plugin name cache
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Statistics
        self._stats = {
            'total_plugins': 0,
            'active_plugins': 0,
            'total_domains': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def register_plugin(self, name: str, extractor_class: Type[BaseExtractor], 
                       info: ExtractorInfo, priority: int = 0) -> bool:
        """
        Register a plugin in the registry.
        
        Args:
            name: Plugin name
            extractor_class: Extractor class
            info: Plugin information
            priority: Plugin priority (higher = preferred)
            
        Returns:
            True if registration successful, False otherwise
        """
        with self._lock:
            try:
                # Create instance to get supported domains
                instance = extractor_class()
                supported_domains = instance.supported_domains
                
                # Create registered plugin
                plugin = RegisteredPlugin(
                    name=name,
                    extractor_class=extractor_class,
                    info=info,
                    supported_domains=supported_domains,
                    priority=priority
                )
                
                # Store plugin
                self._plugins[name] = plugin
                
                # Update domain mapping
                self._update_domain_mapping(name, supported_domains)
                
                # Clear URL cache as new plugin might handle cached URLs
                self._url_cache.clear()
                
                # Update statistics
                self._update_stats()
                
                self.logger.info(f"Registered plugin: {name} (domains: {supported_domains})")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to register plugin {name}: {e}")
                return False
    
    def unregister_plugin(self, name: str) -> bool:
        """
        Unregister a plugin from the registry.
        
        Args:
            name: Plugin name
            
        Returns:
            True if unregistration successful, False otherwise
        """
        with self._lock:
            try:
                if name not in self._plugins:
                    return False
                
                plugin = self._plugins[name]
                
                # Remove from domain mapping
                self._remove_domain_mapping(name, plugin.supported_domains)
                
                # Remove plugin
                del self._plugins[name]
                
                # Clear URL cache
                self._url_cache.clear()
                
                # Update statistics
                self._update_stats()
                
                self.logger.info(f"Unregistered plugin: {name}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to unregister plugin {name}: {e}")
                return False
    
    def get_plugin(self, name: str) -> Optional[RegisteredPlugin]:
        """
        Get a registered plugin by name.
        
        Args:
            name: Plugin name
            
        Returns:
            RegisteredPlugin object or None if not found
        """
        with self._lock:
            return self._plugins.get(name)
    
    def get_all_plugins(self) -> Dict[str, RegisteredPlugin]:
        """
        Get all registered plugins.
        
        Returns:
            Dictionary mapping plugin names to RegisteredPlugin objects
        """
        with self._lock:
            return self._plugins.copy()
    
    def get_active_plugins(self) -> Dict[str, RegisteredPlugin]:
        """
        Get all active plugins.
        
        Returns:
            Dictionary mapping plugin names to active RegisteredPlugin objects
        """
        with self._lock:
            return {
                name: plugin for name, plugin in self._plugins.items()
                if plugin.status == PluginStatus.ACTIVE
            }
    
    def get_plugins_for_domain(self, domain: str) -> List[RegisteredPlugin]:
        """
        Get plugins that can handle a specific domain.
        
        Args:
            domain: Domain name
            
        Returns:
            List of RegisteredPlugin objects sorted by priority (highest first)
        """
        with self._lock:
            domain = domain.lower()
            plugin_names = self._domain_map.get(domain, [])
            
            plugins = []
            for name in plugin_names:
                if name in self._plugins and self._plugins[name].status == PluginStatus.ACTIVE:
                    plugins.append(self._plugins[name])
            
            # Sort by priority (highest first) and then by usage count
            plugins.sort(key=lambda p: (-p.priority, -p.usage_count))
            return plugins
    
    def get_plugin_for_url(self, url: str) -> Optional[RegisteredPlugin]:
        """
        Get the best plugin for handling a specific URL.
        
        Args:
            url: URL to handle
            
        Returns:
            RegisteredPlugin object or None if no suitable plugin found
        """
        with self._lock:
            # Check cache first
            if url in self._url_cache:
                plugin_name = self._url_cache[url]
                if plugin_name in self._plugins:
                    self._stats['cache_hits'] += 1
                    plugin = self._plugins[plugin_name]
                    plugin.usage_count += 1
                    return plugin
                else:
                    # Cached plugin no longer exists, remove from cache
                    del self._url_cache[url]
            
            self._stats['cache_misses'] += 1
            
            # Extract domain from URL
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
            except Exception:
                return None
            
            # Find plugins for this domain
            candidate_plugins = self._get_candidate_plugins(domain)
            
            # Test each plugin to see if it can handle the URL
            for plugin in candidate_plugins:
                try:
                    instance = plugin.extractor_class()
                    if instance.can_handle(url):
                        # Cache the result
                        self._url_cache[url] = plugin.name
                        plugin.usage_count += 1
                        return plugin
                except Exception as e:
                    self.logger.warning(f"Plugin {plugin.name} failed URL test: {e}")
                    continue
            
            return None
    
    def set_plugin_status(self, name: str, status: PluginStatus, 
                         error_message: Optional[str] = None) -> bool:
        """
        Set plugin status.
        
        Args:
            name: Plugin name
            status: New status
            error_message: Error message if status is ERROR
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            if name not in self._plugins:
                return False
            
            plugin = self._plugins[name]
            plugin.status = status
            plugin.error_message = error_message
            
            # Update statistics
            self._update_stats()
            
            return True
    
    def set_plugin_priority(self, name: str, priority: int) -> bool:
        """
        Set plugin priority.
        
        Args:
            name: Plugin name
            priority: New priority
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            if name not in self._plugins:
                return False
            
            self._plugins[name].priority = priority
            return True
    
    def get_supported_domains(self) -> Set[str]:
        """
        Get all supported domains.
        
        Returns:
            Set of supported domain names
        """
        with self._lock:
            return set(self._domain_map.keys())
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get registry statistics.
        
        Returns:
            Dictionary containing statistics
        """
        with self._lock:
            return self._stats.copy()
    
    def clear_cache(self):
        """Clear the URL cache"""
        with self._lock:
            self._url_cache.clear()
            self.logger.info("Plugin registry cache cleared")
    
    def get_plugin_usage_stats(self) -> Dict[str, int]:
        """
        Get plugin usage statistics.
        
        Returns:
            Dictionary mapping plugin names to usage counts
        """
        with self._lock:
            return {name: plugin.usage_count for name, plugin in self._plugins.items()}
    
    def reset_usage_stats(self):
        """Reset all plugin usage statistics"""
        with self._lock:
            for plugin in self._plugins.values():
                plugin.usage_count = 0
            self.logger.info("Plugin usage statistics reset")
    
    def _update_domain_mapping(self, plugin_name: str, domains: List[str]):
        """Update domain to plugin mapping"""
        for domain in domains:
            domain = domain.lower()
            if domain not in self._domain_map:
                self._domain_map[domain] = []
            
            if plugin_name not in self._domain_map[domain]:
                self._domain_map[domain].append(plugin_name)
    
    def _remove_domain_mapping(self, plugin_name: str, domains: List[str]):
        """Remove plugin from domain mapping"""
        for domain in domains:
            domain = domain.lower()
            if domain in self._domain_map:
                if plugin_name in self._domain_map[domain]:
                    self._domain_map[domain].remove(plugin_name)
                
                # Remove domain entry if no plugins left
                if not self._domain_map[domain]:
                    del self._domain_map[domain]
    
    def _get_candidate_plugins(self, domain: str) -> List[RegisteredPlugin]:
        """Get candidate plugins for a domain, including partial matches"""
        candidates = []
        
        # Exact domain match
        if domain in self._domain_map:
            for plugin_name in self._domain_map[domain]:
                if (plugin_name in self._plugins and 
                    self._plugins[plugin_name].status == PluginStatus.ACTIVE):
                    candidates.append(self._plugins[plugin_name])
        
        # Partial domain matches (e.g., youtube.com matches youtu.be)
        for mapped_domain, plugin_names in self._domain_map.items():
            if mapped_domain in domain or domain in mapped_domain:
                for plugin_name in plugin_names:
                    if (plugin_name in self._plugins and 
                        self._plugins[plugin_name].status == PluginStatus.ACTIVE and
                        self._plugins[plugin_name] not in candidates):
                        candidates.append(self._plugins[plugin_name])
        
        # Sort by priority and usage
        candidates.sort(key=lambda p: (-p.priority, -p.usage_count))
        return candidates
    
    def _update_stats(self):
        """Update registry statistics"""
        self._stats['total_plugins'] = len(self._plugins)
        self._stats['active_plugins'] = len([
            p for p in self._plugins.values() 
            if p.status == PluginStatus.ACTIVE
        ])
        self._stats['total_domains'] = len(self._domain_map)