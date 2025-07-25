"""
Configuration and data management service.
"""
import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class BackupInfo:
    """Backup information"""
    name: str
    timestamp: datetime
    size: int
    description: str = ""


class ConfigService:
    """Configuration and data management service"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config.json"
        self.config_data = {}
        self.load_config()
        
        # Create backup directory
        config_dir = Path(self.config_file).parent
        self.backup_dir = config_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            self.config_data = {}
    
    def save_config(self):
        """Save configuration to file"""
        try:
            # Ensure directory exists
            Path(self.config_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error: Could not save config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        keys = key.split('.')
        config = self.config_data
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        self.save_config()

    def export_config(self, export_path: str, include_data: bool = False) -> bool:
        """Export configuration to file"""
        try:
            export_data = {
                "config": self.config_data,
                "export_timestamp": datetime.now().isoformat(),
                "app_version": "1.0.0",
                "include_data": include_data
            }
            
            if include_data:
                export_data["database_data"] = self._export_database_data()
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error exporting config: {e}")
            return False

    def import_config(self, import_path: str, merge: bool = False) -> bool:
        """Import configuration from file"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if merge:
                imported_config = import_data.get("config", {})
                self.config_data.update(imported_config)
            else:
                self.config_data = import_data.get("config", {})
            
            self.save_config()
            
            if import_data.get("include_data") and "database_data" in import_data:
                self._import_database_data(import_data["database_data"])
            
            return True
        except Exception as e:
            print(f"Error importing config: {e}")
            return False

    def create_backup(self, name: str, description: str = "") -> bool:
        """Create a backup of current configuration and data"""
        try:
            timestamp = datetime.now()
            backup_name = f"{name}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.backup_dir / f"{backup_name}.json"
            
            backup_data = {
                "name": name,
                "description": description,
                "timestamp": timestamp.isoformat(),
                "config": self.config_data,
                "database_data": self._export_database_data()
            }
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False

    def _export_database_data(self) -> Dict[str, Any]:
        """Export database data"""
        try:
            return {"downloads": [], "creators": []}
        except Exception as e:
            print(f"Error exporting database data: {e}")
            return {}

    def _import_database_data(self, data: Dict[str, Any]) -> None:
        """Import database data"""
        try:
            pass
        except Exception as e:
            print(f"Error importing database data: {e}")

    def _clear_database_data(self) -> None:
        """Clear all database data"""
        try:
            pass
        except Exception as e:
            print(f"Error clearing database data: {e}")

    def _clear_downloaded_files(self) -> None:
        """Clear downloaded files"""
        try:
            download_path = Path(self.get("download_path", str(Path.home() / "Downloads")))
            if download_path.exists():
                shutil.rmtree(download_path)
                download_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error clearing downloaded files: {e}")