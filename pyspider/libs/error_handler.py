#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-20 12:20:00

"""
Error handler for PySpider
"""

import logging
import traceback
import json
import time
from typing import Dict, Any, Callable, Optional, Union, List, Set, Type

from pyspider.libs.error_types import PySpiderError

logger = logging.getLogger('error_handler')

class ErrorHandler:
    """Handles errors in PySpider"""
    
    def __init__(self):
        """Initialize ErrorHandler"""
        self.error_callbacks: Dict[Type[Exception], List[Callable]] = {}
        self.global_callbacks: List[Callable] = []
        self.error_counts: Dict[str, int] = {}
        self.error_timestamps: Dict[str, List[float]] = {}
        self.max_error_history = 100
        
    def register_callback(self, error_type: Type[Exception], callback: Callable):
        """
        Register a callback for a specific error type
        
        Args:
            error_type: Type of exception to handle
            callback: Callback function to execute
        """
        if error_type not in self.error_callbacks:
            self.error_callbacks[error_type] = []
        self.error_callbacks[error_type].append(callback)
        
    def register_global_callback(self, callback: Callable):
        """
        Register a global callback for all errors
        
        Args:
            callback: Callback function to execute
        """
        self.global_callbacks.append(callback)
        
    def process(self, error: Exception, task=None, context: Dict[str, Any] = None):
        """
        Process an error
        
        Args:
            error: Exception that occurred
            task: Task that caused the error
            context: Additional context information
        """
        if context is None:
            context = {}
            
        # Add task information to context
        if task:
            if hasattr(task, 'to_dict'):
                context['task'] = task.to_dict()
            elif isinstance(task, dict):
                context['task'] = task
            else:
                context['task'] = str(task)
                
            # Extract task ID
            if hasattr(task, 'taskid'):
                context['task_id'] = task.taskid
            elif hasattr(task, 'id'):
                context['task_id'] = task.id
            elif isinstance(task, dict) and 'taskid' in task:
                context['task_id'] = task['taskid']
            elif isinstance(task, dict) and 'id' in task:
                context['task_id'] = task['id']
                
        # Record error
        self._record_error(error)
        
        # Execute type-specific callbacks
        executed = False
        for error_type, callbacks in self.error_callbacks.items():
            if isinstance(error, error_type):
                for callback in callbacks:
                    try:
                        callback(error, task, context)
                        executed = True
                    except Exception as e:
                        logger.error(f"Error in error callback: {e}")
                        logger.error(traceback.format_exc())
        
        # Execute global callbacks
        for callback in self.global_callbacks:
            try:
                callback(error, task, context)
                executed = True
            except Exception as e:
                logger.error(f"Error in global error callback: {e}")
                logger.error(traceback.format_exc())
                
        # If no callbacks were executed, log the error
        if not executed:
            self._default_error_handler(error, task, context)
    
    def _record_error(self, error: Exception):
        """Record error statistics"""
        error_type = type(error).__name__
        
        # Update error count
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Update error timestamps
        if error_type not in self.error_timestamps:
            self.error_timestamps[error_type] = []
        
        self.error_timestamps[error_type].append(time.time())
        
        # Limit history size
        if len(self.error_timestamps[error_type]) > self.max_error_history:
            self.error_timestamps[error_type] = self.error_timestamps[error_type][-self.max_error_history:]
    
    def _default_error_handler(self, error: Exception, task=None, context: Dict[str, Any] = None):
        """Default error handler when no callbacks are executed"""
        error_type = type(error).__name__
        error_message = str(error)
        
        log_context = {
            'error_type': error_type,
        }
        
        if context:
            log_context.update(context)
            
        if task:
            if hasattr(task, 'url'):
                log_context['url'] = task.url
            elif isinstance(task, dict) and 'url' in task:
                log_context['url'] = task['url']
                
        logger.error(f"{error_type}: {error_message}", extra=log_context)
        logger.debug(traceback.format_exc())
    
    def get_error_count(self, error_type: str) -> int:
        """Get count of a specific error type"""
        return self.error_counts.get(error_type, 0)
    
    def get_error_rate(self, error_type: str, window_seconds: float = 60.0) -> float:
        """
        Get error rate for a specific error type
        
        Args:
            error_type: Type of error
            window_seconds: Time window in seconds
            
        Returns:
            Error rate (errors per second)
        """
        if error_type not in self.error_timestamps:
            return 0.0
            
        timestamps = self.error_timestamps[error_type]
        now = time.time()
        
        # Count errors in the time window
        recent_errors = sum(1 for ts in timestamps if now - ts <= window_seconds)
        
        # Calculate rate
        return recent_errors / window_seconds if window_seconds > 0 else 0.0
    
    def get_all_error_counts(self) -> Dict[str, int]:
        """Get counts of all error types"""
        return self.error_counts.copy()
    
    def reset_statistics(self):
        """Reset error statistics"""
        self.error_counts = {}
        self.error_timestamps = {}
