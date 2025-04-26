#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-05-01 12:00:00

"""
Error classes for PySpider
"""

import logging
import traceback
from typing import Optional, Any, Dict, Type

logger = logging.getLogger('errors')

class PySpiderError(Exception):
    """Base class for all PySpider exceptions"""
    status_code = 599  # Default status code for errors

class NetworkError(PySpiderError):
    """Network error"""
    status_code = 599

class TimeoutError(NetworkError):
    """Timeout error"""
    status_code = 599

class HTTPError(NetworkError):
    """HTTP error"""
    def __init__(self, status_code: int, message: str = None):
        self.status_code = status_code
        self.message = message or f"HTTP Error: {status_code}"
        super().__init__(self.message)

class ProxyError(NetworkError):
    """Proxy error"""
    status_code = 599

class DNSError(NetworkError):
    """DNS error"""
    status_code = 599

class SSLError(NetworkError):
    """SSL error"""
    status_code = 599

class ProcessError(PySpiderError):
    """Process error"""
    status_code = 599

class ScriptError(PySpiderError):
    """Script error"""
    status_code = 599

class ParseError(PySpiderError):
    """Parse error"""
    status_code = 599

def convert_exception(exception: Exception) -> PySpiderError:
    """
    Convert a generic exception to a PySpider exception
    
    Args:
        exception: Exception to convert
        
    Returns:
        PySpider exception
    """
    if isinstance(exception, PySpiderError):
        return exception
    
    # Convert common exceptions
    error_type = type(exception).__name__
    error_message = str(exception)
    
    if error_type == 'TimeoutError' or 'timeout' in error_message.lower():
        return TimeoutError(f"Timeout error: {error_message}")
    elif error_type == 'ConnectionError' or 'connection' in error_message.lower():
        return NetworkError(f"Connection error: {error_message}")
    elif error_type == 'SSLError' or 'ssl' in error_message.lower():
        return SSLError(f"SSL error: {error_message}")
    elif error_type == 'ProxyError' or 'proxy' in error_message.lower():
        return ProxyError(f"Proxy error: {error_message}")
    elif error_type == 'DNSError' or 'dns' in error_message.lower() or 'name resolution' in error_message.lower():
        return DNSError(f"DNS error: {error_message}")
    elif error_type == 'HTTPError' and hasattr(exception, 'status_code'):
        return HTTPError(getattr(exception, 'status_code'), error_message)
    else:
        # Default to NetworkError for unknown exceptions
        return NetworkError(f"{error_type}: {error_message}")
