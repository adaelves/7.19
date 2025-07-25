"""
Tests for ConfigService
"""
import os
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from app.services.config_service import ConfigService, BackupInfo
from app.core.config import ConfigManager, AppConfig


class TestConfigService:
    """Test ConfigService functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.config = AppConfig()
        self.config_manager.config.config_path = self.temp_dir
        self.config_service = ConfigService(self.config_manager)
    
    def teardown_method(self):
        """Cleanup test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_export_config_basic(self):
        """Test basic configuration export"""
        export_path = os.path.join(self.temp_dir, "export.json")
        
        result = self.config_service.export_config(export_path, include_data=False)
        
        assert result is True
        assert os.path.exists(export_path)
        
        with open(export_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "config" in data
        assert "export_timestamp" in data
        assert "app_version" in data
        assert data["include_data"] is False
    
    @patch('app.services.config_service.DatabaseConnection')
    def test_export_config_with_data(self, mock_db):
        """Test configuration export with database data"""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        mock_cursor.description = []
        mock_db.return_value.get_connection.return_value.__enter__.return_value = mock_conn
        
        export_path = os.path.join(self.temp_dir, "export_with_data.json")
        
        result = self.config_service.export_config(export_path, include_data=True)
        
        assert result is True
        assert os.path.exists(export_path)
        
        with open(export_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data["include_data"] is True
        assert "database_data" in data
    
    def test_import_config_replace(self):
        """Test configuration import with replace mode"""
        # Create test import file
        import_data = {
            "config": {
                "app_name": "Test App",
                "app_version": "2.0.0",
                "download_path": "/test/path",
                "theme": "dark"
            },
            "include_data": False
        }
        
        import_path = os.path.join(self.temp_dir, "import.json")
        with open(import_path, 'w', encoding='utf-8') as f:
            json.dump(import_data, f)
        
        result = self.config_service.import_config(import_path, merge=False)
        
        assert result is True
        assert self.config_manager.config.app_name == "Test App"
        assert self.config_manager.config.app_version == "2.0.0"
        assert self.config_manager.config.theme == "dark"
        self.config_manager.save.assert_called_once()
    
    def test_import_config_merge(self):
        """Test configuration import with merge mode"""
        # Set initial config
        self.config_manager.config.app_name = "Original App"
        self.config_manager.config.theme = "light"
        
        # Create test import file with partial config
        import_data = {
            "config": {
                "theme": "dark",
                "max_concurrent_downloads": 5
            },
            "include_data": False
        }
        
        import_path = os.path.join(self.temp_dir, "import_merge.json")
        with open(import_path, 'w', encoding='utf-8') as f:
            json.dump(import_data, f)
        
        result = self.config_service.import_config(import_path, merge=True)
        
        assert result is True
        # Original values should be preserved where not overridden
        assert self.config_manager.config.app_name == "Original App"
        # New values should be applied
        assert self.config_manager.config.theme == "dark"
        assert self.config_manager.config.max_concurrent_downloads == 5
    
    def test_create_backup(self):
        """Test backup creation"""
        with patch.object(self.config_service, '_export_database_data', return_value={}):
            result = self.config_service.create_backup("test_backup", "Test description")
        
        assert result is True
        
        # Check backup file exists
        backup_files = list(self.config_service.backup_dir.glob("test_backup_*.json"))
        assert len(backup_files) == 1
        
        # Verify backup content
        with open(backup_files[0], 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        assert backup_data["name"] == "test_backup"
        assert backup_data["description"] == "Test description"
        assert "timestamp" in backup_data
        assert "config" in backup_data
        assert "database_data" in backup_data
    
    def test_list_backups(self):
        """Test backup listing"""
        # Create test backups
        with patch.object(self.config_service, '_export_database_data', return_value={}):
            self.config_service.create_backup("backup1", "First backup")
            self.config_service.create_backup("backup2", "Second backup")
        
        backups = self.config_service.list_backups()
        
        assert len(backups) == 2
        assert all(isinstance(backup, BackupInfo) for backup in backups)
        
        # Should be sorted by timestamp (newest first)
        assert backups[0].timestamp >= backups[1].timestamp
    
    def test_delete_backup(self):
        """Test backup deletion"""
        # Create test backup
        with patch.object(self.config_service, '_export_database_data', return_value={}):
            self.config_service.create_backup("test_delete", "To be deleted")
        
        # Verify backup exists
        backup_files = list(self.config_service.backup_dir.glob("test_delete_*.json"))
        assert len(backup_files) == 1
        
        # Delete backup
        result = self.config_service.delete_backup("test_delete")
        
        assert result is True
        
        # Verify backup is deleted
        backup_files = list(self.config_service.backup_dir.glob("test_delete_*.json"))
        assert len(backup_files) == 0
    
    @patch('app.services.config_service.DatabaseConnection')
    def test_restore_backup(self, mock_db):
        """Test backup restoration"""
        # Mock database connection
        mock_conn = MagicMock()
        mock_db.return_value.get_connection.return_value.__enter__.return_value = mock_conn
        
        # Create test backup
        backup_data = {
            "name": "test_restore",
            "description": "Test restore",
            "timestamp": datetime.now().isoformat(),
            "config": {
                "app_name": "Restored App",
                "theme": "dark"
            },
            "database_data": {
                "downloads": [],
                "creators": []
            }
        }
        
        backup_path = self.config_service.backup_dir / "test_restore_20240101_120000.json"
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f)
        
        result = self.config_service.restore_backup("test_restore")
        
        assert result is True
        assert self.config_manager.config.app_name == "Restored App"
        assert self.config_manager.config.theme == "dark"
        self.config_manager.save.assert_called_once()
    
    def test_migrate_user_data(self):
        """Test user data migration"""
        with patch.object(self.config_service, 'create_backup', return_value=True), \
             patch.object(self.config_service, '_needs_database_migration', return_value=True), \
             patch.object(self.config_service, '_needs_config_migration', return_value=True), \
             patch.object(self.config_service, '_migrate_database_schema'), \
             patch.object(self.config_service, '_migrate_config_format'):
            
            result = self.config_service.migrate_user_data("1.0.0", "1.1.0")
            
            assert result is True
            assert self.config_manager.config.app_version == "1.1.0"
            self.config_manager.save.assert_called_once()
    
    def test_reset_to_defaults(self):
        """Test reset to defaults"""
        with patch.object(self.config_service, 'create_backup', return_value=True), \
             patch.object(self.config_service, '_clear_database_data'), \
             patch.object(self.config_service, '_clear_downloaded_files'):
            
            result = self.config_service.reset_to_defaults(keep_downloads=False, keep_history=False)
            
            assert result is True
            self.config_manager.reset_to_defaults.assert_called_once()
    
    def test_cleanup_old_data(self):
        """Test old data cleanup"""
        with patch.object(self.config_service, '_cleanup_old_database_entries'), \
             patch.object(self.config_service, '_cleanup_temp_files'):
            
            # Create old backup file
            old_backup = self.config_service.backup_dir / "old_backup.json"
            old_backup.touch()
            # Set modification time to 40 days ago
            old_time = datetime.now().timestamp() - (40 * 24 * 3600)
            os.utime(old_backup, (old_time, old_time))
            
            result = self.config_service.cleanup_old_data(days_to_keep=30)
            
            assert result is True
            assert not old_backup.exists()
    
    def test_get_storage_usage(self):
        """Test storage usage calculation"""
        # Create test files
        config_dir = Path(self.config_manager.config.config_path)
        config_dir.mkdir(exist_ok=True)
        
        test_file = config_dir / "test.txt"
        test_file.write_text("test content")
        
        usage = self.config_service.get_storage_usage()
        
        assert isinstance(usage, dict)
        assert "config" in usage
        assert "database" in usage
        assert "backups" in usage
        assert "downloads" in usage
        assert "temp" in usage
        assert usage["config"] > 0  # Should include our test file


if __name__ == "__main__":
    pytest.main([__file__])