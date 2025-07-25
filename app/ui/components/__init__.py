"""
UI组件模块
"""

from .url_input import URLInputWidget
from .download_list import DownloadListWidget
from .download_task_card import DownloadTaskCard, MagicProgressBar, StatusIndicator
from .status_bar import CustomStatusBar

__all__ = [
    'URLInputWidget',
    'DownloadListWidget', 
    'DownloadTaskCard',
    'MagicProgressBar',
    'StatusIndicator',
    'CustomStatusBar'
]