"""
Core utilities for the video downloader.
"""

from .file_manager import FileManager, DuplicateAction, file_manager
from .naming_template import NamingTemplate, naming_template
from .cookie_manager import CookieManager, cookie_manager
from .user_agent import UserAgentManager, user_agent_manager

__all__ = [
    'FileManager', 'DuplicateAction', 'file_manager',
    'NamingTemplate', 'naming_template',
    'CookieManager', 'cookie_manager',
    'UserAgentManager', 'user_agent_manager'
]