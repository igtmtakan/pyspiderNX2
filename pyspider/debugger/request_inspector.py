#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-30 10:00:00

"""
Request Inspector for PySpider
"""

import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

logger = logging.getLogger('debugger.request_inspector')

class RequestInspector:
    """Request inspector for PySpider"""
    
    def __init__(self):
        self.requests = {}
        self.max_requests = 100
    
    def inspect_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Inspect a request"""
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Parse URL
        url = request.get('url', '')
        parsed_url = urlparse(url)
        
        # Parse query parameters
        query_params = parse_qsl(parsed_url.query)
        
        # Parse headers
        headers = request.get('headers', {})
        
        # Parse cookies
        cookies = {}
        if 'Cookie' in headers:
            cookie_str = headers['Cookie']
            for cookie in cookie_str.split(';'):
                if '=' in cookie:
                    name, value = cookie.strip().split('=', 1)
                    cookies[name] = value
        
        # Parse body
        body = request.get('data', '')
        body_parsed = None
        content_type = headers.get('Content-Type', '').lower()
        
        if content_type.startswith('application/json'):
            try:
                body_parsed = json.loads(body) if body else None
            except Exception as e:
                logger.warning(f"Failed to parse JSON body: {e}")
        elif content_type.startswith('application/x-www-form-urlencoded'):
            try:
                body_parsed = dict(parse_qsl(body))
            except Exception as e:
                logger.warning(f"Failed to parse form data: {e}")
        elif content_type.startswith('multipart/form-data'):
            body_parsed = "<multipart form data>"
        
        # Create inspection result
        inspection = {
            'id': request_id,
            'timestamp': time.time(),
            'method': request.get('method', 'GET'),
            'url': url,
            'scheme': parsed_url.scheme,
            'host': parsed_url.netloc,
            'path': parsed_url.path,
            'query_string': parsed_url.query,
            'query_params': query_params,
            'headers': headers,
            'cookies': cookies,
            'body': body,
            'body_parsed': body_parsed,
            'size': len(body) if body else 0,
            'content_type': content_type
        }
        
        # Store inspection
        self.requests[request_id] = {
            'request': inspection,
            'response': None
        }
        
        # Limit the number of stored requests
        if len(self.requests) > self.max_requests:
            oldest_id = min(self.requests.keys(), key=lambda k: self.requests[k]['request']['timestamp'])
            del self.requests[oldest_id]
        
        return inspection
    
    def inspect_response(self, response: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Inspect a response"""
        # Generate response ID if not provided
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Parse headers
        headers = response.get('headers', {})
        
        # Parse cookies
        cookies = {}
        if 'Set-Cookie' in headers:
            cookie_str = headers['Set-Cookie']
            for cookie in cookie_str.split(';'):
                if '=' in cookie:
                    name, value = cookie.strip().split('=', 1)
                    cookies[name] = value
        
        # Parse body
        body = response.get('content', '')
        body_parsed = None
        content_type = headers.get('Content-Type', '').lower()
        
        if content_type.startswith('application/json'):
            try:
                body_parsed = json.loads(body) if body else None
            except Exception as e:
                logger.warning(f"Failed to parse JSON body: {e}")
        elif content_type.startswith('text/html'):
            body_parsed = "<html content>"
        elif content_type.startswith('text/xml') or content_type.startswith('application/xml'):
            body_parsed = "<xml content>"
        
        # Create inspection result
        inspection = {
            'id': request_id,
            'timestamp': time.time(),
            'status_code': response.get('status_code', 200),
            'headers': headers,
            'cookies': cookies,
            'body': body,
            'body_parsed': body_parsed,
            'size': len(body) if body else 0,
            'content_type': content_type,
            'time': response.get('time', 0)
        }
        
        # Store inspection
        if request_id in self.requests:
            self.requests[request_id]['response'] = inspection
        else:
            self.requests[request_id] = {
                'request': None,
                'response': inspection
            }
        
        return inspection
    
    def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get request inspection"""
        if request_id not in self.requests:
            return None
        
        return self.requests[request_id]['request']
    
    def get_response(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get response inspection"""
        if request_id not in self.requests:
            return None
        
        return self.requests[request_id]['response']
    
    def get_request_response(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get request and response inspection"""
        if request_id not in self.requests:
            return None
        
        return self.requests[request_id]
    
    def get_all_requests(self) -> List[Dict[str, Any]]:
        """Get all request inspections"""
        result = []
        for request_id, data in self.requests.items():
            if data['request']:
                result.append(data['request'])
        
        # Sort by timestamp (newest first)
        result.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return result
    
    def get_all_responses(self) -> List[Dict[str, Any]]:
        """Get all response inspections"""
        result = []
        for request_id, data in self.requests.items():
            if data['response']:
                result.append(data['response'])
        
        # Sort by timestamp (newest first)
        result.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return result
    
    def get_all_request_responses(self) -> List[Dict[str, Any]]:
        """Get all request and response inspections"""
        result = []
        for request_id, data in self.requests.items():
            result.append({
                'id': request_id,
                'request': data['request'],
                'response': data['response']
            })
        
        # Sort by timestamp (newest first)
        result.sort(key=lambda x: x['request']['timestamp'] if x['request'] else (x['response']['timestamp'] if x['response'] else 0), reverse=True)
        
        return result
    
    def clear_all(self):
        """Clear all inspections"""
        self.requests = {}
    
    def delete_request(self, request_id: str) -> bool:
        """Delete a request inspection"""
        if request_id not in self.requests:
            return False
        
        del self.requests[request_id]
        return True
    
    def modify_request(self, request_id: str, modifications: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Modify a request for resending"""
        if request_id not in self.requests or not self.requests[request_id]['request']:
            return None
        
        # Get original request
        original = self.requests[request_id]['request']
        
        # Create a copy
        modified = dict(original)
        
        # Apply modifications
        if 'method' in modifications:
            modified['method'] = modifications['method']
        
        if 'url' in modifications:
            modified['url'] = modifications['url']
            # Update parsed URL components
            parsed_url = urlparse(modifications['url'])
            modified['scheme'] = parsed_url.scheme
            modified['host'] = parsed_url.netloc
            modified['path'] = parsed_url.path
            modified['query_string'] = parsed_url.query
            modified['query_params'] = parse_qsl(parsed_url.query)
        
        if 'query_params' in modifications:
            # Update query parameters
            query_params = modifications['query_params']
            modified['query_params'] = query_params
            
            # Rebuild URL
            parsed_url = urlparse(modified['url'])
            new_query = urlencode(query_params)
            modified['query_string'] = new_query
            modified['url'] = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query,
                parsed_url.fragment
            ))
        
        if 'headers' in modifications:
            modified['headers'] = modifications['headers']
        
        if 'cookies' in modifications:
            modified['cookies'] = modifications['cookies']
            
            # Update Cookie header
            cookie_str = '; '.join([f"{name}={value}" for name, value in modifications['cookies'].items()])
            if cookie_str:
                modified['headers']['Cookie'] = cookie_str
            elif 'Cookie' in modified['headers']:
                del modified['headers']['Cookie']
        
        if 'body' in modifications:
            modified['body'] = modifications['body']
            modified['size'] = len(modifications['body']) if modifications['body'] else 0
            
            # Update Content-Length header
            if modified['size'] > 0:
                modified['headers']['Content-Length'] = str(modified['size'])
            elif 'Content-Length' in modified['headers']:
                del modified['headers']['Content-Length']
        
        return modified
    
    def resend_request(self, request_id: str, modifications: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Resend a request with optional modifications"""
        # Get modified request
        if modifications:
            request = self.modify_request(request_id, modifications)
        else:
            request = self.get_request(request_id)
        
        if not request:
            return None
        
        # Convert to PySpider request format
        pyspider_request = {
            'url': request['url'],
            'method': request['method'],
            'headers': request['headers'],
            'data': request['body']
        }
        
        # Inspect the new request
        new_request = self.inspect_request(pyspider_request)
        
        return new_request
