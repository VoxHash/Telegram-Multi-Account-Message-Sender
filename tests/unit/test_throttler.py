"""
Unit tests for throttler functionality.
"""

import pytest
import asyncio
from app.core.throttler import Throttler, RateLimiter


class TestRateLimiter:
    """Test rate limiter functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test basic rate limiting."""
        limiter = RateLimiter(max_requests=2, time_window=1)
        
        # First two requests should succeed
        assert await limiter.acquire() is True
        assert await limiter.acquire() is True
        
        # Third request should fail
        assert await limiter.acquire() is False
    
    @pytest.mark.asyncio
    async def test_rate_limiting_reset(self):
        """Test rate limiting resets after time window."""
        limiter = RateLimiter(max_requests=1, time_window=0.1)
        
        # First request should succeed
        assert await limiter.acquire() is True
        
        # Second request should fail
        assert await limiter.acquire() is False
        
        # Wait for time window to reset
        await asyncio.sleep(0.2)
        
        # Request should succeed again
        assert await limiter.acquire() is True
    
    def test_wait_time(self):
        """Test wait time calculation."""
        limiter = RateLimiter(max_requests=1, time_window=1)
        
        # No requests made yet
        assert limiter.get_wait_time() == 0.0
        
        # Make a request
        asyncio.run(limiter.acquire())
        
        # Should have wait time
        assert limiter.get_wait_time() > 0.0
    
    def test_current_rate(self):
        """Test current rate calculation."""
        limiter = RateLimiter(max_requests=10, time_window=1)
        
        # No requests made yet
        assert limiter.get_current_rate() == 0.0


class TestThrottler:
    """Test throttler functionality."""
    
    def test_set_account_limits(self):
        """Test setting account limits."""
        throttler = Throttler()
        throttler.set_account_limits(1, 10, 100, 1000)
        
        assert 1 in throttler.account_limiters
        assert 1 in throttler.semaphores
    
    def test_set_global_limits(self):
        """Test setting global limits."""
        throttler = Throttler()
        throttler.set_global_limits(50, 5)
        
        assert throttler.global_limiter is not None
        assert hasattr(throttler, 'global_semaphore')
    
    @pytest.mark.asyncio
    async def test_acquire_account_token(self):
        """Test acquiring account token."""
        throttler = Throttler()
        throttler.set_account_limits(1, 2, 20, 200)
        
        # Should succeed
        assert await throttler.acquire_account_token(1) is True
        
        # Should succeed again
        assert await throttler.acquire_account_token(1) is True
        
        # Should fail (rate limited)
        assert await throttler.acquire_account_token(1) is False
    
    @pytest.mark.asyncio
    async def test_acquire_global_token(self):
        """Test acquiring global token."""
        throttler = Throttler()
        throttler.set_global_limits(2, 5)
        
        # Should succeed
        assert await throttler.acquire_global_token() is True
        assert await throttler.acquire_global_token() is True
        
        # Should fail (rate limited)
        assert await throttler.acquire_global_token() is False
    
    @pytest.mark.asyncio
    async def test_acquire_semaphore(self):
        """Test acquiring semaphore."""
        throttler = Throttler()
        throttler.set_account_limits(1, 10, 100, 1000)
        
        # Should succeed
        assert await throttler.acquire_semaphore(1) is True
        
        # Release and acquire again
        throttler.release_semaphore(1)
        assert await throttler.acquire_semaphore(1) is True
    
    def test_get_account_stats(self):
        """Test getting account statistics."""
        throttler = Throttler()
        throttler.set_account_limits(1, 10, 100, 1000)
        
        stats = throttler.get_account_stats(1)
        
        assert "current_rate" in stats
        assert "wait_time" in stats
        assert "last_activity" in stats
        assert "semaphore_available" in stats
    
    def test_get_global_stats(self):
        """Test getting global statistics."""
        throttler = Throttler()
        throttler.set_global_limits(50, 5)
        
        stats = throttler.get_global_stats()
        
        assert "current_rate" in stats
        assert "wait_time" in stats
        assert "global_semaphore_available" in stats
    
    def test_reset_account_limits(self):
        """Test resetting account limits."""
        throttler = Throttler()
        throttler.set_account_limits(1, 10, 100, 1000)
        
        # Reset
        throttler.reset_account_limits(1)
        
        # Should be removed
        assert 1 not in throttler.account_limiters
        assert 1 not in throttler.semaphores
        assert 1 not in throttler.last_activity
    
    def test_reset_all_limits(self):
        """Test resetting all limits."""
        throttler = Throttler()
        throttler.set_account_limits(1, 10, 100, 1000)
        throttler.set_global_limits(50, 5)
        
        # Reset all
        throttler.reset_all_limits()
        
        # Should be empty
        assert len(throttler.account_limiters) == 0
        assert len(throttler.semaphores) == 0
        assert len(throttler.last_activity) == 0
        assert throttler.global_limiter is None
        assert not hasattr(throttler, 'global_semaphore')
