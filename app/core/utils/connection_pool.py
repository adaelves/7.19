"""
Network connection pool management for improved performance
"""
import asyncio
import aiohttp
import threading
import time
from typing import Dict, Optional, List, Any
from urllib.parse import urlparse
from dataclasses import dataclass
from contextlib import asynccontextmanager
import ssl
import certifi


@dataclass
class ConnectionConfig:
    """Configuration for connection pool"""
    max_connections: int = 100
    max_connections_per_host: int = 30
    connection_timeout: float = 30.0
    read_timeout: float = 300.0
    keepalive_timeout: float = 30.0
    enable_cleanup_closed: bool = True
    ttl_dns_cache: int = 300
    use_dns_cache: bool = True


@dataclass
class ConnectionStats:
    """Connection pool statistics"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    requests_count: int = 0
    errors_count: int = 0
    timeouts_count: int = 0
    created_at: float = 0.0
    
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()


class ConnectionPoolManager:
    """Manages HTTP connection pools for different hosts"""
    
    def __init__(self, config: Optional[ConnectionConfig] = None):
        self.config = config or ConnectionConfig()
        self.sessions: Dict[str, aiohttp.ClientSession] = {}
        self.stats: Dict[str, ConnectionStats] = {}
        self.lock = threading.Lock()
        self._cleanup_task = None
        self._running = False
    
    async def start(self):
        """Start the connection pool manager"""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Stop the connection pool manager and close all connections"""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Close all sessions
        for session in self.sessions.values():
            await session.close()
        
        self.sessions.clear()
        self.stats.clear()
    
    def _get_host_key(self, url: str) -> str:
        """Extract host key from URL"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def _create_session(self, host_key: str) -> aiohttp.ClientSession:
        """Create a new HTTP session for a host"""
        # SSL context
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        # Connection timeout
        timeout = aiohttp.ClientTimeout(
            total=self.config.connection_timeout,
            connect=self.config.connection_timeout,
            sock_read=self.config.read_timeout
        )
        
        # Connector configuration
        connector = aiohttp.TCPConnector(
            limit=self.config.max_connections,
            limit_per_host=self.config.max_connections_per_host,
            keepalive_timeout=self.config.keepalive_timeout,
            enable_cleanup_closed=self.config.enable_cleanup_closed,
            ttl_dns_cache=self.config.ttl_dns_cache,
            use_dns_cache=self.config.use_dns_cache,
            ssl=ssl_context
        )
        
        # Create session
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        return session
    
    def get_session(self, url: str) -> aiohttp.ClientSession:
        """Get or create a session for the given URL"""
        host_key = self._get_host_key(url)
        
        with self.lock:
            if host_key not in self.sessions:
                self.sessions[host_key] = self._create_session(host_key)
                self.stats[host_key] = ConnectionStats()
            
            return self.sessions[host_key]
    
    @asynccontextmanager
    async def request(self, method: str, url: str, **kwargs):
        """Make an HTTP request using the connection pool"""
        host_key = self._get_host_key(url)
        session = self.get_session(url)
        
        # Update stats
        with self.lock:
            if host_key in self.stats:
                self.stats[host_key].requests_count += 1
        
        try:
            async with session.request(method, url, **kwargs) as response:
                yield response
        except asyncio.TimeoutError:
            with self.lock:
                if host_key in self.stats:
                    self.stats[host_key].timeouts_count += 1
            raise
        except Exception:
            with self.lock:
                if host_key in self.stats:
                    self.stats[host_key].errors_count += 1
            raise
    
    async def get(self, url: str, **kwargs):
        """Make a GET request"""
        async with self.request('GET', url, **kwargs) as response:
            return response
    
    async def post(self, url: str, **kwargs):
        """Make a POST request"""
        async with self.request('POST', url, **kwargs) as response:
            return response
    
    async def head(self, url: str, **kwargs):
        """Make a HEAD request"""
        async with self.request('HEAD', url, **kwargs) as response:
            return response
    
    def get_connection_stats(self, host: Optional[str] = None) -> Dict[str, Any]:
        """Get connection statistics"""
        with self.lock:
            if host:
                host_key = self._get_host_key(host) if '://' in host else host
                if host_key in self.stats:
                    stats = self.stats[host_key]
                    session = self.sessions.get(host_key)
                    
                    result = {
                        'requests_count': stats.requests_count,
                        'errors_count': stats.errors_count,
                        'timeouts_count': stats.timeouts_count,
                        'error_rate': stats.errors_count / max(1, stats.requests_count),
                        'timeout_rate': stats.timeouts_count / max(1, stats.requests_count),
                        'uptime': time.time() - stats.created_at
                    }
                    
                    if session and hasattr(session.connector, '_conns'):
                        result.update({
                            'active_connections': len(session.connector._conns),
                            'total_connections': session.connector.limit,
                            'connections_per_host': session.connector.limit_per_host
                        })
                    
                    return result
                else:
                    return {}
            else:
                # Return stats for all hosts
                all_stats = {}
                for host_key, stats in self.stats.items():
                    session = self.sessions.get(host_key)
                    
                    host_stats = {
                        'requests_count': stats.requests_count,
                        'errors_count': stats.errors_count,
                        'timeouts_count': stats.timeouts_count,
                        'error_rate': stats.errors_count / max(1, stats.requests_count),
                        'timeout_rate': stats.timeouts_count / max(1, stats.requests_count),
                        'uptime': time.time() - stats.created_at
                    }
                    
                    if session and hasattr(session.connector, '_conns'):
                        host_stats.update({
                            'active_connections': len(session.connector._conns),
                            'total_connections': session.connector.limit,
                            'connections_per_host': session.connector.limit_per_host
                        })
                    
                    all_stats[host_key] = host_stats
                
                return all_stats
    
    async def cleanup_idle_connections(self):
        """Clean up idle connections"""
        cleaned_count = 0
        
        for host_key, session in list(self.sessions.items()):
            if hasattr(session.connector, '_cleanup_closed_disabled'):
                # Force cleanup of closed connections
                await session.connector._cleanup_closed()
                cleaned_count += 1
        
        return cleaned_count
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while self._running:
            try:
                await asyncio.sleep(60)  # Run cleanup every minute
                await self.cleanup_idle_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue
                print(f"Connection pool cleanup error: {e}")
    
    def reset_stats(self, host: Optional[str] = None):
        """Reset statistics"""
        with self.lock:
            if host:
                host_key = self._get_host_key(host) if '://' in host else host
                if host_key in self.stats:
                    self.stats[host_key] = ConnectionStats()
            else:
                for host_key in self.stats:
                    self.stats[host_key] = ConnectionStats()


class GlobalConnectionManager:
    """Global connection manager singleton"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not getattr(self, '_initialized', False):
            self.pool_manager = None
            self._initialized = True
    
    async def initialize(self, config: Optional[ConnectionConfig] = None):
        """Initialize the global connection manager"""
        if self.pool_manager is None:
            self.pool_manager = ConnectionPoolManager(config)
            await self.pool_manager.start()
    
    async def shutdown(self):
        """Shutdown the global connection manager"""
        if self.pool_manager:
            await self.pool_manager.stop()
            self.pool_manager = None
    
    def get_manager(self) -> Optional[ConnectionPoolManager]:
        """Get the connection pool manager"""
        return self.pool_manager


# Global connection manager instance
global_connection_manager = GlobalConnectionManager()