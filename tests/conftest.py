"""
Global test configuration and fixtures for pytest.
"""
import pytest
import asyncio
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Import test utilities
from tests.utils.test_helpers import TestDataFactory, MockDownloadManager
from tests.utils.fixtures import *


def pytest_configure(config):
    """Configure pytest with custom markers and settings"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "ui: mark test as a UI test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Add unit marker to tests in test_* files
        if "test_" in item.nodeid and not any(
            marker in item.keywords for marker in ["integration", "ui", "performance"]
        ):
            item.add_marker(pytest.mark.unit)
        
        # Add slow marker to performance tests
        if "performance" in item.keywords:
            item.add_marker(pytest.mark.slow)


# Remove custom event_loop fixture to avoid conflicts with pytest-asyncio


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_network():
    """Mock network requests for testing"""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post, \
         patch('aiohttp.ClientSession') as mock_session:
        
        # Configure default responses
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {}
        mock_get.return_value.text = ""
        
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {}
        
        yield {
            'get': mock_get,
            'post': mock_post,
            'session': mock_session
        }


@pytest.fixture
def test_data_factory():
    """Provide test data factory"""
    return TestDataFactory()


@pytest.fixture
def mock_download_manager():
    """Provide mock download manager"""
    return MockDownloadManager()


# Performance testing fixtures
@pytest.fixture
def performance_monitor():
    """Monitor performance metrics during tests"""
    import psutil
    import time
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.start_memory = None
            self.process = psutil.Process()
        
        def start(self):
            self.start_time = time.perf_counter()
            self.start_memory = self.process.memory_info().rss
        
        def stop(self):
            end_time = time.perf_counter()
            end_memory = self.process.memory_info().rss
            
            return {
                'duration': end_time - self.start_time if self.start_time else 0.0,
                'memory_delta': end_memory - self.start_memory if self.start_memory else 0,
                'peak_memory': self.process.memory_info().peak_wss if hasattr(self.process.memory_info(), 'peak_wss') else end_memory
            }
    
    return PerformanceMonitor()


# UI testing fixtures
@pytest.fixture
def qapp():
    """Create QApplication for UI tests"""
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    yield app
    
    # Clean up
    app.processEvents()


@pytest.fixture
def main_window(qapp):
    """Create main window for UI tests"""
    from app.ui.main_window import MainWindow
    
    window = MainWindow()
    window.show()
    qapp.processEvents()
    
    yield window
    
    window.close()
    qapp.processEvents()