#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-05-01 12:00:00

"""
Memory optimizer for PySpider
"""

import gc
import time
import logging
import threading
from typing import Dict, Any, Optional, List, Tuple, Union, Callable

logger = logging.getLogger('memory_optimizer')

class MemoryOptimizer:
    """
    Memory optimizer for PySpider
    
    This class monitors memory usage and performs optimization when needed.
    """
    
    def __init__(self, 
                 max_memory_percent: float = 80.0, 
                 gc_interval: int = 60,
                 check_interval: int = 30,
                 auto_optimize: bool = True):
        """
        Initialize MemoryOptimizer
        
        Args:
            max_memory_percent: Maximum memory usage percentage before optimization
            gc_interval: Minimum interval between garbage collections in seconds
            check_interval: Interval between memory checks in seconds
            auto_optimize: Whether to automatically optimize memory usage
        """
        self.max_memory_percent = max_memory_percent
        self.gc_interval = gc_interval
        self.check_interval = check_interval
        self.auto_optimize = auto_optimize
        
        self.last_gc_time = 0
        self._stop_event = threading.Event()
        self._monitor_thread = None
        
        # Initialize metrics
        from pyspider.libs.metrics import metrics
        self.metrics = metrics
        
        # Set initial memory usage
        self.update_memory_metrics()
        
        logger.info(f"Memory optimizer initialized with max_memory_percent={max_memory_percent}%, "
                   f"gc_interval={gc_interval}s, check_interval={check_interval}s, "
                   f"auto_optimize={auto_optimize}")
    
    def start(self):
        """
        Start memory monitoring
        """
        if self.auto_optimize and self._monitor_thread is None:
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()
            logger.info("Memory monitoring started")
    
    def stop(self):
        """
        Stop memory monitoring
        """
        if self._monitor_thread is not None:
            self._stop_event.set()
            self._monitor_thread.join(timeout=5)
            self._monitor_thread = None
            logger.info("Memory monitoring stopped")
    
    def _monitor_loop(self):
        """
        Memory monitoring loop
        """
        while not self._stop_event.is_set():
            try:
                self.check_memory()
            except Exception as e:
                logger.error(f"Error in memory monitoring: {e}")
            
            # Wait for next check
            self._stop_event.wait(self.check_interval)
    
    def check_memory(self) -> Dict[str, Any]:
        """
        Check memory usage and optimize if needed
        
        Returns:
            Memory usage information
        """
        try:
            import psutil
            process = psutil.Process()
            
            # Get memory usage
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            # Update metrics
            self.update_memory_metrics(memory_info, memory_percent)
            
            # Check if optimization is needed
            if memory_percent > self.max_memory_percent:
                current_time = time.time()
                if current_time - self.last_gc_time >= self.gc_interval:
                    self.optimize_memory()
            
            return {
                'rss': memory_info.rss,
                'vms': memory_info.vms,
                'percent': memory_percent,
                'optimized': False
            }
        except ImportError:
            logger.warning("psutil module not available, memory monitoring disabled")
            return {
                'rss': 0,
                'vms': 0,
                'percent': 0,
                'optimized': False
            }
    
    def optimize_memory(self) -> Dict[str, Any]:
        """
        Optimize memory usage
        
        Returns:
            Optimization results
        """
        try:
            import psutil
            process = psutil.Process()
            
            # Get memory usage before optimization
            before_memory_info = process.memory_info()
            before_memory_percent = process.memory_percent()
            
            # Perform garbage collection
            logger.info(f"Memory usage is high ({before_memory_percent:.1f}%), performing garbage collection")
            collected = gc.collect(generation=2)
            
            # Update last GC time
            self.last_gc_time = time.time()
            
            # Get memory usage after optimization
            after_memory_info = process.memory_info()
            after_memory_percent = process.memory_percent()
            
            # Calculate memory saved
            rss_saved = before_memory_info.rss - after_memory_info.rss
            percent_saved = before_memory_percent - after_memory_percent
            
            # Update metrics
            self.update_memory_metrics(after_memory_info, after_memory_percent)
            self.metrics.increment('memory_optimizations')
            self.metrics.gauge('memory_optimization_objects_collected', collected)
            self.metrics.gauge('memory_optimization_bytes_saved', rss_saved)
            
            logger.info(f"Garbage collection completed: {collected} objects collected, "
                       f"{rss_saved / (1024 * 1024):.2f} MB saved, "
                       f"memory usage: {after_memory_percent:.1f}%")
            
            return {
                'before': {
                    'rss': before_memory_info.rss,
                    'vms': before_memory_info.vms,
                    'percent': before_memory_percent
                },
                'after': {
                    'rss': after_memory_info.rss,
                    'vms': after_memory_info.vms,
                    'percent': after_memory_percent
                },
                'saved': {
                    'rss': rss_saved,
                    'percent': percent_saved
                },
                'collected': collected,
                'optimized': True
            }
        except ImportError:
            logger.warning("psutil module not available, memory optimization disabled")
            
            # Perform garbage collection anyway
            collected = gc.collect(generation=2)
            self.last_gc_time = time.time()
            
            logger.info(f"Garbage collection completed: {collected} objects collected")
            
            return {
                'collected': collected,
                'optimized': True
            }
    
    def update_memory_metrics(self, memory_info=None, memory_percent=None):
        """
        Update memory metrics
        
        Args:
            memory_info: Memory information from psutil
            memory_percent: Memory usage percentage from psutil
        """
        try:
            import psutil
            
            if memory_info is None or memory_percent is None:
                process = psutil.Process()
                memory_info = process.memory_info()
                memory_percent = process.memory_percent()
            
            # Update metrics
            self.metrics.gauge('memory_usage_rss', memory_info.rss)
            self.metrics.gauge('memory_usage_vms', memory_info.vms)
            self.metrics.gauge('memory_usage_percent', memory_percent)
            
            # System memory
            system_memory = psutil.virtual_memory()
            self.metrics.gauge('system_memory_total', system_memory.total)
            self.metrics.gauge('system_memory_available', system_memory.available)
            self.metrics.gauge('system_memory_percent', system_memory.percent)
        except ImportError:
            pass  # psutil not available
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get current memory usage
        
        Returns:
            Memory usage information
        """
        try:
            import psutil
            process = psutil.Process()
            
            # Get memory usage
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            # System memory
            system_memory = psutil.virtual_memory()
            
            return {
                'process': {
                    'rss': memory_info.rss,
                    'vms': memory_info.vms,
                    'percent': memory_percent
                },
                'system': {
                    'total': system_memory.total,
                    'available': system_memory.available,
                    'percent': system_memory.percent
                }
            }
        except ImportError:
            logger.warning("psutil module not available, memory usage information disabled")
            return {
                'process': {
                    'rss': 0,
                    'vms': 0,
                    'percent': 0
                },
                'system': {
                    'total': 0,
                    'available': 0,
                    'percent': 0
                }
            }


# Global memory optimizer instance
memory_optimizer = MemoryOptimizer()
