#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-05-01 12:00:00

"""
Metrics collection for PySpider
"""

import time
import json
import logging
import threading
import contextlib
from typing import Dict, Any, List, Optional, Union, Callable

logger = logging.getLogger('metrics')

class Metrics:
    """
    Metrics collection for PySpider
    """
    
    def __init__(self):
        """
        Initialize Metrics
        """
        self._counters = {}
        self._gauges = {}
        self._timers = {}
        self._lock = threading.RLock()
        self._last_report_time = time.time()
        self._report_interval = 60  # Report every 60 seconds
    
    def increment(self, name: str, value: int = 1, tags: Dict[str, str] = None) -> int:
        """
        Increment a counter
        
        Args:
            name: Counter name
            value: Value to increment by
            tags: Tags for the counter
            
        Returns:
            New counter value
        """
        with self._lock:
            key = self._get_key(name, tags)
            if key not in self._counters:
                self._counters[key] = 0
            self._counters[key] += value
            
            # Check if it's time to report metrics
            self._check_report()
            
            return self._counters[key]
    
    def decrement(self, name: str, value: int = 1, tags: Dict[str, str] = None) -> int:
        """
        Decrement a counter
        
        Args:
            name: Counter name
            value: Value to decrement by
            tags: Tags for the counter
            
        Returns:
            New counter value
        """
        return self.increment(name, -value, tags)
    
    def gauge(self, name: str, value: Union[int, float], tags: Dict[str, str] = None) -> Union[int, float]:
        """
        Set a gauge
        
        Args:
            name: Gauge name
            value: Gauge value
            tags: Tags for the gauge
            
        Returns:
            Gauge value
        """
        with self._lock:
            key = self._get_key(name, tags)
            self._gauges[key] = value
            
            # Check if it's time to report metrics
            self._check_report()
            
            return value
    
    @contextlib.contextmanager
    def timer(self, name: str, tags: Dict[str, str] = None):
        """
        Time a block of code
        
        Args:
            name: Timer name
            tags: Tags for the timer
        """
        start_time = time.time()
        try:
            yield
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            with self._lock:
                key = self._get_key(name, tags)
                if key not in self._timers:
                    self._timers[key] = {
                        'count': 0,
                        'sum': 0,
                        'min': float('inf'),
                        'max': 0
                    }
                
                self._timers[key]['count'] += 1
                self._timers[key]['sum'] += duration
                self._timers[key]['min'] = min(self._timers[key]['min'], duration)
                self._timers[key]['max'] = max(self._timers[key]['max'], duration)
                
                # Check if it's time to report metrics
                self._check_report()
    
    def _get_key(self, name: str, tags: Dict[str, str] = None) -> str:
        """
        Get a key for a metric
        
        Args:
            name: Metric name
            tags: Tags for the metric
            
        Returns:
            Metric key
        """
        if not tags:
            return name
        
        # Sort tags by key to ensure consistent keys
        sorted_tags = sorted(tags.items())
        tag_str = ','.join(f"{k}={v}" for k, v in sorted_tags)
        
        return f"{name}[{tag_str}]"
    
    def _check_report(self):
        """
        Check if it's time to report metrics
        """
        now = time.time()
        if now - self._last_report_time >= self._report_interval:
            self._report_metrics()
            self._last_report_time = now
    
    def _report_metrics(self):
        """
        Report metrics
        """
        # Create a copy of metrics to avoid holding the lock during reporting
        with self._lock:
            counters = self._counters.copy()
            gauges = self._gauges.copy()
            timers = self._timers.copy()
        
        # Log metrics
        if counters:
            logger.info("Counters: %s", json.dumps(counters))
        
        if gauges:
            logger.info("Gauges: %s", json.dumps(gauges))
        
        if timers:
            # Calculate averages for timers
            timer_report = {}
            for key, timer in timers.items():
                if timer['count'] > 0:
                    avg = timer['sum'] / timer['count']
                    timer_report[key] = {
                        'count': timer['count'],
                        'avg': avg,
                        'min': timer['min'],
                        'max': timer['max']
                    }
            
            logger.info("Timers: %s", json.dumps(timer_report))
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics
        
        Returns:
            All metrics
        """
        with self._lock:
            # Calculate averages for timers
            timer_report = {}
            for key, timer in self._timers.items():
                if timer['count'] > 0:
                    avg = timer['sum'] / timer['count']
                    timer_report[key] = {
                        'count': timer['count'],
                        'avg': avg,
                        'min': timer['min'],
                        'max': timer['max']
                    }
            
            return {
                'counters': self._counters.copy(),
                'gauges': self._gauges.copy(),
                'timers': timer_report
            }
    
    def reset(self):
        """
        Reset all metrics
        """
        with self._lock:
            self._counters = {}
            self._gauges = {}
            self._timers = {}
            self._last_report_time = time.time()
    
    def set_report_interval(self, interval: int):
        """
        Set report interval
        
        Args:
            interval: Report interval in seconds
        """
        with self._lock:
            self._report_interval = interval


# Global metrics instance
metrics = Metrics()
