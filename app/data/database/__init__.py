"""
Database module for the video downloader application.
"""

from .connection import DatabaseConnection, DatabaseManager
from .repositories import (
    DownloadHistoryRepository,
    CreatorRepository, 
    SettingsRepository
)
from .service import DatabaseService, get_database_service, close_database_service

__all__ = [
    'DatabaseConnection',
    'DatabaseManager',
    'DownloadHistoryRepository',
    'CreatorRepository',
    'SettingsRepository',
    'DatabaseService',
    'get_database_service',
    'close_database_service'
]