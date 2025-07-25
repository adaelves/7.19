"""
Download history management service.
Provides functionality for managing download history, search, filtering, and duplicate detection.
"""
import hashlib
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict

from ..data.database.repositories import DownloadHistoryRepository
from ..data.database.connection import DatabaseConnection
from ..data.models.core import DownloadTask, VideoMetadata, Platform


class HistoryService:
    """Service for managing download history"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
        self.history_repo = DownloadHistoryRepository(db_connection)
    
    def add_download_record(self, task: DownloadTask, metadata: Optional[VideoMetadata] = None) -> int:
        """Add download record to history"""
        # Calculate MD5 hash if file exists
        if task.download_path and Path(task.download_path).exists():
            md5_hash = self._calculate_file_md5(task.download_path)
            # Update the record with MD5 hash
            record_id = self.history_repo.create(task, metadata)
            if record_id:
                self.history_repo.update_md5(record_id, md5_hash)
            return record_id
        else:
            return self.history_repo.create(task, metadata)
    
    def get_history(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get download history with pagination"""
        # Get more records and slice for pagination
        all_records = self.history_repo.get_recent(limit + offset)
        return all_records[offset:offset + limit]
    
    def search_history(self, keyword: str, platform: Optional[str] = None, 
                      date_from: Optional[datetime] = None, date_to: Optional[datetime] = None,
                      limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Search download history with filters"""
        # Basic keyword search
        results = self.history_repo.search(keyword, platform, limit, offset)
        
        # Apply date filters if specified
        if date_from or date_to:
            filtered_results = []
            for record in results:
                download_date = record.get('download_date')
                if isinstance(download_date, str):
                    try:
                        download_date = datetime.fromisoformat(download_date.replace(' ', 'T'))
                    except ValueError:
                        continue
                
                # Check date range
                if date_from and download_date < date_from:
                    continue
                if date_to and download_date > date_to:
                    continue
                
                filtered_results.append(record)
            
            return filtered_results
        
        return results
    
    def get_history_by_platform(self, platform: str) -> List[Dict[str, Any]]:
        """Get download history filtered by platform"""
        return self.history_repo.get_by_platform(platform)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get download statistics"""
        stats = self.history_repo.get_statistics()
        
        # Add additional statistics
        stats['recent_downloads'] = len(self.get_recent_downloads(days=7))
        stats['platforms_count'] = len(stats.get('by_platform', {}))
        
        # Format file size
        total_size = stats.get('total_size', 0)
        stats['total_size_formatted'] = self._format_file_size(total_size)
        
        return stats
    
    def get_recent_downloads(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get downloads from recent days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get all recent downloads and filter by date
        all_downloads = self.history_repo.get_recent(1000)  # Get more records for filtering
        recent_downloads = []
        
        for record in all_downloads:
            download_date = record.get('download_date')
            if isinstance(download_date, str):
                try:
                    download_date = datetime.fromisoformat(download_date.replace(' ', 'T'))
                    if download_date >= cutoff_date:
                        recent_downloads.append(record)
                except ValueError:
                    continue
        
        return recent_downloads
    
    def check_duplicate_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Check if URL has been downloaded before"""
        records = self.history_repo.get_by_url(url)
        return records[0] if records else None
    
    def check_duplicate_by_md5(self, md5_hash: str) -> Optional[Dict[str, Any]]:
        """Check if file with same MD5 exists"""
        return self.history_repo.get_by_md5(md5_hash)
    
    def detect_duplicates(self) -> List[Tuple[Dict[str, Any], List[Dict[str, Any]]]]:
        """Detect duplicate files in download history"""
        duplicates = []
        
        # Get all records with MD5 hashes
        all_records = self.history_repo.get_recent(10000)  # Get large number for analysis
        md5_groups = {}
        
        for record in all_records:
            md5_hash = record.get('md5_hash')
            if md5_hash:
                if md5_hash not in md5_groups:
                    md5_groups[md5_hash] = []
                md5_groups[md5_hash].append(record)
        
        # Find groups with multiple records
        for md5_hash, records in md5_groups.items():
            if len(records) > 1:
                # Sort by download date, newest first
                records.sort(key=lambda x: x.get('download_date', ''), reverse=True)
                original = records[0]
                duplicates_list = records[1:]
                duplicates.append((original, duplicates_list))
        
        return duplicates
    
    def delete_record(self, record_id: int) -> bool:
        """Delete download history record"""
        return self.history_repo.delete(record_id)
    
    def export_history(self, export_path: str, format: str = 'csv', 
                      filters: Optional[Dict[str, Any]] = None) -> bool:
        """Export download history to file"""
        try:
            # Get records to export
            if filters:
                keyword = filters.get('keyword', '')
                platform = filters.get('platform')
                date_from = filters.get('date_from')
                date_to = filters.get('date_to')
                records = self.search_history(keyword, platform, date_from, date_to, limit=10000)
            else:
                records = self.history_repo.get_recent(10000)
            
            export_path = Path(export_path)
            
            if format.lower() == 'csv':
                return self._export_to_csv(records, export_path)
            elif format.lower() == 'json':
                return self._export_to_json(records, export_path)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            print(f"Export failed: {e}")
            return False
    
    def _export_to_csv(self, records: List[Dict[str, Any]], export_path: Path) -> bool:
        """Export records to CSV file"""
        if not records:
            return False
        
        # Define CSV columns
        columns = [
            'id', 'url', 'title', 'author', 'platform', 'file_path',
            'file_size', 'download_date', 'duration', 'view_count',
            'quality', 'format', 'status'
        ]
        
        with open(export_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            
            for record in records:
                # Filter record to only include defined columns
                filtered_record = {col: record.get(col, '') for col in columns}
                # Format file size
                if filtered_record['file_size']:
                    filtered_record['file_size'] = self._format_file_size(filtered_record['file_size'])
                writer.writerow(filtered_record)
        
        return True
    
    def _export_to_json(self, records: List[Dict[str, Any]], export_path: Path) -> bool:
        """Export records to JSON file"""
        if not records:
            return False
        
        # Prepare data for JSON export
        export_data = {
            'export_date': datetime.now().isoformat(),
            'total_records': len(records),
            'records': records
        }
        
        with open(export_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, ensure_ascii=False, default=str)
        
        return True
    
    def _calculate_file_md5(self, file_path: str) -> str:
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (IOError, OSError):
            return ""
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"
    
    def cleanup_old_records(self, days_to_keep: int = 365) -> int:
        """Clean up old download records"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Get old records
        all_records = self.history_repo.get_recent(10000)
        deleted_count = 0
        
        for record in all_records:
            download_date = record.get('download_date')
            if isinstance(download_date, str):
                try:
                    download_date = datetime.fromisoformat(download_date.replace(' ', 'T'))
                    if download_date < cutoff_date:
                        if self.history_repo.delete(record['id']):
                            deleted_count += 1
                except ValueError:
                    continue
        
        return deleted_count
    
    def get_download_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get download trends and analytics"""
        recent_downloads = self.get_recent_downloads(days)
        
        # Group by date
        daily_counts = {}
        platform_counts = {}
        
        for record in recent_downloads:
            download_date = record.get('download_date')
            platform = record.get('platform', 'Unknown')
            
            if isinstance(download_date, str):
                try:
                    date_obj = datetime.fromisoformat(download_date.replace(' ', 'T'))
                    date_key = date_obj.strftime('%Y-%m-%d')
                    
                    # Count by date
                    daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
                    
                    # Count by platform
                    platform_counts[platform] = platform_counts.get(platform, 0) + 1
                    
                except ValueError:
                    continue
        
        return {
            'daily_downloads': daily_counts,
            'platform_distribution': platform_counts,
            'total_recent': len(recent_downloads),
            'average_per_day': len(recent_downloads) / days if days > 0 else 0
        }