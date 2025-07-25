"""
File naming template system for video downloader.
Supports dynamic filename generation based on video metadata.
"""
import re
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..utils.file_manager import file_manager


class NamingTemplate:
    """File naming template processor"""
    
    # Default templates
    DEFAULT_TEMPLATES = {
        'simple': '%(title)s.%(ext)s',
        'with_author': '%(author)s - %(title)s.%(ext)s',
        'with_date': '%(upload_date)s - %(title)s.%(ext)s',
        'organized': '%(author)s/%(upload_date)s - %(title)s.%(ext)s',
        'quality': '%(title)s [%(quality)s].%(ext)s',
        'full': '%(author)s - %(title)s [%(quality)s] (%(upload_date)s).%(ext)s'
    }
    
    # Available template variables
    TEMPLATE_VARIABLES = {
        'title': 'Video title',
        'author': 'Video author/uploader',
        'upload_date': 'Upload date (YYYY-MM-DD)',
        'upload_year': 'Upload year (YYYY)',
        'upload_month': 'Upload month (MM)',
        'upload_day': 'Upload day (DD)',
        'quality': 'Video quality (e.g., 1080p)',
        'format': 'Video format (e.g., mp4)',
        'ext': 'File extension',
        'duration': 'Video duration (HH:MM:SS)',
        'duration_sec': 'Video duration in seconds',
        'view_count': 'View count',
        'like_count': 'Like count',
        'platform': 'Platform name',
        'video_id': 'Video ID',
        'channel_id': 'Channel ID',
        'index': 'Index number (for batch downloads)',
        'timestamp': 'Current timestamp (YYYY-MM-DD_HH-MM-SS)'
    }
    
    def __init__(self):
        self.custom_templates: Dict[str, str] = {}
        self.load_custom_templates()
    
    def load_custom_templates(self):
        """Load custom templates from configuration"""
        # This would typically load from a config file
        # For now, we'll use an empty dict
        pass
    
    def save_custom_templates(self):
        """Save custom templates to configuration"""
        # This would typically save to a config file
        pass
    
    def add_custom_template(self, name: str, template: str) -> bool:
        """
        Add a custom naming template.
        
        Args:
            name: Template name
            template: Template string
            
        Returns:
            True if template is valid and added, False otherwise
        """
        if self.validate_template(template):
            self.custom_templates[name] = template
            self.save_custom_templates()
            return True
        return False
    
    def remove_custom_template(self, name: str) -> bool:
        """
        Remove a custom template.
        
        Args:
            name: Template name to remove
            
        Returns:
            True if removed, False if not found
        """
        if name in self.custom_templates:
            del self.custom_templates[name]
            self.save_custom_templates()
            return True
        return False
    
    def get_all_templates(self) -> Dict[str, str]:
        """Get all available templates (default + custom)"""
        templates = self.DEFAULT_TEMPLATES.copy()
        templates.update(self.custom_templates)
        return templates
    
    def validate_template(self, template: str) -> bool:
        """
        Validate a template string.
        
        Args:
            template: Template string to validate
            
        Returns:
            True if template is valid, False otherwise
        """
        try:
            # Check for valid template syntax
            test_data = {var: f"test_{var}" for var in self.TEMPLATE_VARIABLES.keys()}
            test_data['ext'] = 'mp4'
            
            # Try to format the template
            result = template % test_data
            
            # Check if result would be a valid filename
            sanitized = file_manager.sanitize_filename(result)
            
            return len(sanitized) > 0 and sanitized != "untitled"
            
        except (KeyError, TypeError, ValueError):
            return False
    
    def format_filename(self, template: str, metadata: Dict[str, Any], 
                       quality: Optional[str] = None, 
                       format_ext: Optional[str] = None,
                       index: Optional[int] = None) -> str:
        """
        Format filename using template and metadata.
        
        Args:
            template: Template string
            metadata: Video metadata dictionary
            quality: Video quality string
            format_ext: File extension
            index: Index number for batch downloads
            
        Returns:
            Formatted filename
        """
        try:
            # Prepare template variables
            template_vars = self._prepare_template_vars(metadata, quality, format_ext, index)
            
            # Format template
            filename = template % template_vars
            
            # Sanitize filename
            filename = file_manager.sanitize_filename(filename)
            
            return filename
            
        except Exception as e:
            print(f"Error formatting filename with template '{template}': {e}")
            # Fallback to simple template
            fallback = f"{template_vars.get('title', 'untitled')}.{template_vars.get('ext', 'mp4')}"
            return file_manager.sanitize_filename(fallback)
    
    def _prepare_template_vars(self, metadata: Dict[str, Any], 
                              quality: Optional[str] = None,
                              format_ext: Optional[str] = None,
                              index: Optional[int] = None) -> Dict[str, str]:
        """
        Prepare template variables from metadata.
        
        Args:
            metadata: Video metadata
            quality: Video quality
            format_ext: File extension
            index: Index number
            
        Returns:
            Dictionary of template variables
        """
        vars_dict = {}
        
        # Basic info
        vars_dict['title'] = str(metadata.get('title', 'Untitled')).strip()
        vars_dict['author'] = str(metadata.get('author', 'Unknown')).strip()
        vars_dict['platform'] = str(metadata.get('platform', 'unknown')).lower()
        vars_dict['video_id'] = str(metadata.get('video_id', ''))
        vars_dict['channel_id'] = str(metadata.get('channel_id', ''))
        
        # Date formatting
        upload_date = metadata.get('upload_date')
        if isinstance(upload_date, datetime):
            vars_dict['upload_date'] = upload_date.strftime('%Y-%m-%d')
            vars_dict['upload_year'] = upload_date.strftime('%Y')
            vars_dict['upload_month'] = upload_date.strftime('%m')
            vars_dict['upload_day'] = upload_date.strftime('%d')
        else:
            vars_dict['upload_date'] = 'unknown'
            vars_dict['upload_year'] = 'unknown'
            vars_dict['upload_month'] = 'unknown'
            vars_dict['upload_day'] = 'unknown'
        
        # Duration formatting
        duration = metadata.get('duration', 0)
        if isinstance(duration, (int, float)) and duration > 0:
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = int(duration % 60)
            vars_dict['duration'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            vars_dict['duration_sec'] = str(int(duration))
        else:
            vars_dict['duration'] = '00:00:00'
            vars_dict['duration_sec'] = '0'
        
        # Counts
        vars_dict['view_count'] = str(metadata.get('view_count', 0))
        vars_dict['like_count'] = str(metadata.get('like_count', 0))
        
        # Quality and format
        vars_dict['quality'] = quality or 'unknown'
        vars_dict['format'] = format_ext or 'mp4'
        vars_dict['ext'] = format_ext or 'mp4'
        
        # Index for batch downloads
        if index is not None:
            vars_dict['index'] = f"{index:03d}"
        else:
            vars_dict['index'] = '001'
        
        # Current timestamp
        vars_dict['timestamp'] = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # Clean up all variables to ensure they're filename-safe
        for key, value in vars_dict.items():
            if isinstance(value, str):
                # Don't sanitize duration format - it's already safe
                if key != 'duration':
                    # Remove path separators and other problematic characters
                    value = re.sub(r'[<>"/\\|?*]', '_', value)
                    # Keep colons for time formats in duration
                    value = value.strip(' .')
                    if not value:
                        value = 'unknown'
                vars_dict[key] = value
        
        return vars_dict
    
    def preview_filename(self, template: str, sample_metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Preview how a filename would look with sample data.
        
        Args:
            template: Template string
            sample_metadata: Sample metadata (uses default if None)
            
        Returns:
            Preview filename
        """
        if sample_metadata is None:
            sample_metadata = {
                'title': 'Sample Video Title',
                'author': 'Sample Author',
                'upload_date': datetime(2024, 1, 15),
                'duration': 3661,  # 1:01:01
                'view_count': 12345,
                'like_count': 678,
                'platform': 'youtube',
                'video_id': 'abc123',
                'channel_id': 'channel123'
            }
        
        return self.format_filename(template, sample_metadata, '1080p', 'mp4', 1)
    
    def get_template_help(self) -> str:
        """
        Get help text for template variables.
        
        Returns:
            Help text string
        """
        help_text = "Available template variables:\n\n"
        
        for var, description in self.TEMPLATE_VARIABLES.items():
            help_text += f"  %({var})s - {description}\n"
        
        help_text += "\nExample templates:\n"
        
        for name, template in self.DEFAULT_TEMPLATES.items():
            preview = self.preview_filename(template)
            help_text += f"  {name}: {template}\n    → {preview}\n\n"
        
        return help_text
    
    def suggest_template(self, preferences: Dict[str, bool]) -> str:
        """
        Suggest a template based on user preferences.
        
        Args:
            preferences: Dictionary of preferences
                - include_author: Include author in filename
                - include_date: Include upload date
                - include_quality: Include video quality
                - organize_by_author: Create author subdirectories
                
        Returns:
            Suggested template string
        """
        template_parts = []
        
        # Directory structure
        if preferences.get('organize_by_author', False):
            template_parts.append('%(author)s/')
        
        # Filename components
        filename_parts = []
        
        if preferences.get('include_author', True):
            filename_parts.append('%(author)s')
        
        filename_parts.append('%(title)s')
        
        if preferences.get('include_quality', False):
            filename_parts.append('[%(quality)s]')
        
        if preferences.get('include_date', False):
            filename_parts.append('(%(upload_date)s)')
        
        # Combine parts
        template_parts.append(' - '.join(filename_parts))
        template_parts.append('.%(ext)s')
        
        return ''.join(template_parts)


# Global naming template instance
naming_template = NamingTemplate()