"""
Base extractor abstract class defining the interface for platform-specific extractors.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.data.models.core import VideoMetadata, QualityOption


@dataclass
class ExtractorInfo:
    """Information about an extractor"""
    name: str
    version: str
    supported_domains: List[str]
    description: str
    author: Optional[str] = None


class BaseExtractor(ABC):
    """
    Abstract base class for all platform extractors.
    Each platform plugin must inherit from this class and implement the required methods.
    """
    
    def __init__(self):
        self._info = self.get_extractor_info()
    
    @property
    @abstractmethod
    def supported_domains(self) -> List[str]:
        """
        Return list of domains this extractor can handle.
        
        Returns:
            List of domain names (e.g., ['youtube.com', 'youtu.be'])
        """
        pass
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """
        Check if this extractor can handle the given URL.
        
        Args:
            url: The URL to check
            
        Returns:
            True if this extractor can handle the URL, False otherwise
        """
        pass
    
    @abstractmethod
    async def extract_info(self, url: str) -> Dict[str, Any]:
        """
        Extract information from the given URL.
        
        Args:
            url: The URL to extract information from
            
        Returns:
            Dictionary containing extracted information
        """
        pass
    
    @abstractmethod
    async def get_download_urls(self, info: Dict[str, Any]) -> List[str]:
        """
        Get direct download URLs from extracted information.
        
        Args:
            info: Information dictionary from extract_info()
            
        Returns:
            List of direct download URLs
        """
        pass
    
    @abstractmethod
    async def get_metadata(self, url: str) -> VideoMetadata:
        """
        Extract metadata from the given URL.
        
        Args:
            url: The URL to extract metadata from
            
        Returns:
            VideoMetadata object containing the extracted information
        """
        pass
    
    @abstractmethod
    def get_extractor_info(self) -> ExtractorInfo:
        """
        Get information about this extractor.
        
        Returns:
            ExtractorInfo containing extractor details
        """
        pass
    
    async def get_quality_options(self, url: str) -> List[QualityOption]:
        """
        Get available quality options for the given URL.
        
        Args:
            url: The URL to get quality options for
            
        Returns:
            List of available quality options
        """
        info = await self.extract_info(url)
        return self._parse_quality_options(info)
    
    def _parse_quality_options(self, info: Dict[str, Any]) -> List[QualityOption]:
        """
        Parse quality options from extracted information.
        Override this method in subclasses for platform-specific parsing.
        
        Args:
            info: Information dictionary from extract_info()
            
        Returns:
            List of QualityOption objects
        """
        # Default implementation - should be overridden by subclasses
        return []
    
    def _extract_domain(self, url: str) -> str:
        """
        Extract domain from URL.
        
        Args:
            url: The URL to extract domain from
            
        Returns:
            Domain name
        """
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.lower()
    
    def _is_supported_domain(self, url: str) -> bool:
        """
        Check if the URL's domain is in the supported domains list.
        
        Args:
            url: The URL to check
            
        Returns:
            True if domain is supported, False otherwise
        """
        domain = self._extract_domain(url)
        return any(supported in domain for supported in self.supported_domains)
    
    @property
    def info(self) -> ExtractorInfo:
        """Get extractor information"""
        return self._info
    
    @property
    def name(self) -> str:
        """Get extractor name"""
        return self._info.name
    
    @property
    def version(self) -> str:
        """Get extractor version"""
        return self._info.version