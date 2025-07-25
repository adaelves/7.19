"""
Rate limiting implementation using token bucket algorithm.
"""
import asyncio
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter for controlling download speeds.
    
    The token bucket algorithm allows for burst traffic while maintaining
    an average rate limit over time.
    """
    
    def __init__(self, rate: float, capacity: Optional[float] = None):
        """
        Initialize token bucket rate limiter.
        
        Args:
            rate: Rate in bytes per second
            capacity: Bucket capacity in bytes (defaults to 2x rate for 1 second burst)
        """
        self.rate = rate  # bytes per second
        self.capacity = capacity or (rate * 2)  # allow 2 second burst by default
        self.tokens = self.capacity  # start with full bucket
        self.last_update = time.time()
        self._lock = asyncio.Lock()
        
        logger.info(f"Rate limiter initialized: {rate} bytes/s, capacity: {self.capacity} bytes")
    
    async def acquire(self, bytes_requested: int) -> None:
        """
        Acquire tokens for the requested number of bytes.
        This method will block until enough tokens are available.
        
        Args:
            bytes_requested: Number of bytes to acquire tokens for
        """
        if bytes_requested <= 0:
            return
        
        async with self._lock:
            await self._wait_for_tokens(bytes_requested)
            self.tokens -= bytes_requested
    
    async def _wait_for_tokens(self, bytes_requested: int) -> None:
        """Wait until enough tokens are available"""
        while True:
            # Refill tokens based on elapsed time
            now = time.time()
            elapsed = now - self.last_update
            self.last_update = now
            
            # Add tokens based on rate and elapsed time
            tokens_to_add = elapsed * self.rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            
            # Check if we have enough tokens
            if self.tokens >= bytes_requested:
                break
            
            # Calculate how long to wait for enough tokens
            tokens_needed = bytes_requested - self.tokens
            wait_time = tokens_needed / self.rate
            
            # Wait for a short time and then check again
            # We use small increments to allow for cancellation
            sleep_time = min(wait_time, 0.1)  # Max 100ms sleep
            await asyncio.sleep(sleep_time)
    
    def set_rate(self, new_rate: float) -> None:
        """
        Update the rate limit.
        
        Args:
            new_rate: New rate in bytes per second
        """
        self.rate = new_rate
        self.capacity = new_rate * 2  # Update capacity proportionally
        logger.info(f"Rate limit updated to {new_rate} bytes/s")
    
    def get_current_tokens(self) -> float:
        """Get current number of tokens in bucket"""
        # Update tokens first
        now = time.time()
        elapsed = now - self.last_update
        tokens_to_add = elapsed * self.rate
        current_tokens = min(self.capacity, self.tokens + tokens_to_add)
        return current_tokens
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics"""
        return {
            'rate': self.rate,
            'capacity': self.capacity,
            'current_tokens': self.get_current_tokens(),
            'utilization': 1.0 - (self.get_current_tokens() / self.capacity)
        }


class AdaptiveRateLimiter(TokenBucketRateLimiter):
    """
    Adaptive rate limiter that can adjust its rate based on network conditions.
    """
    
    def __init__(self, initial_rate: float, min_rate: float = None, max_rate: float = None):
        """
        Initialize adaptive rate limiter.
        
        Args:
            initial_rate: Initial rate in bytes per second
            min_rate: Minimum allowed rate (defaults to initial_rate / 10)
            max_rate: Maximum allowed rate (defaults to initial_rate * 10)
        """
        super().__init__(initial_rate)
        self.initial_rate = initial_rate
        self.min_rate = min_rate or (initial_rate / 10)
        self.max_rate = max_rate or (initial_rate * 10)
        
        # Adaptation parameters
        self.adaptation_factor = 1.1  # Factor to increase/decrease rate
        self.success_threshold = 10  # Successful transfers before increasing rate
        self.failure_threshold = 3   # Failed transfers before decreasing rate
        
        # Statistics
        self.successful_transfers = 0
        self.failed_transfers = 0
        self.consecutive_successes = 0
        self.consecutive_failures = 0
        
        logger.info(f"Adaptive rate limiter initialized: {initial_rate} bytes/s "
                   f"(min: {self.min_rate}, max: {self.max_rate})")
    
    def record_success(self) -> None:
        """Record a successful transfer"""
        self.successful_transfers += 1
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        
        # Increase rate if we have enough consecutive successes
        if self.consecutive_successes >= self.success_threshold:
            self._increase_rate()
            self.consecutive_successes = 0
    
    def record_failure(self) -> None:
        """Record a failed transfer"""
        self.failed_transfers += 1
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        
        # Decrease rate if we have too many consecutive failures
        if self.consecutive_failures >= self.failure_threshold:
            self._decrease_rate()
            self.consecutive_failures = 0
    
    def _increase_rate(self) -> None:
        """Increase the rate limit"""
        new_rate = min(self.max_rate, self.rate * self.adaptation_factor)
        if new_rate != self.rate:
            logger.info(f"Increasing rate limit from {self.rate} to {new_rate} bytes/s")
            self.set_rate(new_rate)
    
    def _decrease_rate(self) -> None:
        """Decrease the rate limit"""
        new_rate = max(self.min_rate, self.rate / self.adaptation_factor)
        if new_rate != self.rate:
            logger.info(f"Decreasing rate limit from {self.rate} to {new_rate} bytes/s")
            self.set_rate(new_rate)
    
    def reset_adaptation(self) -> None:
        """Reset adaptation statistics"""
        self.successful_transfers = 0
        self.failed_transfers = 0
        self.consecutive_successes = 0
        self.consecutive_failures = 0
        self.set_rate(self.initial_rate)
        logger.info("Rate limiter adaptation reset")
    
    def get_adaptation_stats(self) -> dict:
        """Get adaptation statistics"""
        stats = self.get_stats()
        stats.update({
            'initial_rate': self.initial_rate,
            'min_rate': self.min_rate,
            'max_rate': self.max_rate,
            'successful_transfers': self.successful_transfers,
            'failed_transfers': self.failed_transfers,
            'consecutive_successes': self.consecutive_successes,
            'consecutive_failures': self.consecutive_failures,
            'success_rate': (
                self.successful_transfers / (self.successful_transfers + self.failed_transfers)
                if (self.successful_transfers + self.failed_transfers) > 0 else 0
            )
        })
        return stats


class BandwidthMonitor:
    """
    Monitor bandwidth usage and provide statistics.
    """
    
    def __init__(self, window_size: int = 60):
        """
        Initialize bandwidth monitor.
        
        Args:
            window_size: Size of the monitoring window in seconds
        """
        self.window_size = window_size
        self.data_points = []  # List of (timestamp, bytes) tuples
        self._lock = asyncio.Lock()
    
    async def record_transfer(self, bytes_transferred: int) -> None:
        """Record a data transfer"""
        async with self._lock:
            now = time.time()
            self.data_points.append((now, bytes_transferred))
            
            # Remove old data points outside the window
            cutoff_time = now - self.window_size
            self.data_points = [(t, b) for t, b in self.data_points if t >= cutoff_time]
    
    async def get_current_bandwidth(self) -> float:
        """Get current bandwidth in bytes per second"""
        async with self._lock:
            if len(self.data_points) < 2:
                return 0.0
            
            now = time.time()
            cutoff_time = now - self.window_size
            
            # Filter data points within the window
            recent_points = [(t, b) for t, b in self.data_points if t >= cutoff_time]
            
            if len(recent_points) < 2:
                return 0.0
            
            # Calculate total bytes and time span
            total_bytes = sum(b for t, b in recent_points)
            time_span = recent_points[-1][0] - recent_points[0][0]
            
            if time_span > 0:
                return total_bytes / time_span
            else:
                return 0.0
    
    async def get_peak_bandwidth(self) -> float:
        """Get peak bandwidth in the current window"""
        async with self._lock:
            if len(self.data_points) < 2:
                return 0.0
            
            # Calculate bandwidth for each second
            bandwidths = []
            for i in range(len(self.data_points) - 1):
                time_diff = self.data_points[i + 1][0] - self.data_points[i][0]
                if time_diff > 0:
                    bandwidth = self.data_points[i + 1][1] / time_diff
                    bandwidths.append(bandwidth)
            
            return max(bandwidths) if bandwidths else 0.0
    
    async def get_average_bandwidth(self) -> float:
        """Get average bandwidth in the current window"""
        return await self.get_current_bandwidth()
    
    async def get_stats(self) -> dict:
        """Get bandwidth statistics"""
        current = await self.get_current_bandwidth()
        peak = await self.get_peak_bandwidth()
        average = await self.get_average_bandwidth()
        
        return {
            'current_bandwidth': current,
            'peak_bandwidth': peak,
            'average_bandwidth': average,
            'window_size': self.window_size,
            'data_points': len(self.data_points)
        }