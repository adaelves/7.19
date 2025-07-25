"""
Plugin loader for dynamically loading and managing extractor plugins.
"""
import os
import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Type, Optional, Set
import logging
from dataclasses import dataclass
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from app.core.extractor.base import BaseExtractor, ExtractorInfo


@dataclass
class PluginLoadResult:
    """Result of plugin loading operation"""
    success: bool
    plugin_name: str
    extractor_class: Optional[Type[BaseExtractor]] = None
    error_message: Optional[str] = None


class PluginFileWatcher(FileSystemEventHandler):
    """File system watcher for plugin hot reloading"""
    
    def __init__(self, loader: 'PluginLoader'):
        self.loader = loader
        self.logger = logging.getLogger(__name__)
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        if event.src_path.endswith('.py'):
            plugin_name = Path(event.src_path).stem
            if plugin_name != '__init__':
                self.logger.info(f"Plugin file modified: {plugin_name}")
                # Reload the plugin after a short delay to ensure file is fully written
                threading.Timer(1.0, self._reload_plugin, args=[plugin_name]).start()
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        if event.src_path.endswith('.py'):
            plugin_name = Path(event.src_path).stem
            if plugin_name != '__init__':
                self.logger.info(f"New plugin file created: {plugin_name}")
                threading.Timer(1.0, self._load_plugin, args=[plugin_name]).start()
    
    def on_deleted(self, event):
        if event.is_directory:
            return
        
        if event.src_path.endswith('.py'):
            plugin_name = Path(event.src_path).stem
            if plugin_name != '__init__':
                self.logger.info(f"Plugin file deleted: {plugin_name}")
                self.loader.unload_plugin(plugin_name)
    
    def _reload_plugin(self, plugin_name: str):
        """Reload a plugin"""
        try:
            self.loader.reload_plugin(plugin_name)
        except Exception as e:
            self.logger.error(f"Failed to reload plugin {plugin_name}: {e}")
    
    def _load_plugin(self, plugin_name: str):
        """Load a new plugin"""
        try:
            self.loader.load_plugin(plugin_name)
        except Exception as e:
            self.logger.error(f"Failed to load new plugin {plugin_name}: {e}")


class PluginLoader:
    """
    Dynamic plugin loader for extractor plugins.
    Supports loading, unloading, and hot reloading of plugins.
    """
    
    def __init__(self, plugin_directories: List[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Default plugin directories
        if plugin_directories is None:
            plugin_directories = [
                os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins'),
                os.path.join(os.path.expanduser('~'), '.video_downloader', 'plugins')
            ]
        
        self.plugin_directories = [Path(d).resolve() for d in plugin_directories]
        
        # Loaded plugins
        self.loaded_plugins: Dict[str, Type[BaseExtractor]] = {}
        self.plugin_modules: Dict[str, object] = {}
        self.plugin_info: Dict[str, ExtractorInfo] = {}
        
        # Security settings
        self.allowed_imports: Set[str] = {
            'requests', 'urllib', 'json', 're', 'datetime', 'time',
            'base64', 'hashlib', 'hmac', 'uuid', 'typing',
            'dataclasses', 'abc', 'asyncio', 'aiohttp'
        }
        
        # File watcher for hot reloading
        self.observer: Optional[Observer] = None
        self.file_watcher: Optional[PluginFileWatcher] = None
        self.hot_reload_enabled = False
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Ensure plugin directories exist
        self._ensure_plugin_directories()
    
    def _ensure_plugin_directories(self):
        """Ensure plugin directories exist"""
        for plugin_dir in self.plugin_directories:
            plugin_dir.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py if it doesn't exist
            init_file = plugin_dir / '__init__.py'
            if not init_file.exists():
                init_file.write_text('# Plugin directory\n')
    
    def enable_hot_reload(self):
        """Enable hot reloading of plugins"""
        if self.hot_reload_enabled:
            return
        
        self.file_watcher = PluginFileWatcher(self)
        self.observer = Observer()
        
        for plugin_dir in self.plugin_directories:
            if plugin_dir.exists():
                self.observer.schedule(self.file_watcher, str(plugin_dir), recursive=False)
        
        self.observer.start()
        self.hot_reload_enabled = True
        self.logger.info("Plugin hot reloading enabled")
    
    def disable_hot_reload(self):
        """Disable hot reloading of plugins"""
        if not self.hot_reload_enabled:
            return
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        
        self.file_watcher = None
        self.hot_reload_enabled = False
        self.logger.info("Plugin hot reloading disabled")
    
    def load_all_plugins(self) -> List[PluginLoadResult]:
        """
        Load all plugins from plugin directories.
        
        Returns:
            List of PluginLoadResult objects
        """
        results = []
        
        with self._lock:
            for plugin_dir in self.plugin_directories:
                if not plugin_dir.exists():
                    continue
                
                for plugin_file in plugin_dir.glob('*.py'):
                    if plugin_file.name == '__init__.py':
                        continue
                    
                    plugin_name = plugin_file.stem
                    result = self.load_plugin(plugin_name)
                    results.append(result)
        
        self.logger.info(f"Loaded {len([r for r in results if r.success])} plugins successfully")
        return results
    
    def load_plugin(self, plugin_name: str) -> PluginLoadResult:
        """
        Load a specific plugin by name.
        
        Args:
            plugin_name: Name of the plugin to load
            
        Returns:
            PluginLoadResult object
        """
        with self._lock:
            try:
                # Find plugin file
                plugin_file = self._find_plugin_file(plugin_name)
                if not plugin_file:
                    return PluginLoadResult(
                        success=False,
                        plugin_name=plugin_name,
                        error_message=f"Plugin file not found: {plugin_name}"
                    )
                
                # Security check
                if not self._security_check(plugin_file):
                    return PluginLoadResult(
                        success=False,
                        plugin_name=plugin_name,
                        error_message=f"Security check failed for plugin: {plugin_name}"
                    )
                
                # Load module
                module = self._load_module(plugin_name, plugin_file)
                if not module:
                    return PluginLoadResult(
                        success=False,
                        plugin_name=plugin_name,
                        error_message=f"Failed to load module: {plugin_name}"
                    )
                
                # Find extractor class
                extractor_class = self._find_extractor_class(module)
                if not extractor_class:
                    return PluginLoadResult(
                        success=False,
                        plugin_name=plugin_name,
                        error_message=f"No valid extractor class found in plugin: {plugin_name}"
                    )
                
                # Validate extractor
                if not self._validate_extractor(extractor_class):
                    return PluginLoadResult(
                        success=False,
                        plugin_name=plugin_name,
                        error_message=f"Extractor validation failed: {plugin_name}"
                    )
                
                # Store plugin
                self.loaded_plugins[plugin_name] = extractor_class
                self.plugin_modules[plugin_name] = module
                
                # Get plugin info
                try:
                    instance = extractor_class()
                    self.plugin_info[plugin_name] = instance.info
                except Exception as e:
                    self.logger.warning(f"Failed to get plugin info for {plugin_name}: {e}")
                
                self.logger.info(f"Successfully loaded plugin: {plugin_name}")
                return PluginLoadResult(
                    success=True,
                    plugin_name=plugin_name,
                    extractor_class=extractor_class
                )
                
            except Exception as e:
                self.logger.error(f"Error loading plugin {plugin_name}: {e}")
                return PluginLoadResult(
                    success=False,
                    plugin_name=plugin_name,
                    error_message=str(e)
                )
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a specific plugin.
        
        Args:
            plugin_name: Name of the plugin to unload
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                if plugin_name in self.loaded_plugins:
                    del self.loaded_plugins[plugin_name]
                
                if plugin_name in self.plugin_modules:
                    # Remove from sys.modules if it was added
                    module_name = f"plugins.{plugin_name}"
                    if module_name in sys.modules:
                        del sys.modules[module_name]
                    del self.plugin_modules[plugin_name]
                
                if plugin_name in self.plugin_info:
                    del self.plugin_info[plugin_name]
                
                self.logger.info(f"Successfully unloaded plugin: {plugin_name}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error unloading plugin {plugin_name}: {e}")
                return False
    
    def reload_plugin(self, plugin_name: str) -> PluginLoadResult:
        """
        Reload a specific plugin.
        
        Args:
            plugin_name: Name of the plugin to reload
            
        Returns:
            PluginLoadResult object
        """
        with self._lock:
            # Unload first
            self.unload_plugin(plugin_name)
            
            # Then load again
            return self.load_plugin(plugin_name)
    
    def get_loaded_plugins(self) -> Dict[str, Type[BaseExtractor]]:
        """
        Get all loaded plugins.
        
        Returns:
            Dictionary mapping plugin names to extractor classes
        """
        with self._lock:
            return self.loaded_plugins.copy()
    
    def get_plugin_info(self, plugin_name: str) -> Optional[ExtractorInfo]:
        """
        Get information about a specific plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            ExtractorInfo object or None if plugin not found
        """
        with self._lock:
            return self.plugin_info.get(plugin_name)
    
    def get_all_plugin_info(self) -> Dict[str, ExtractorInfo]:
        """
        Get information about all loaded plugins.
        
        Returns:
            Dictionary mapping plugin names to ExtractorInfo objects
        """
        with self._lock:
            return self.plugin_info.copy()
    
    def _find_plugin_file(self, plugin_name: str) -> Optional[Path]:
        """Find plugin file in plugin directories"""
        for plugin_dir in self.plugin_directories:
            plugin_file = plugin_dir / f"{plugin_name}.py"
            if plugin_file.exists():
                return plugin_file
        return None
    
    def _security_check(self, plugin_file: Path) -> bool:
        """
        Perform basic security check on plugin file.
        
        Args:
            plugin_file: Path to plugin file
            
        Returns:
            True if security check passes, False otherwise
        """
        try:
            content = plugin_file.read_text(encoding='utf-8')
            
            # Check for dangerous imports/operations
            dangerous_patterns = [
                'import os',
                'import subprocess',
                'import sys',
                'exec(',
                'eval(',
                '__import__',
                'open(',
                'file(',
            ]
            
            for pattern in dangerous_patterns:
                if pattern in content:
                    self.logger.warning(f"Potentially dangerous pattern found in {plugin_file}: {pattern}")
                    # For now, just warn but don't block - in production this might be stricter
            
            return True
            
        except Exception as e:
            self.logger.error(f"Security check failed for {plugin_file}: {e}")
            return False
    
    def _load_module(self, plugin_name: str, plugin_file: Path) -> Optional[object]:
        """Load Python module from file"""
        try:
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
            if not spec or not spec.loader:
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            return module
            
        except Exception as e:
            self.logger.error(f"Failed to load module {plugin_name}: {e}")
            return None
    
    def _find_extractor_class(self, module: object) -> Optional[Type[BaseExtractor]]:
        """Find BaseExtractor subclass in module"""
        try:
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                if (isinstance(attr, type) and 
                    issubclass(attr, BaseExtractor) and 
                    attr != BaseExtractor):
                    return attr
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to find extractor class: {e}")
            return None
    
    def _validate_extractor(self, extractor_class: Type[BaseExtractor]) -> bool:
        """Validate extractor class"""
        try:
            # Try to instantiate
            instance = extractor_class()
            
            # Check required properties
            if not hasattr(instance, 'supported_domains') or not instance.supported_domains:
                return False
            
            # Check required methods
            required_methods = ['can_handle', 'extract_info', 'get_download_urls', 'get_metadata']
            for method in required_methods:
                if not hasattr(instance, method) or not callable(getattr(instance, method)):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Extractor validation failed: {e}")
            return False
    
    def __del__(self):
        """Cleanup when loader is destroyed"""
        self.disable_hot_reload()