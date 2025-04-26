#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-20 12:00:00

"""
Error types for PySpider
"""

class PySpiderError(Exception):
    """Base class for all PySpider errors"""
    pass

class NetworkError(PySpiderError):
    """Error raised when network connection fails"""
    pass

class TimeoutError(PySpiderError):
    """Error raised when request times out"""
    pass

class ParserError(PySpiderError):
    """Error raised when parsing fails"""
    pass

class ValidationError(PySpiderError):
    """Error raised when data validation fails"""
    pass

class AuthenticationError(PySpiderError):
    """Error raised when authentication fails"""
    pass

class RateLimitError(PySpiderError):
    """Error raised when rate limit is exceeded"""
    pass

class ProxyError(PySpiderError):
    """Error raised when proxy fails"""
    pass

class CaptchaError(PySpiderError):
    """Error raised when captcha solving fails"""
    pass

class DataError(PySpiderError):
    """Error raised when data processing fails"""
    pass

class ResourceError(PySpiderError):
    """Error raised when resource allocation fails"""
    pass

class ConfigurationError(PySpiderError):
    """Error raised when configuration is invalid"""
    pass
