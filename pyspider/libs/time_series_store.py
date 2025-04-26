#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-25 10:00:00

import time
import threading
import logging
from collections import defaultdict, deque

logger = logging.getLogger('time_series_store')

class TimeSeriesStore:
    """
    Store time series data for projects
    """
    def __init__(self, max_points=100, retention_period=3600):
        """
        Initialize the time series store
        
        Args:
            max_points: Maximum number of data points to store per project
            retention_period: Data retention period in seconds
        """
        self.max_points = max_points
        self.retention_period = retention_period
        self.data = defaultdict(lambda: defaultdict(lambda: deque(maxlen=max_points)))
        self.lock = threading.RLock()
        self.last_cleanup = time.time()
    
    def add_data_point(self, project, metric, value):
        """
        Add a data point for a project
        
        Args:
            project: Project name
            metric: Metric name (e.g., 'success_rate', 'process_time')
            value: Metric value
        """
        with self.lock:
            timestamp = time.time()
            self.data[project][metric].append({
                'timestamp': timestamp,
                'value': value
            })
            
            # Cleanup old data periodically
            if timestamp - self.last_cleanup > 60:  # Cleanup every minute
                self._cleanup_old_data()
                self.last_cleanup = timestamp
    
    def get_data(self, project, metric, start_time=None, end_time=None):
        """
        Get time series data for a project
        
        Args:
            project: Project name
            metric: Metric name
            start_time: Start time (timestamp)
            end_time: End time (timestamp)
            
        Returns:
            List of data points
        """
        with self.lock:
            if project not in self.data or metric not in self.data[project]:
                return []
            
            data = list(self.data[project][metric])
            
            if start_time is not None:
                data = [d for d in data if d['timestamp'] >= start_time]
            
            if end_time is not None:
                data = [d for d in data if d['timestamp'] <= end_time]
            
            return data
    
    def get_all_data(self, project=None, start_time=None, end_time=None):
        """
        Get all time series data
        
        Args:
            project: Project name (optional)
            start_time: Start time (timestamp)
            end_time: End time (timestamp)
            
        Returns:
            Dictionary of project -> metric -> data points
        """
        with self.lock:
            result = {}
            
            if project:
                projects = [project]
            else:
                projects = list(self.data.keys())
            
            for proj in projects:
                if proj not in self.data:
                    continue
                
                result[proj] = {}
                for metric, data in self.data[proj].items():
                    filtered_data = list(data)
                    
                    if start_time is not None:
                        filtered_data = [d for d in filtered_data if d['timestamp'] >= start_time]
                    
                    if end_time is not None:
                        filtered_data = [d for d in filtered_data if d['timestamp'] <= end_time]
                    
                    result[proj][metric] = filtered_data
            
            return result
    
    def _cleanup_old_data(self):
        """
        Clean up old data points
        """
        now = time.time()
        cutoff = now - self.retention_period
        
        for project in list(self.data.keys()):
            for metric in list(self.data[project].keys()):
                # Filter out old data points
                self.data[project][metric] = deque(
                    [d for d in self.data[project][metric] if d['timestamp'] >= cutoff],
                    maxlen=self.max_points
                )
                
                # Remove empty metrics
                if not self.data[project][metric]:
                    del self.data[project][metric]
            
            # Remove empty projects
            if not self.data[project]:
                del self.data[project]

# Global instance
time_series_store = TimeSeriesStore()
