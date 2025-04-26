#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
Log utilities for PySpider
"""

# ANSI color codes
class Colors:
    RESET = '\033[0m'
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def colored_log(logger, level, color, message, *args, **kwargs):
    """
    Log a colored message

    Args:
        logger: The logger instance
        level: The log level (debug, info, warning, error, critical)
        color: The color to use (from Colors class)
        message: The message to log
        *args, **kwargs: Additional arguments for the logger
    """
    # Format the message with args and kwargs first
    if args or kwargs:
        try:
            formatted_message = message % args
        except TypeError:
            formatted_message = message
    else:
        formatted_message = message

    # Add color codes
    colored_message = f"{color}{formatted_message}{Colors.RESET}"

    # Log directly to stdout/stderr to ensure colors are displayed
    import sys
    if level in ('error', 'critical'):
        print(colored_message, file=sys.stderr)
    else:
        print(colored_message, file=sys.stdout)

    # Also log through the regular logger (without colors)
    if level == 'debug':
        logger.debug(message, *args, **kwargs)
    elif level == 'info':
        logger.info(message, *args, **kwargs)
    elif level == 'warning':
        logger.warning(message, *args, **kwargs)
    elif level == 'error':
        logger.error(message, *args, **kwargs)
    elif level == 'critical':
        logger.critical(message, *args, **kwargs)
    else:
        # Default to info
        logger.info(message, *args, **kwargs)

def success_log(logger, message, *args, **kwargs):
    """Log a success message in green"""
    colored_log(logger, 'info', Colors.GREEN, message, *args, **kwargs)

def error_log(logger, message, *args, **kwargs):
    """Log an error message in red"""
    colored_log(logger, 'error', Colors.RED, message, *args, **kwargs)

def warning_log(logger, message, *args, **kwargs):
    """Log a warning message in yellow"""
    colored_log(logger, 'warning', Colors.YELLOW, message, *args, **kwargs)

def info_log(logger, message, *args, **kwargs):
    """Log an info message in blue"""
    colored_log(logger, 'info', Colors.BLUE, message, *args, **kwargs)
