#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-05-01 12:00:00

"""
Connection pool optimizer for PySpider
"""

import time
import asyncio
import logging
import threading
from typing import Dict, Any, Optional, List, Tuple, Union, Callable

logger = logging.getLogger('connection_pool_optimizer')

class ConnectionPoolOptimizer:
    """
    Connection pool optimizer for PySpider
    
    This class optimizes connection pool size based on workload.
    """
    
    def __init__(self, 
                 min_pool_size: int = 10,
                 max_pool_size: int = 200,
                 initial_pool_size: int = 50,
                 check_interval: int = 30,
                 scale_factor: float = 1.5,
                 scale_down_threshold: float = 0.3,
                 auto_optimize: bool = True):
        """
        Initialize ConnectionPoolOptimizer
        
        Args:
            min_pool_size: Minimum connection pool size
            max_pool_size: Maximum connection pool size
            initial_pool_size: Initial connection pool size
            check_interval: Interval between pool size checks in seconds
            scale_factor: Factor to scale up pool size based on queue size
            scale_down_threshold: Threshold to scale down pool size
            auto_optimize: Whether to automatically optimize pool size
        """
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self.current_pool_size = initial_pool_size
        self.check_interval = check_interval
        self.scale_factor = scale_factor
        self.scale_down_threshold = scale_down_threshold
        self.auto_optimize = auto_optimize
        
        self._stop_event = threading.Event()
        self._monitor_thread = None
        self._active_connections = 0
        self._queue_size = 0
        self._lock = threading.RLock()
        
        # Initialize metrics
        from pyspider.libs.metrics import metrics
        self.metrics = metrics
        
        # Set initial metrics
        self.update_pool_metrics()
        
        logger.info(f"Connection pool optimizer initialized with min_pool_size={min_pool_size}, "
                   f"max_pool_size={max_pool_size}, initial_pool_size={initial_pool_size}, "
                   f"check_interval={check_interval}s, scale_factor={scale_factor}, "
                   f"scale_down_threshold={scale_down_threshold}, auto_optimize={auto_optimize}")
    
    def start(self):
        """
        Start pool size monitoring
        """
        if self.auto_optimize and self._monitor_thread is None:
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()
            logger.info("Connection pool monitoring started")
    
    def stop(self):
        """
        Stop pool size monitoring
        """
        if self._monitor_thread is not None:
            self._stop_event.set()
            self._monitor_thread.join(timeout=5)
            self._monitor_thread = None
            logger.info("Connection pool monitoring stopped")
    
    def _monitor_loop(self):
        """
        Pool size monitoring loop
        """
        while not self._stop_event.is_set():
            try:
                self.optimize_pool_size()
            except Exception as e:
                logger.error(f"Error in pool size monitoring: {e}")
            
            # Wait for next check
            self._stop_event.wait(self.check_interval)
    
    def set_active_connections(self, count: int):
        """
        Set number of active connections
        
        Args:
            count: Number of active connections
        """
        with self._lock:
            self._active_connections = count
            self.update_pool_metrics()
    
    def set_queue_size(self, size: int):
        """
        Set queue size
        
        Args:
            size: Queue size
        """
        with self._lock:
            self._queue_size = size
            self.update_pool_metrics()
    
    def optimize_pool_size(self) -> Dict[str, Any]:
        """
        Optimize connection pool size based on workload
        
        Returns:
            Optimization results
        """
        with self._lock:
            # Get current state
            active_connections = self._active_connections
            queue_size = self._queue_size
            current_pool_size = self.current_pool_size
            
            # Calculate optimal pool size
            optimal_pool_size = min(
                max(self.min_pool_size, int(queue_size * self.scale_factor)),
                self.max_pool_size
            )
            
            # Check if pool size needs to be adjusted
            if optimal_pool_size > current_pool_size:
                # Scale up
                new_pool_size = optimal_pool_size
                action = "increased"
            elif optimal_pool_size < current_pool_size * self.scale_down_threshold and current_pool_size > self.min_pool_size:
                # Scale down
                new_pool_size = max(self.min_pool_size, optimal_pool_size)
                action = "decreased"
            else:
                # No change needed
                new_pool_size = current_pool_size
                action = "unchanged"
            
            # Update pool size if changed
            if new_pool_size != current_pool_size:
                logger.info(f"Connection pool size {action} from {current_pool_size} to {new_pool_size} "
                           f"(active: {active_connections}, queue: {queue_size})")
                self.current_pool_size = new_pool_size
                self.update_pool_metrics()
                self.metrics.increment(f'connection_pool_{action}')
            
            return {
                'before': current_pool_size,
                'after': new_pool_size,
                'active_connections': active_connections,
                'queue_size': queue_size,
                'optimal_pool_size': optimal_pool_size,
                'action': action
            }
    
    def update_pool_metrics(self):
        """
        Update pool metrics
        """
        self.metrics.gauge('connection_pool_size', self.current_pool_size)
        self.metrics.gauge('connection_pool_active', self._active_connections)
        self.metrics.gauge('connection_pool_queue', self._queue_size)
        
        # Calculate utilization
        if self.current_pool_size > 0:
            utilization = self._active_connections / self.current_pool_size
            self.metrics.gauge('connection_pool_utilization', utilization)
    
    def get_pool_size(self) -> int:
        """
        Get current pool size
        
        Returns:
            Current pool size
        """
        return self.current_pool_size
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """
        Get pool statistics
        
        Returns:
            Pool statistics
        """
        with self._lock:
            return {
                'pool_size': self.current_pool_size,
                'min_pool_size': self.min_pool_size,
                'max_pool_size': self.max_pool_size,
                'active_connections': self._active_connections,
                'queue_size': self._queue_size,
                'utilization': self._active_connections / self.current_pool_size if self.current_pool_size > 0 else 0
            }


# Global connection pool optimizer instance
connection_pool_optimizer = ConnectionPoolOptimizer()
