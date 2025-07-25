"""
File management utilities for video downloader.
Handles file verification, deduplication, and naming.
"""
import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import re
import json
from datetime import datetime


class DuplicateAction(Enum):
    """Actions to take when duplicate files are found"""
    OVERWRITE = "overwrite"
    SKIP = "skip"
    RENAME = "rename"
    ASK = "ask"


class FileManager:
    """File management utilities"""
    
    def __init__(self):
        self.duplicate_action = DuplicateAction.ASK
        self.naming_template = "%(title)s.%(ext)s"
        self.max_filename_length = 255
    
    def calculate_md5(self, file_path: str, chunk_size: int = 8192) -> Optional[str]:
        """
        Calculate MD5 hash of a file.
        
        Args:
            file_path: Path to the file
            chunk_size: Size of chunks to read (default 8KB)
            
        Returns:
            MD5 hash string or None if file doesn't exist
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            md5_hash = hashlib.md5()
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    md5_hash.update(chunk)
            
            return md5_hash.hexdigest()
        except Exception as e:
            print(f"Error calculating MD5 for {file_path}: {e}")
            return None
    
    def verify_file_integrity(self, file_path: str, expected_md5: str) -> bool:
        """
        Verify file integrity using MD5 hash.
        
        Args:
            file_path: Path to the file to verify
            expected_md5: Expected MD5 hash
            
        Returns:
            True if file is valid, False otherwise
        """
        if not expected_md5:
            return True  # No hash to verify against
        
        actual_md5 = self.calculate_md5(file_path)
        if actual_md5 is None:
            return False
        
        return actual_md5.lower() == expected_md5.lower()
    
    def find_duplicates(self, file_path: str, search_dirs: List[str]) -> List[str]:
        """
        Find duplicate files based on MD5 hash.
        
        Args:
            file_path: Path to the file to check
            search_dirs: Directories to search for duplicates
            
        Returns:
            List of paths to duplicate files
        """
        if not os.path.exists(file_path):
            return []
        
        file_md5 = self.calculate_md5(file_path)
        if not file_md5:
            return []
        
        duplicates = []
        file_size = os.path.getsize(file_path)
        
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
            
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    candidate_path = os.path.join(root, file)
                    
                    # Skip the original file
                    if os.path.samefile(candidate_path, file_path):
                        continue
                    
                    # Quick size check first
                    try:
                        if os.path.getsize(candidate_path) != file_size:
                            continue
                    except OSError:
                        continue
                    
                    # Calculate MD5 for potential duplicate
                    candidate_md5 = self.calculate_md5(candidate_path)
                    if candidate_md5 == file_md5:
                        duplicates.append(candidate_path)
        
        return duplicates
    
    def handle_duplicate_file(self, target_path: str, action: Optional[DuplicateAction] = None) -> Tuple[str, bool]:
        """
        Handle duplicate file based on specified action.
        
        Args:
            target_path: Path where file should be saved
            action: Action to take (uses default if None)
            
        Returns:
            Tuple of (final_path, should_proceed)
        """
        if not os.path.exists(target_path):
            return target_path, True
        
        action = action or self.duplicate_action
        
        if action == DuplicateAction.OVERWRITE:
            return target_path, True
        
        elif action == DuplicateAction.SKIP:
            return target_path, False
        
        elif action == DuplicateAction.RENAME:
            return self._generate_unique_filename(target_path), True
        
        else:  # ASK - for now, default to rename
            return self._generate_unique_filename(target_path), True
    
    def _generate_unique_filename(self, file_path: str) -> str:
        """
        Generate a unique filename by adding a number suffix.
        
        Args:
            file_path: Original file path
            
        Returns:
            Unique file path
        """
        path = Path(file_path)
        base_name = path.stem
        extension = path.suffix
        directory = path.parent
        
        counter = 1
        while True:
            new_name = f"{base_name} ({counter}){extension}"
            new_path = directory / new_name
            
            if not new_path.exists():
                return str(new_path)
            
            counter += 1
            
            # Prevent infinite loop
            if counter > 9999:
                # Use timestamp as fallback
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_name = f"{base_name}_{timestamp}{extension}"
                return str(directory / new_name)
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by removing invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        import platform
        
        # On Windows, colons are not allowed in filenames, so convert time formats
        if platform.system() == 'Windows':
            # Replace time formats (HH:MM:SS) with Windows-safe format (HH-MM-SS)
            time_pattern = r'\b(\d{1,2}):(\d{2}):(\d{2})\b'
            filename = re.sub(time_pattern, r'\1-\2-\3', filename)
        
        # Remove invalid characters for Windows/Unix
        invalid_chars = r'[<>:"/\\|?*]'
        filename = re.sub(invalid_chars, '_', filename)
        
        # Remove control characters
        filename = ''.join(char for char in filename if ord(char) >= 32)
        
        # Trim whitespace and dots
        filename = filename.strip(' .')
        
        # Ensure filename is not empty
        if not filename:
            filename = "untitled"
        
        # Truncate if too long
        if len(filename) > self.max_filename_length:
            name, ext = os.path.splitext(filename)
            max_name_length = self.max_filename_length - len(ext)
            filename = name[:max_name_length] + ext
        
        return filename
    
    def create_directory(self, directory_path: str) -> bool:
        """
        Create directory if it doesn't exist.
        
        Args:
            directory_path: Path to create
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(directory_path, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory {directory_path}: {e}")
            return False
    
    def move_file_safely(self, source_path: str, target_path: str) -> bool:
        """
        Move file safely with error handling.
        
        Args:
            source_path: Source file path
            target_path: Target file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure target directory exists
            target_dir = os.path.dirname(target_path)
            self.create_directory(target_dir)
            
            # Handle duplicate
            final_path, should_proceed = self.handle_duplicate_file(target_path)
            
            if not should_proceed:
                return False
            
            # Move file
            shutil.move(source_path, final_path)
            return True
            
        except Exception as e:
            print(f"Error moving file from {source_path} to {target_path}: {e}")
            return False
    
    def copy_file_safely(self, source_path: str, target_path: str) -> bool:
        """
        Copy file safely with error handling.
        
        Args:
            source_path: Source file path
            target_path: Target file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure target directory exists
            target_dir = os.path.dirname(target_path)
            self.create_directory(target_dir)
            
            # Handle duplicate
            final_path, should_proceed = self.handle_duplicate_file(target_path)
            
            if not should_proceed:
                return False
            
            # Copy file
            shutil.copy2(source_path, final_path)
            return True
            
        except Exception as e:
            print(f"Error copying file from {source_path} to {target_path}: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive file information.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information or None if file doesn't exist
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            
            return {
                'path': file_path,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'accessed': datetime.fromtimestamp(stat.st_atime),
                'md5': self.calculate_md5(file_path),
                'extension': os.path.splitext(file_path)[1].lower(),
                'basename': os.path.basename(file_path)
            }
            
        except Exception as e:
            print(f"Error getting file info for {file_path}: {e}")
            return None
    
    def cleanup_temp_files(self, temp_dir: str, max_age_hours: int = 24) -> int:
        """
        Clean up temporary files older than specified age.
        
        Args:
            temp_dir: Temporary directory to clean
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of files cleaned up
        """
        if not os.path.exists(temp_dir):
            return 0
        
        cleaned_count = 0
        max_age_seconds = max_age_hours * 3600
        current_time = datetime.now().timestamp()
        
        try:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_age = current_time - os.path.getmtime(file_path)
                        if file_age > max_age_seconds:
                            os.remove(file_path)
                            cleaned_count += 1
                    except Exception as e:
                        print(f"Error cleaning up {file_path}: {e}")
        
        except Exception as e:
            print(f"Error cleaning temp directory {temp_dir}: {e}")
        
        return cleaned_count


# Global file manager instance
file_manager = FileManager()