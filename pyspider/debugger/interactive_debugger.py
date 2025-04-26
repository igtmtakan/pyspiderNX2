#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-30 10:00:00

"""
Interactive Debugger for PySpider
"""

import os
import sys
import inspect
import logging
import threading
import traceback
from typing import Dict, List, Any, Optional, Callable, Set, Tuple
from bdb import Bdb, BdbQuit
from io import StringIO

logger = logging.getLogger('debugger.interactive')

class BreakpointInfo:
    """Breakpoint information"""
    def __init__(self, filename: str, lineno: int, condition: Optional[str] = None, enabled: bool = True):
        self.filename = filename
        self.lineno = lineno
        self.condition = condition
        self.enabled = enabled
        self.hits = 0
        
    def __str__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        condition = f" if {self.condition}" if self.condition else ""
        return f"Breakpoint at {self.filename}:{self.lineno} ({status}){condition}, hits: {self.hits}"

class DebuggerState:
    """Debugger state"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    STEPPING = "stepping"
    ERROR = "error"

class InteractiveDebugger(Bdb):
    """Interactive debugger for PySpider"""
    
    def __init__(self):
        super().__init__()
        self.breakpoints: Dict[str, Dict[int, BreakpointInfo]] = {}
        self.state = DebuggerState.STOPPED
        self.current_frame = None
        self.current_frame_info = None
        self.stdout_capture = None
        self.stderr_capture = None
        self.original_stdout = None
        self.original_stderr = None
        self.output_buffer = StringIO()
        self.error_buffer = StringIO()
        self.step_commands = {
            'step_into': self.step_into,
            'step_over': self.step_over,
            'step_out': self.step_out,
            'continue': self.continue_execution,
        }
        self.lock = threading.RLock()
        self._callback = None
        
    def start(self, callback: Optional[Callable] = None):
        """Start the debugger"""
        with self.lock:
            if self.state != DebuggerState.STOPPED:
                return False
            
            self.state = DebuggerState.RUNNING
            self._callback = callback
            return True
    
    def stop(self):
        """Stop the debugger"""
        with self.lock:
            if self.state == DebuggerState.STOPPED:
                return False
            
            self.state = DebuggerState.STOPPED
            self.clear_all_breaks()
            self._callback = None
            return True
    
    def set_break(self, filename: str, lineno: int, condition: Optional[str] = None) -> Optional[BreakpointInfo]:
        """Set a breakpoint"""
        with self.lock:
            # Normalize filename
            filename = os.path.abspath(filename)
            
            # Check if file exists
            if not os.path.isfile(filename):
                logger.error(f"File not found: {filename}")
                return None
            
            # Check if line is valid
            try:
                with open(filename, 'r') as f:
                    lines = f.readlines()
                    if lineno <= 0 or lineno > len(lines):
                        logger.error(f"Invalid line number: {lineno}")
                        return None
            except Exception as e:
                logger.error(f"Error reading file: {e}")
                return None
            
            # Set breakpoint
            if filename not in self.breakpoints:
                self.breakpoints[filename] = {}
            
            bp_info = BreakpointInfo(filename, lineno, condition)
            self.breakpoints[filename][lineno] = bp_info
            
            # Set breakpoint in bdb
            super().set_break(filename, lineno, condition)
            
            logger.info(f"Breakpoint set at {filename}:{lineno}")
            return bp_info
    
    def clear_break(self, filename: str, lineno: int) -> bool:
        """Clear a breakpoint"""
        with self.lock:
            # Normalize filename
            filename = os.path.abspath(filename)
            
            # Check if breakpoint exists
            if filename not in self.breakpoints or lineno not in self.breakpoints[filename]:
                logger.error(f"No breakpoint at {filename}:{lineno}")
                return False
            
            # Clear breakpoint
            del self.breakpoints[filename][lineno]
            if not self.breakpoints[filename]:
                del self.breakpoints[filename]
            
            # Clear breakpoint in bdb
            super().clear_break(filename, lineno)
            
            logger.info(f"Breakpoint cleared at {filename}:{lineno}")
            return True
    
    def enable_break(self, filename: str, lineno: int) -> bool:
        """Enable a breakpoint"""
        with self.lock:
            # Normalize filename
            filename = os.path.abspath(filename)
            
            # Check if breakpoint exists
            if filename not in self.breakpoints or lineno not in self.breakpoints[filename]:
                logger.error(f"No breakpoint at {filename}:{lineno}")
                return False
            
            # Enable breakpoint
            bp_info = self.breakpoints[filename][lineno]
            bp_info.enabled = True
            
            # Enable breakpoint in bdb
            super().clear_break(filename, lineno)
            super().set_break(filename, lineno, bp_info.condition)
            
            logger.info(f"Breakpoint enabled at {filename}:{lineno}")
            return True
    
    def disable_break(self, filename: str, lineno: int) -> bool:
        """Disable a breakpoint"""
        with self.lock:
            # Normalize filename
            filename = os.path.abspath(filename)
            
            # Check if breakpoint exists
            if filename not in self.breakpoints or lineno not in self.breakpoints[filename]:
                logger.error(f"No breakpoint at {filename}:{lineno}")
                return False
            
            # Disable breakpoint
            bp_info = self.breakpoints[filename][lineno]
            bp_info.enabled = False
            
            # Disable breakpoint in bdb
            super().clear_break(filename, lineno)
            
            logger.info(f"Breakpoint disabled at {filename}:{lineno}")
            return True
    
    def clear_all_breaks(self) -> bool:
        """Clear all breakpoints"""
        with self.lock:
            self.breakpoints = {}
            super().clear_all_breaks()
            logger.info("All breakpoints cleared")
            return True
    
    def get_all_breaks(self) -> List[BreakpointInfo]:
        """Get all breakpoints"""
        with self.lock:
            result = []
            for filename, breaks in self.breakpoints.items():
                for lineno, bp_info in breaks.items():
                    result.append(bp_info)
            return result
    
    def get_break(self, filename: str, lineno: int) -> Optional[BreakpointInfo]:
        """Get breakpoint information"""
        with self.lock:
            # Normalize filename
            filename = os.path.abspath(filename)
            
            # Check if breakpoint exists
            if filename not in self.breakpoints or lineno not in self.breakpoints[filename]:
                return None
            
            return self.breakpoints[filename][lineno]
    
    def step_into(self):
        """Step into the next line"""
        with self.lock:
            if self.state != DebuggerState.PAUSED:
                return False
            
            self.state = DebuggerState.STEPPING
            self.set_step()
            return True
    
    def step_over(self):
        """Step over the next line"""
        with self.lock:
            if self.state != DebuggerState.PAUSED:
                return False
            
            self.state = DebuggerState.STEPPING
            self.set_next(self.current_frame)
            return True
    
    def step_out(self):
        """Step out of the current function"""
        with self.lock:
            if self.state != DebuggerState.PAUSED:
                return False
            
            self.state = DebuggerState.STEPPING
            self.set_return(self.current_frame)
            return True
    
    def continue_execution(self):
        """Continue execution"""
        with self.lock:
            if self.state != DebuggerState.PAUSED:
                return False
            
            self.state = DebuggerState.RUNNING
            self.set_continue()
            return True
    
    def get_current_frame_info(self) -> Dict[str, Any]:
        """Get current frame information"""
        with self.lock:
            if self.state != DebuggerState.PAUSED or not self.current_frame:
                return {}
            
            frame = self.current_frame
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno
            function = frame.f_code.co_name
            
            # Get source code
            source_lines = []
            source_line = ""
            try:
                with open(filename, 'r') as f:
                    source_lines = f.readlines()
                    if 0 < lineno <= len(source_lines):
                        source_line = source_lines[lineno - 1].rstrip()
            except Exception as e:
                logger.error(f"Error reading source: {e}")
            
            # Get context (5 lines before and after)
            context_start = max(0, lineno - 6)
            context_end = min(len(source_lines), lineno + 5)
            context = []
            for i in range(context_start, context_end):
                context.append({
                    'lineno': i + 1,
                    'content': source_lines[i].rstrip() if i < len(source_lines) else "",
                    'current': i + 1 == lineno
                })
            
            # Get local variables
            locals_dict = {}
            for name, value in frame.f_locals.items():
                try:
                    # Convert value to string representation
                    str_value = repr(value)
                    # Truncate long values
                    if len(str_value) > 1000:
                        str_value = str_value[:1000] + "..."
                    locals_dict[name] = str_value
                except Exception as e:
                    locals_dict[name] = f"<Error: {e}>"
            
            # Get global variables
            globals_dict = {}
            for name, value in frame.f_globals.items():
                # Skip modules and internal variables
                if name.startswith('__') and name.endswith('__'):
                    continue
                try:
                    # Convert value to string representation
                    str_value = repr(value)
                    # Truncate long values
                    if len(str_value) > 1000:
                        str_value = str_value[:1000] + "..."
                    globals_dict[name] = str_value
                except Exception as e:
                    globals_dict[name] = f"<Error: {e}>"
            
            # Get call stack
            stack = []
            frame_temp = frame
            while frame_temp:
                stack.append({
                    'filename': frame_temp.f_code.co_filename,
                    'lineno': frame_temp.f_lineno,
                    'function': frame_temp.f_code.co_name
                })
                frame_temp = frame_temp.f_back
            
            # Get output
            output = self.output_buffer.getvalue()
            error = self.error_buffer.getvalue()
            
            return {
                'filename': filename,
                'lineno': lineno,
                'function': function,
                'source_line': source_line,
                'context': context,
                'locals': locals_dict,
                'globals': globals_dict,
                'stack': stack,
                'output': output,
                'error': error
            }
    
    def evaluate_expression(self, expression: str) -> Dict[str, Any]:
        """Evaluate an expression in the current frame"""
        with self.lock:
            if self.state != DebuggerState.PAUSED or not self.current_frame:
                return {'success': False, 'error': 'Debugger not paused'}
            
            try:
                # Evaluate expression
                result = eval(expression, self.current_frame.f_globals, self.current_frame.f_locals)
                
                # Convert result to string representation
                str_result = repr(result)
                # Truncate long results
                if len(str_result) > 10000:
                    str_result = str_result[:10000] + "..."
                
                return {
                    'success': True,
                    'result': str_result,
                    'type': type(result).__name__
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
    
    def execute_statement(self, statement: str) -> Dict[str, Any]:
        """Execute a statement in the current frame"""
        with self.lock:
            if self.state != DebuggerState.PAUSED or not self.current_frame:
                return {'success': False, 'error': 'Debugger not paused'}
            
            try:
                # Execute statement
                exec(statement, self.current_frame.f_globals, self.current_frame.f_locals)
                
                return {
                    'success': True
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
    
    def start_capture(self):
        """Start capturing stdout and stderr"""
        self.output_buffer = StringIO()
        self.error_buffer = StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self.output_buffer
        sys.stderr = self.error_buffer
    
    def stop_capture(self):
        """Stop capturing stdout and stderr"""
        if self.original_stdout:
            sys.stdout = self.original_stdout
            self.original_stdout = None
        
        if self.original_stderr:
            sys.stderr = self.original_stderr
            self.original_stderr = None
    
    def debug_script(self, script: str, globals_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Debug a script"""
        with self.lock:
            if self.state != DebuggerState.RUNNING:
                return {'success': False, 'error': 'Debugger not running'}
            
            # Create globals dictionary
            if globals_dict is None:
                globals_dict = {}
            
            # Add builtins
            globals_dict['__builtins__'] = __builtins__
            
            try:
                # Start capturing stdout and stderr
                self.start_capture()
                
                # Run script
                self.run(script, globals_dict)
                
                # Stop capturing stdout and stderr
                self.stop_capture()
                
                return {
                    'success': True,
                    'output': self.output_buffer.getvalue(),
                    'error': self.error_buffer.getvalue()
                }
            except BdbQuit:
                # Stop capturing stdout and stderr
                self.stop_capture()
                
                return {
                    'success': True,
                    'output': self.output_buffer.getvalue(),
                    'error': self.error_buffer.getvalue()
                }
            except Exception as e:
                # Stop capturing stdout and stderr
                self.stop_capture()
                
                return {
                    'success': False,
                    'error': str(e),
                    'traceback': traceback.format_exc(),
                    'output': self.output_buffer.getvalue(),
                    'error_output': self.error_buffer.getvalue()
                }
    
    def debug_function(self, func: Callable, args: List[Any] = None, kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
        """Debug a function"""
        with self.lock:
            if self.state != DebuggerState.RUNNING:
                return {'success': False, 'error': 'Debugger not running'}
            
            if args is None:
                args = []
            
            if kwargs is None:
                kwargs = {}
            
            try:
                # Start capturing stdout and stderr
                self.start_capture()
                
                # Run function
                result = self.runcall(func, *args, **kwargs)
                
                # Stop capturing stdout and stderr
                self.stop_capture()
                
                return {
                    'success': True,
                    'result': result,
                    'output': self.output_buffer.getvalue(),
                    'error': self.error_buffer.getvalue()
                }
            except BdbQuit:
                # Stop capturing stdout and stderr
                self.stop_capture()
                
                return {
                    'success': True,
                    'output': self.output_buffer.getvalue(),
                    'error': self.error_buffer.getvalue()
                }
            except Exception as e:
                # Stop capturing stdout and stderr
                self.stop_capture()
                
                return {
                    'success': False,
                    'error': str(e),
                    'traceback': traceback.format_exc(),
                    'output': self.output_buffer.getvalue(),
                    'error_output': self.error_buffer.getvalue()
                }
    
    def user_line(self, frame):
        """Called when the debugger stops at a line"""
        with self.lock:
            # Check if we should stop at this line
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno
            
            # Check if this is a breakpoint
            is_breakpoint = False
            if filename in self.breakpoints and lineno in self.breakpoints[filename]:
                bp_info = self.breakpoints[filename][lineno]
                if bp_info.enabled:
                    bp_info.hits += 1
                    is_breakpoint = True
            
            # Update state
            self.state = DebuggerState.PAUSED
            self.current_frame = frame
            
            # Get frame information
            self.current_frame_info = self.get_current_frame_info()
            
            # Call callback
            if self._callback:
                self._callback({
                    'event': 'pause',
                    'reason': 'breakpoint' if is_breakpoint else 'step',
                    'frame_info': self.current_frame_info
                })
            
            # Wait for user command
            self.wait_for_user_command()
    
    def user_return(self, frame, return_value):
        """Called when a function returns"""
        pass
    
    def user_exception(self, frame, exc_info):
        """Called when an exception occurs"""
        with self.lock:
            # Update state
            self.state = DebuggerState.PAUSED
            self.current_frame = frame
            
            # Get frame information
            self.current_frame_info = self.get_current_frame_info()
            
            # Get exception information
            exc_type, exc_value, exc_traceback = exc_info
            exception_info = {
                'type': exc_type.__name__,
                'message': str(exc_value),
                'traceback': traceback.format_tb(exc_traceback)
            }
            
            # Call callback
            if self._callback:
                self._callback({
                    'event': 'pause',
                    'reason': 'exception',
                    'frame_info': self.current_frame_info,
                    'exception': exception_info
                })
            
            # Wait for user command
            self.wait_for_user_command()
    
    def wait_for_user_command(self):
        """Wait for user command"""
        # This method is a placeholder
        # In a real implementation, this would wait for commands from the UI
        # For now, we'll just continue execution
        self.continue_execution()
    
    def set_callback(self, callback: Callable):
        """Set callback function"""
        self._callback = callback
