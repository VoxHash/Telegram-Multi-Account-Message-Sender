"""
Performance monitoring and optimization utilities.
"""

import time
import functools
import tracemalloc
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict
from contextlib import contextmanager

from . import get_logger


class PerformanceMonitor:
    """Monitors application performance metrics."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.logger = get_logger()
        self.metrics: Dict[str, List[float]] = defaultdict(list)
        self.memory_snapshots: List[Dict[str, Any]] = []
        self.query_times: List[Dict[str, Any]] = []
        self.tracemalloc_started = False
        
        # Start memory tracking
        try:
            tracemalloc.start()
            self.tracemalloc_started = True
        except RuntimeError:
            # Already started
            pass
    
    def record_metric(self, name: str, value: float) -> None:
        """Record a performance metric."""
        self.metrics[name].append(value)
        # Keep only last 1000 measurements
        if len(self.metrics[name]) > 1000:
            self.metrics[name] = self.metrics[name][-1000:]
    
    def get_metric_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a metric."""
        if name not in self.metrics or not self.metrics[name]:
            return {}
        
        values = self.metrics[name]
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "median": sorted(values)[len(values) // 2] if values else 0,
        }
    
    @contextmanager
    def measure_time(self, operation_name: str):
        """Context manager to measure operation time."""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start_time
            self.record_metric(f"{operation_name}_time", elapsed)
            self.logger.debug(f"{operation_name} took {elapsed:.3f}s")
    
    @contextmanager
    def measure_memory(self, operation_name: str):
        """Context manager to measure memory usage."""
        if not self.tracemalloc_started:
            try:
                tracemalloc.start()
                self.tracemalloc_started = True
            except RuntimeError:
                pass
        
        snapshot_before = None
        snapshot_after = None
        
        if self.tracemalloc_started:
            snapshot_before = tracemalloc.take_snapshot()
        
        try:
            yield
        finally:
            if self.tracemalloc_started:
                snapshot_after = tracemalloc.take_snapshot()
                
                if snapshot_before and snapshot_after:
                    top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
                    total_diff = sum(stat.size_diff for stat in top_stats)
                    
                    self.memory_snapshots.append({
                        "operation": operation_name,
                        "timestamp": datetime.utcnow(),
                        "memory_diff_bytes": total_diff,
                        "memory_diff_mb": total_diff / (1024 * 1024),
                    })
                    
                    self.logger.debug(f"{operation_name} memory delta: {total_diff / (1024 * 1024):.2f} MB")
    
    def record_query_time(self, query_name: str, duration: float, row_count: int = 0) -> None:
        """Record database query performance."""
        self.query_times.append({
            "query": query_name,
            "duration": duration,
            "row_count": row_count,
            "timestamp": datetime.utcnow(),
        })
        
        # Keep only last 1000 queries
        if len(self.query_times) > 1000:
            self.query_times = self.query_times[-1000:]
    
    def get_slow_queries(self, threshold_seconds: float = 1.0) -> List[Dict[str, Any]]:
        """Get queries that took longer than threshold."""
        return [
            q for q in self.query_times
            if q["duration"] > threshold_seconds
        ]
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {},
            "slow_queries": self.get_slow_queries(),
            "memory_snapshots": self.memory_snapshots[-100:] if self.memory_snapshots else [],
        }
        
        # Calculate stats for all metrics
        for metric_name in self.metrics:
            report["metrics"][metric_name] = self.get_metric_stats(metric_name)
        
        # Query statistics
        if self.query_times:
            query_durations = [q["duration"] for q in self.query_times]
            report["query_stats"] = {
                "total_queries": len(self.query_times),
                "avg_duration": sum(query_durations) / len(query_durations),
                "max_duration": max(query_durations),
                "min_duration": min(query_durations),
            }
        
        return report
    
    def reset(self) -> None:
        """Reset all performance metrics."""
        self.metrics.clear()
        self.memory_snapshots.clear()
        self.query_times.clear()
        self.logger.info("Performance metrics reset")


def performance_timer(operation_name: Optional[str] = None):
    """Decorator to measure function execution time."""
    def decorator(func: Callable) -> Callable:
        name = operation_name or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            with monitor.measure_time(name):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

