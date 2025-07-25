"""
Plugin management module for dynamic loading and management of extractor plugins.
"""

from .manager import PluginManager, PluginManagerStats
from .loader import PluginLoader, PluginLoadResult
from .registry import PluginRegistry, RegisteredPlugin, PluginStatus
from .router import URLRouter, RoutingResult, URLInfo, URLType
from .security import PluginSecurityManager, SecurityPolicy, SecurityLevel, SecurityViolation

__all__ = [
    'PluginManager',
    'PluginManagerStats',
    'PluginLoader',
    'PluginLoadResult',
    'PluginRegistry',
    'RegisteredPlugin',
    'PluginStatus',
    'URLRouter',
    'RoutingResult',
    'URLInfo',
    'URLType',
    'PluginSecurityManager',
    'SecurityPolicy',
    'SecurityLevel',
    'SecurityViolation',
]