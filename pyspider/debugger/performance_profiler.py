#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-30 10:00:00

"""
Performance Profiler for PySpider
"""

import os
import time
import logging
import cProfile
import pstats
import io
import tracemalloc
import gc
import threading
import json
from typing import Dict, List, Any, Optional, Callable, Union
from functools import wraps

logger = logging.getLogger('debugger.performance_profiler')

class PerformanceProfiler:
    """Performance profiler for PySpider"""
    
    def __init__(self):
        self.profiler = None
        self.memory_tracker = None
        self.is_profiling = False
        self.is_tracking_memory = False
        self.memory_snapshots = []
        self.max_snapshots = 10
        self.timing_stats = {}
        self.function_stats = {}
        self.lock = threading.RLock()
    
    def start_profiling(self) -> bool:
        """Start CPU profiling"""
        with self.lock:
            if self.is_profiling:
                return False
            
            self.profiler = cProfile.Profile()
            self.profiler.enable()
            self.is_profiling = True
            
            logger.info("CPU profiling started")
            return True
    
    def stop_profiling(self) -> Dict[str, Any]:
        """Stop CPU profiling and return results"""
        with self.lock:
            if not self.is_profiling or not self.profiler:
                return {'error': 'Profiling not started'}
            
            self.profiler.disable()
            self.is_profiling = False
            
            # Get profiling results
            s = io.StringIO()
            ps = pstats.Stats(self.profiler, stream=s).sort_stats('cumulative')
            ps.print_stats(50)  # Print top 50 functions
            
            # Get function statistics
            function_stats = []
            for func, (cc, nc, tt, ct, callers) in ps.stats.items():
                if len(function_stats) >= 100:  # Limit to top 100 functions
                    break
                
                if isinstance(func, tuple) and len(func) == 3:
                    filename, lineno, funcname = func
                    
                    # Skip built-in functions
                    if filename == '~' or funcname == '~':
                        continue
                    
                    function_stats.append({
                        'filename': filename,
                        'lineno': lineno,
                        'funcname': funcname,
                        'calls': cc,  # Cumulative calls
                        'ncalls': nc,  # Number of calls
                        'tottime': tt,  # Total time spent in this function
                        'cumtime': ct,  # Cumulative time spent in this function and all subfunctions
                        'callers': len(callers)  # Number of callers
                    })
            
            # Sort by cumulative time
            function_stats.sort(key=lambda x: x['cumtime'], reverse=True)
            
            logger.info("CPU profiling stopped")
            
            return {
                'success': True,
                'text_report': s.getvalue(),
                'function_stats': function_stats
            }
    
    def start_memory_tracking(self) -> bool:
        """Start memory tracking"""
        with self.lock:
            if self.is_tracking_memory:
                return False
            
            # Start tracemalloc
            tracemalloc.start()
            self.is_tracking_memory = True
            self.memory_snapshots = []
            
            # Take initial snapshot
            self.take_memory_snapshot("Initial")
            
            logger.info("Memory tracking started")
            return True
    
    def stop_memory_tracking(self) -> Dict[str, Any]:
        """Stop memory tracking and return results"""
        with self.lock:
            if not self.is_tracking_memory:
                return {'error': 'Memory tracking not started'}
            
            # Take final snapshot
            self.take_memory_snapshot("Final")
            
            # Stop tracemalloc
            tracemalloc.stop()
            self.is_tracking_memory = False
            
            logger.info("Memory tracking stopped")
            
            return {
                'success': True,
                'snapshots': self.memory_snapshots
            }
    
    def take_memory_snapshot(self, label: str = None) -> Dict[str, Any]:
        """Take a memory snapshot"""
        with self.lock:
            if not self.is_tracking_memory:
                return {'error': 'Memory tracking not started'}
            
            # Generate label if not provided
            if not label:
                label = f"Snapshot {len(self.memory_snapshots) + 1}"
            
            # Take snapshot
            snapshot = tracemalloc.take_snapshot()
            
            # Get memory statistics
            stats = snapshot.statistics('lineno')
            
            # Get top memory consumers
            top_stats = []
            for stat in stats[:50]:  # Top 50 memory consumers
                top_stats.append({
                    'filename': stat.traceback[0].filename,
                    'lineno': stat.traceback[0].lineno,
                    'size': stat.size,
                    'count': stat.count
                })
            
            # Get total memory usage
            total_size = sum(stat.size for stat in stats)
            
            # Get current process memory usage
            import psutil
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            # Create snapshot info
            snapshot_info = {
                'label': label,
                'timestamp': time.time(),
                'total_size': total_size,
                'rss': memory_info.rss,  # Resident Set Size
                'vms': memory_info.vms,  # Virtual Memory Size
                'top_stats': top_stats
            }
            
            # Add to snapshots
            self.memory_snapshots.append(snapshot_info)
            
            # Limit the number of snapshots
            if len(self.memory_snapshots) > self.max_snapshots:
                self.memory_snapshots.pop(0)
            
            logger.info(f"Memory snapshot taken: {label}")
            
            return snapshot_info
    
    def compare_memory_snapshots(self, snapshot1_index: int, snapshot2_index: int) -> Dict[str, Any]:
        """Compare two memory snapshots"""
        with self.lock:
            if not self.memory_snapshots:
                return {'error': 'No memory snapshots available'}
            
            if snapshot1_index < 0 or snapshot1_index >= len(self.memory_snapshots) or \
               snapshot2_index < 0 or snapshot2_index >= len(self.memory_snapshots):
                return {'error': 'Invalid snapshot indices'}
            
            snapshot1 = self.memory_snapshots[snapshot1_index]
            snapshot2 = self.memory_snapshots[snapshot2_index]
            
            # Compare total memory usage
            total_diff = snapshot2['total_size'] - snapshot1['total_size']
            rss_diff = snapshot2['rss'] - snapshot1['rss']
            vms_diff = snapshot2['vms'] - snapshot1['vms']
            
            return {
                'success': True,
                'snapshot1': {
                    'label': snapshot1['label'],
                    'timestamp': snapshot1['timestamp'],
                    'total_size': snapshot1['total_size'],
                    'rss': snapshot1['rss'],
                    'vms': snapshot1['vms']
                },
                'snapshot2': {
                    'label': snapshot2['label'],
                    'timestamp': snapshot2['timestamp'],
                    'total_size': snapshot2['total_size'],
                    'rss': snapshot2['rss'],
                    'vms': snapshot2['vms']
                },
                'total_diff': total_diff,
                'rss_diff': rss_diff,
                'vms_diff': vms_diff,
                'time_diff': snapshot2['timestamp'] - snapshot1['timestamp']
            }
    
    def start_timing(self, name: str) -> bool:
        """Start timing a section of code"""
        with self.lock:
            if name in self.timing_stats and self.timing_stats[name]['active']:
                return False
            
            self.timing_stats[name] = {
                'start_time': time.time(),
                'active': True,
                'elapsed': 0,
                'calls': 1
            }
            
            return True
    
    def stop_timing(self, name: str) -> Dict[str, Any]:
        """Stop timing a section of code"""
        with self.lock:
            if name not in self.timing_stats or not self.timing_stats[name]['active']:
                return {'error': f"Timing '{name}' not started"}
            
            end_time = time.time()
            elapsed = end_time - self.timing_stats[name]['start_time']
            
            self.timing_stats[name]['active'] = False
            self.timing_stats[name]['elapsed'] += elapsed
            
            return {
                'success': True,
                'name': name,
                'elapsed': elapsed,
                'total_elapsed': self.timing_stats[name]['elapsed'],
                'calls': self.timing_stats[name]['calls']
            }
    
    def reset_timing(self, name: str = None) -> bool:
        """Reset timing statistics"""
        with self.lock:
            if name:
                if name not in self.timing_stats:
                    return False
                
                self.timing_stats[name] = {
                    'start_time': 0,
                    'active': False,
                    'elapsed': 0,
                    'calls': 0
                }
            else:
                self.timing_stats = {}
            
            return True
    
    def get_timing_stats(self, name: str = None) -> Dict[str, Any]:
        """Get timing statistics"""
        with self.lock:
            if name:
                if name not in self.timing_stats:
                    return {'error': f"Timing '{name}' not found"}
                
                return {
                    'success': True,
                    'name': name,
                    'active': self.timing_stats[name]['active'],
                    'elapsed': self.timing_stats[name]['elapsed'],
                    'calls': self.timing_stats[name]['calls']
                }
            else:
                result = []
                for name, stats in self.timing_stats.items():
                    result.append({
                        'name': name,
                        'active': stats['active'],
                        'elapsed': stats['elapsed'],
                        'calls': stats['calls']
                    })
                
                return {
                    'success': True,
                    'stats': result
                }
    
    def profile_function(self, func: Callable) -> Callable:
        """Decorator to profile a function"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function name
            func_name = func.__name__
            
            # Start timing
            start_time = time.time()
            
            # Initialize function stats if not exists
            if func_name not in self.function_stats:
                self.function_stats[func_name] = {
                    'calls': 0,
                    'total_time': 0,
                    'min_time': float('inf'),
                    'max_time': 0,
                    'avg_time': 0,
                    'last_call_time': 0
                }
            
            # Call function
            try:
                result = func(*args, **kwargs)
            finally:
                # Stop timing
                end_time = time.time()
                elapsed = end_time - start_time
                
                # Update function stats
                with self.lock:
                    stats = self.function_stats[func_name]
                    stats['calls'] += 1
                    stats['total_time'] += elapsed
                    stats['min_time'] = min(stats['min_time'], elapsed)
                    stats['max_time'] = max(stats['max_time'], elapsed)
                    stats['avg_time'] = stats['total_time'] / stats['calls']
                    stats['last_call_time'] = elapsed
            
            return result
        
        return wrapper
    
    def get_function_stats(self, func_name: str = None) -> Dict[str, Any]:
        """Get function statistics"""
        with self.lock:
            if func_name:
                if func_name not in self.function_stats:
                    return {'error': f"Function '{func_name}' not found"}
                
                return {
                    'success': True,
                    'name': func_name,
                    'stats': self.function_stats[func_name]
                }
            else:
                result = []
                for name, stats in self.function_stats.items():
                    result.append({
                        'name': name,
                        'stats': stats
                    })
                
                return {
                    'success': True,
                    'stats': result
                }
    
    def reset_function_stats(self, func_name: str = None) -> bool:
        """Reset function statistics"""
        with self.lock:
            if func_name:
                if func_name not in self.function_stats:
                    return False
                
                self.function_stats[func_name] = {
                    'calls': 0,
                    'total_time': 0,
                    'min_time': float('inf'),
                    'max_time': 0,
                    'avg_time': 0,
                    'last_call_time': 0
                }
            else:
                self.function_stats = {}
            
            return True
    
    def collect_garbage(self) -> Dict[str, Any]:
        """Collect garbage"""
        # Get memory usage before collection
        import psutil
        process = psutil.Process(os.getpid())
        before_memory = process.memory_info()
        
        # Collect garbage
        collected = gc.collect()
        
        # Get memory usage after collection
        after_memory = process.memory_info()
        
        return {
            'success': True,
            'collected': collected,
            'before_rss': before_memory.rss,
            'after_rss': after_memory.rss,
            'diff_rss': before_memory.rss - after_memory.rss,
            'before_vms': before_memory.vms,
            'after_vms': after_memory.vms,
            'diff_vms': before_memory.vms - after_memory.vms
        }
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage"""
        import psutil
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            'success': True,
            'rss': memory_info.rss,  # Resident Set Size
            'vms': memory_info.vms,  # Virtual Memory Size
            'percent': process.memory_percent(),
            'cpu_percent': process.cpu_percent(interval=0.1)
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report"""
        # Get memory usage
        memory_usage = self.get_memory_usage()
        
        # Get timing stats
        timing_stats = self.get_timing_stats()
        
        # Get function stats
        function_stats = self.get_function_stats()
        
        # Get memory snapshots
        memory_snapshots = []
        for snapshot in self.memory_snapshots:
            memory_snapshots.append({
                'label': snapshot['label'],
                'timestamp': snapshot['timestamp'],
                'total_size': snapshot['total_size'],
                'rss': snapshot['rss'],
                'vms': snapshot['vms']
            })
        
        # Get system info
        import platform
        import psutil
        
        system_info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'memory_percent': psutil.virtual_memory().percent
        }
        
        return {
            'success': True,
            'timestamp': time.time(),
            'memory_usage': memory_usage,
            'timing_stats': timing_stats,
            'function_stats': function_stats,
            'memory_snapshots': memory_snapshots,
            'system_info': system_info
        }
    
    def save_report(self, filename: str) -> Dict[str, Any]:
        """Save performance report to a file"""
        try:
            report = self.generate_report()
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            return {
                'success': True,
                'filename': filename
            }
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return {
                'success': False,
                'error': str(e)
            }
