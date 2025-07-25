"""
Tests for the plugin management system.
"""
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from app.core.plugin import (
    PluginManager, PluginLoader, PluginRegistry, URLRouter,
    PluginSecurityManager, SecurityPolicy, SecurityLevel
)
from app.core.plugin.loader import PluginLoadResult
from app.core.plugin.registry import PluginStatus
from app.core.plugin.router import URLType
from app.core.extractor.base import BaseExtractor, ExtractorInfo


class TestPluginLoader:
    """Test plugin loader functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.plugin_dir = self.temp_dir / 'plugins'
        self.plugin_dir.mkdir()
        
        # Create a simple test plugin
        self.test_plugin_content = '''
from app.core.extractor.base import BaseExtractor, ExtractorInfo
from typing import List, Dict, Any

class TestExtractor(BaseExtractor):
    @property
    def supported_domains(self) -> List[str]:
        return ['test.com']
    
    def can_handle(self, url: str) -> bool:
        return 'test.com' in url
    
    async def extract_info(self, url: str) -> Dict[str, Any]:
        return {'title': 'Test Video', 'id': '123'}
    
    async def get_download_urls(self, info: Dict[str, Any]) -> List[str]:
        return ['http://test.com/video.mp4']
    
    async def get_metadata(self, url: str):
        from app.data.models.core import VideoMetadata
        from datetime import datetime
        return VideoMetadata(
            title='Test Video',
            author='Test Author',
            thumbnail_url='',
            duration=120,
            view_count=1000,
            upload_date=datetime.now(),
            quality_options=[]
        )
    
    def get_extractor_info(self) -> ExtractorInfo:
        return ExtractorInfo(
            name='Test Extractor',
            version='1.0.0',
            supported_domains=self.supported_domains,
            description='Test extractor'
        )
'''
        
        # Write test plugin
        (self.plugin_dir / 'test_plugin.py').write_text(self.test_plugin_content)
        
        self.loader = PluginLoader([str(self.plugin_dir)])
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_load_plugin_success(self):
        """Test successful plugin loading"""
        result = self.loader.load_plugin('test_plugin')
        
        assert result.success
        assert result.plugin_name == 'test_plugin'
        assert result.extractor_class is not None
        assert 'test_plugin' in self.loader.loaded_plugins
    
    def test_load_plugin_not_found(self):
        """Test loading non-existent plugin"""
        result = self.loader.load_plugin('nonexistent')
        
        assert not result.success
        assert 'not found' in result.error_message.lower()
    
    def test_load_all_plugins(self):
        """Test loading all plugins"""
        results = self.loader.load_all_plugins()
        
        assert len(results) == 1
        assert results[0].success
        assert results[0].plugin_name == 'test_plugin'
    
    def test_unload_plugin(self):
        """Test plugin unloading"""
        # Load first
        self.loader.load_plugin('test_plugin')
        assert 'test_plugin' in self.loader.loaded_plugins
        
        # Unload
        success = self.loader.unload_plugin('test_plugin')
        assert success
        assert 'test_plugin' not in self.loader.loaded_plugins
    
    def test_reload_plugin(self):
        """Test plugin reloading"""
        # Load first
        result1 = self.loader.load_plugin('test_plugin')
        assert result1.success
        
        # Reload
        result2 = self.loader.reload_plugin('test_plugin')
        assert result2.success
        assert result2.plugin_name == 'test_plugin'


class TestPluginRegistry:
    """Test plugin registry functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.registry = PluginRegistry()
        
        # Create mock extractor class
        self.mock_extractor_class = Mock(spec=BaseExtractor)
        self.mock_extractor_instance = Mock()
        self.mock_extractor_instance.supported_domains = ['test.com']
        self.mock_extractor_instance.can_handle.return_value = True
        self.mock_extractor_class.return_value = self.mock_extractor_instance
        
        self.test_info = ExtractorInfo(
            name='Test Extractor',
            version='1.0.0',
            supported_domains=['test.com'],
            description='Test extractor'
        )
    
    def test_register_plugin(self):
        """Test plugin registration"""
        success = self.registry.register_plugin(
            'test_plugin', 
            self.mock_extractor_class, 
            self.test_info
        )
        
        assert success
        assert 'test_plugin' in self.registry._plugins
        
        plugin = self.registry.get_plugin('test_plugin')
        assert plugin is not None
        assert plugin.name == 'test_plugin'
        assert plugin.status == PluginStatus.ACTIVE
    
    def test_unregister_plugin(self):
        """Test plugin unregistration"""
        # Register first
        self.registry.register_plugin('test_plugin', self.mock_extractor_class, self.test_info)
        
        # Unregister
        success = self.registry.unregister_plugin('test_plugin')
        assert success
        assert 'test_plugin' not in self.registry._plugins
    
    def test_get_plugins_for_domain(self):
        """Test getting plugins for domain"""
        self.registry.register_plugin('test_plugin', self.mock_extractor_class, self.test_info)
        
        plugins = self.registry.get_plugins_for_domain('test.com')
        assert len(plugins) == 1
        assert plugins[0].name == 'test_plugin'
    
    def test_get_plugin_for_url(self):
        """Test getting plugin for URL"""
        self.registry.register_plugin('test_plugin', self.mock_extractor_class, self.test_info)
        
        plugin = self.registry.get_plugin_for_url('https://test.com/video')
        assert plugin is not None
        assert plugin.name == 'test_plugin'


class TestURLRouter:
    """Test URL router functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.registry = PluginRegistry()
        self.router = URLRouter(self.registry)
        
        # Create mock plugin
        mock_extractor_class = Mock(spec=BaseExtractor)
        mock_extractor_instance = Mock()
        mock_extractor_instance.supported_domains = ['youtube.com']
        mock_extractor_instance.can_handle.return_value = True
        mock_extractor_class.return_value = mock_extractor_instance
        
        test_info = ExtractorInfo(
            name='YouTube Extractor',
            version='1.0.0',
            supported_domains=['youtube.com'],
            description='YouTube extractor'
        )
        
        self.registry.register_plugin('youtube', mock_extractor_class, test_info)
    
    def test_route_youtube_video(self):
        """Test routing YouTube video URL"""
        url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        result = self.router.route_url(url)
        
        assert result.success
        assert result.plugin is not None
        assert result.plugin.name == 'youtube'
        assert result.url_info is not None
        assert result.url_info.url_type == URLType.VIDEO
        assert result.url_info.platform == 'youtube'
        assert result.url_info.video_id == 'dQw4w9WgXcQ'
    
    def test_route_youtube_playlist(self):
        """Test routing YouTube playlist URL"""
        url = 'https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMt9H1mu_0Qk0XLhqF'
        result = self.router.route_url(url)
        
        assert result.success
        assert result.url_info.url_type == URLType.PLAYLIST
        assert result.url_info.playlist_id == 'PLrAXtmRdnEQy6nuLMt9H1mu_0Qk0XLhqF'
    
    def test_route_unsupported_url(self):
        """Test routing unsupported URL"""
        url = 'https://unsupported.com/video'
        result = self.router.route_url(url)
        
        assert not result.success
        assert 'No suitable plugin found' in result.error_message
    
    def test_get_url_info(self):
        """Test getting URL information"""
        url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        url_info = self.router.get_url_info(url)
        
        assert url_info is not None
        assert url_info.url_type == URLType.VIDEO
        assert url_info.platform == 'youtube'
        assert url_info.video_id == 'dQw4w9WgXcQ'
    
    def test_is_supported_url(self):
        """Test checking if URL is supported"""
        supported_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        unsupported_url = 'https://unsupported.com/video'
        
        assert self.router.is_supported_url(supported_url)
        assert not self.router.is_supported_url(unsupported_url)


class TestPluginSecurityManager:
    """Test plugin security manager functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.security_manager = PluginSecurityManager()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_validate_safe_plugin(self):
        """Test validating a safe plugin"""
        safe_plugin_content = '''
import json
import re
from app.core.extractor.base import BaseExtractor

class SafeExtractor(BaseExtractor):
    def can_handle(self, url):
        return True
'''
        
        plugin_file = self.temp_dir / 'safe_plugin.py'
        plugin_file.write_text(safe_plugin_content)
        
        violations = self.security_manager.validate_plugin_file(plugin_file)
        
        # Should have no critical violations
        critical_violations = [v for v in violations if v.severity == "critical"]
        assert len(critical_violations) == 0
    
    def test_validate_dangerous_plugin(self):
        """Test validating a dangerous plugin"""
        dangerous_plugin_content = '''
import os
import subprocess
from app.core.extractor.base import BaseExtractor

class DangerousExtractor(BaseExtractor):
    def can_handle(self, url):
        os.system("rm -rf /")  # Very dangerous!
        return True
'''
        
        plugin_file = self.temp_dir / 'dangerous_plugin.py'
        plugin_file.write_text(dangerous_plugin_content)
        
        violations = self.security_manager.validate_plugin_file(plugin_file)
        
        # Should have violations for dangerous imports
        assert len(violations) > 0
        dangerous_imports = [v for v in violations if 'import' in v.description.lower()]
        assert len(dangerous_imports) > 0
    
    def test_is_plugin_safe(self):
        """Test checking if plugin is safe"""
        safe_plugin_content = '''
import json
from app.core.extractor.base import BaseExtractor

class SafeExtractor(BaseExtractor):
    pass
'''
        
        plugin_file = self.temp_dir / 'safe_plugin.py'
        plugin_file.write_text(safe_plugin_content)
        
        assert self.security_manager.is_plugin_safe(plugin_file)


class TestPluginManager:
    """Test plugin manager functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.plugin_dir = self.temp_dir / 'plugins'
        self.plugin_dir.mkdir()
        
        # Create test plugin
        test_plugin_content = '''
from app.core.extractor.base import BaseExtractor, ExtractorInfo
from typing import List, Dict, Any

class TestExtractor(BaseExtractor):
    @property
    def supported_domains(self) -> List[str]:
        return ['test.com']
    
    def can_handle(self, url: str) -> bool:
        return 'test.com' in url
    
    async def extract_info(self, url: str) -> Dict[str, Any]:
        return {'title': 'Test Video', 'id': '123'}
    
    async def get_download_urls(self, info: Dict[str, Any]) -> List[str]:
        return ['http://test.com/video.mp4']
    
    async def get_metadata(self, url: str):
        from app.data.models.core import VideoMetadata
        from datetime import datetime
        return VideoMetadata(
            title='Test Video',
            author='Test Author',
            thumbnail_url='',
            duration=120,
            view_count=1000,
            upload_date=datetime.now(),
            quality_options=[]
        )
    
    def get_extractor_info(self) -> ExtractorInfo:
        return ExtractorInfo(
            name='Test Extractor',
            version='1.0.0',
            supported_domains=self.supported_domains,
            description='Test extractor'
        )
'''
        
        (self.plugin_dir / 'test_plugin.py').write_text(test_plugin_content)
        
        self.manager = PluginManager(
            plugin_directories=[str(self.plugin_dir)],
            enable_hot_reload=False
        )
    
    def teardown_method(self):
        """Clean up test environment"""
        asyncio.run(self.manager.shutdown())
        shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test plugin manager initialization"""
        success = await self.manager.initialize()
        assert success
        assert self.manager._initialized
        
        # Check that plugin was loaded
        plugins = self.manager.get_all_plugins()
        assert 'test_plugin' in plugins
    
    @pytest.mark.asyncio
    async def test_load_plugin(self):
        """Test loading a specific plugin"""
        await self.manager.initialize()
        
        # Plugin should already be loaded during initialization
        plugin = self.manager.get_plugin_info('test_plugin')
        assert plugin is not None
        assert plugin.name == 'test_plugin'
    
    @pytest.mark.asyncio
    async def test_route_url(self):
        """Test URL routing"""
        await self.manager.initialize()
        
        result = await self.manager.route_url('https://test.com/video')
        assert result.success
        assert result.plugin is not None
        assert result.plugin.name == 'test_plugin'
    
    @pytest.mark.asyncio
    async def test_extract_info(self):
        """Test extracting information from URL"""
        await self.manager.initialize()
        
        info = await self.manager.extract_info('https://test.com/video')
        assert info is not None
        assert info['title'] == 'Test Video'
        assert info['id'] == '123'
    
    @pytest.mark.asyncio
    async def test_get_metadata(self):
        """Test getting metadata from URL"""
        await self.manager.initialize()
        
        metadata = await self.manager.get_metadata('https://test.com/video')
        assert metadata is not None
        assert metadata.title == 'Test Video'
        assert metadata.author == 'Test Author'
    
    def test_get_supported_domains(self):
        """Test getting supported domains"""
        asyncio.run(self.manager.initialize())
        
        domains = self.manager.get_supported_domains()
        assert 'test.com' in domains
    
    def test_is_url_supported(self):
        """Test checking if URL is supported"""
        asyncio.run(self.manager.initialize())
        
        assert self.manager.is_url_supported('https://test.com/video')
        assert not self.manager.is_url_supported('https://unsupported.com/video')
    
    def test_get_statistics(self):
        """Test getting plugin manager statistics"""
        asyncio.run(self.manager.initialize())
        
        stats = self.manager.get_statistics()
        assert stats.total_plugins >= 1
        assert stats.active_plugins >= 1


if __name__ == '__main__':
    pytest.main([__file__])