"""
Rate limiting and throttling for message sending.
"""

import asyncio
import time
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, deque


@dataclass
class RateLimit:
    """Rate limit configuration."""
    max_requests: int
    time_window: int  # in seconds
    current_requests: int = 0
    window_start: float = 0.0


class RateLimiter:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, max_requests: int, time_window: int):
        """Initialize rate limiter."""
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    async def acquire(self) -> bool:
        """Acquire a token from the rate limiter."""
        now = time.time()
        
        # Remove old requests outside the time window
        while self.requests and self.requests[0] <= now - self.time_window:
            self.requests.popleft()
        
        # Check if we can make a new request
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        return False
    
    def get_wait_time(self) -> float:
        """Get time to wait before next request can be made."""
        if not self.requests:
            return 0.0
        
        oldest_request = self.requests[0]
        wait_time = (oldest_request + self.time_window) - time.time()
        return max(0.0, wait_time)
    
    def get_current_rate(self) -> float:
        """Get current requests per second."""
        now = time.time()
        recent_requests = sum(1 for req_time in self.requests if req_time > now - self.time_window)
        return recent_requests / self.time_window


class Throttler:
    """Multi-level throttler for managing message sending rates."""
    
    def __init__(self):
        """Initialize throttler."""
        self.account_limiters: Dict[int, RateLimiter] = {}
        self.global_limiter: Optional[RateLimiter] = None
        self.semaphores: Dict[int, asyncio.Semaphore] = {}
        self.last_activity: Dict[int, float] = {}
    
    def set_account_limits(self, account_id: int, per_minute: int, per_hour: int, per_day: int):
        """Set rate limits for an account."""
        # Use the most restrictive limit (per minute)
        self.account_limiters[account_id] = RateLimiter(per_minute, 60)
        
        # Set concurrency limit (max 3 concurrent sends per account)
        self.semaphores[account_id] = asyncio.Semaphore(3)
    
    def set_global_limits(self, per_minute: int, max_concurrency: int):
        """Set global rate limits."""
        self.global_limiter = RateLimiter(per_minute, 60)
        self.global_semaphore = asyncio.Semaphore(max_concurrency)
    
    async def acquire_account_token(self, account_id: int) -> bool:
        """Acquire a token for account-specific sending."""
        if account_id not in self.account_limiters:
            return True
        
        return await self.account_limiters[account_id].acquire()
    
    async def acquire_global_token(self) -> bool:
        """Acquire a global token."""
        if not self.global_limiter:
            return True
        
        return await self.global_limiter.acquire()
    
    async def acquire_semaphore(self, account_id: int) -> bool:
        """Acquire account semaphore for concurrency control."""
        if account_id not in self.semaphores:
            return True
        
        try:
            await asyncio.wait_for(self.semaphores[account_id].acquire(), timeout=1.0)
            return True
        except asyncio.TimeoutError:
            return False
    
    def release_semaphore(self, account_id: int):
        """Release account semaphore."""
        if account_id in self.semaphores:
            self.semaphores[account_id].release()
    
    async def acquire_global_semaphore(self) -> bool:
        """Acquire global semaphore."""
        if not hasattr(self, 'global_semaphore'):
            return True
        
        try:
            await asyncio.wait_for(self.global_semaphore.acquire(), timeout=1.0)
            return True
        except asyncio.TimeoutError:
            return False
    
    def release_global_semaphore(self):
        """Release global semaphore."""
        if hasattr(self, 'global_semaphore'):
            self.global_semaphore.release()
    
    def get_account_wait_time(self, account_id: int) -> float:
        """Get wait time for account."""
        if account_id not in self.account_limiters:
            return 0.0
        
        return self.account_limiters[account_id].get_wait_time()
    
    def get_global_wait_time(self) -> float:
        """Get global wait time."""
        if not self.global_limiter:
            return 0.0
        
        return self.global_limiter.get_wait_time()
    
    def get_account_rate(self, account_id: int) -> float:
        """Get current rate for account."""
        if account_id not in self.account_limiters:
            return 0.0
        
        return self.account_limiters[account_id].get_current_rate()
    
    def get_global_rate(self) -> float:
        """Get current global rate."""
        if not self.global_limiter:
            return 0.0
        
        return self.global_limiter.get_current_rate()
    
    def update_activity(self, account_id: int):
        """Update last activity time for account."""
        self.last_activity[account_id] = time.time()
    
    def get_account_stats(self, account_id: int) -> Dict[str, float]:
        """Get statistics for an account."""
        return {
            "current_rate": self.get_account_rate(account_id),
            "wait_time": self.get_account_wait_time(account_id),
            "last_activity": self.last_activity.get(account_id, 0),
            "semaphore_available": self.semaphores.get(account_id, asyncio.Semaphore(1))._value > 0
        }
    
    def get_global_stats(self) -> Dict[str, float]:
        """Get global statistics."""
        return {
            "current_rate": self.get_global_rate(),
            "wait_time": self.get_global_wait_time(),
            "global_semaphore_available": getattr(self, 'global_semaphore', asyncio.Semaphore(1))._value > 0
        }
    
    def reset_account_limits(self, account_id: int):
        """Reset limits for an account."""
        if account_id in self.account_limiters:
            del self.account_limiters[account_id]
        if account_id in self.semaphores:
            del self.semaphores[account_id]
        if account_id in self.last_activity:
            del self.last_activity[account_id]
    
    def reset_all_limits(self):
        """Reset all limits."""
        self.account_limiters.clear()
        self.semaphores.clear()
        self.last_activity.clear()
        self.global_limiter = None
        if hasattr(self, 'global_semaphore'):
            delattr(self, 'global_semaphore')
