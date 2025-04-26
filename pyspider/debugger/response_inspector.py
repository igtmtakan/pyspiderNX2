#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-30 10:00:00

"""
Response Inspector for PySpider
"""

import json
import logging
import time
import uuid
import re
from typing import Dict, List, Any, Optional, Union
from difflib import Differ, HtmlDiff

logger = logging.getLogger('debugger.response_inspector')

class ResponseInspector:
    """Response inspector for PySpider"""
    
    def __init__(self):
        self.responses = {}
        self.max_responses = 100
    
    def inspect_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Inspect a response"""
        # Generate response ID
        response_id = str(uuid.uuid4())
        
        # Parse headers
        headers = response.get('headers', {})
        
        # Parse cookies
        cookies = {}
        set_cookie_headers = headers.get('Set-Cookie', [])
        if not isinstance(set_cookie_headers, list):
            set_cookie_headers = [set_cookie_headers]
        
        for cookie_str in set_cookie_headers:
            if '=' in cookie_str:
                parts = cookie_str.split(';')
                name_value = parts[0].strip()
                name, value = name_value.split('=', 1)
                
                cookie_info = {
                    'value': value,
                    'attributes': {}
                }
                
                for part in parts[1:]:
                    part = part.strip()
                    if '=' in part:
                        attr_name, attr_value = part.split('=', 1)
                        cookie_info['attributes'][attr_name.lower()] = attr_value
                    else:
                        cookie_info['attributes'][part.lower()] = True
                
                cookies[name] = cookie_info
        
        # Parse body
        body = response.get('content', '')
        body_parsed = None
        content_type = headers.get('Content-Type', '').lower()
        
        if content_type.startswith('application/json'):
            try:
                body_parsed = json.loads(body) if body else None
            except Exception as e:
                logger.warning(f"Failed to parse JSON body: {e}")
        
        # Extract links from HTML
        links = []
        if content_type.startswith('text/html'):
            try:
                # Simple regex to extract links
                href_pattern = re.compile(r'<a[^>]+href=["\'](.*?)["\']', re.IGNORECASE)
                src_pattern = re.compile(r'<(?:img|script|link)[^>]+(?:src|href)=["\'](.*?)["\']', re.IGNORECASE)
                
                links.extend(href_pattern.findall(body))
                links.extend(src_pattern.findall(body))
                
                # Remove duplicates
                links = list(set(links))
            except Exception as e:
                logger.warning(f"Failed to extract links: {e}")
        
        # Create inspection result
        inspection = {
            'id': response_id,
            'timestamp': time.time(),
            'url': response.get('url', ''),
            'status_code': response.get('status_code', 200),
            'headers': headers,
            'cookies': cookies,
            'body': body,
            'body_parsed': body_parsed,
            'size': len(body) if body else 0,
            'content_type': content_type,
            'time': response.get('time', 0),
            'links': links
        }
        
        # Store inspection
        self.responses[response_id] = inspection
        
        # Limit the number of stored responses
        if len(self.responses) > self.max_responses:
            oldest_id = min(self.responses.keys(), key=lambda k: self.responses[k]['timestamp'])
            del self.responses[oldest_id]
        
        return inspection
    
    def get_response(self, response_id: str) -> Optional[Dict[str, Any]]:
        """Get response inspection"""
        if response_id not in self.responses:
            return None
        
        return self.responses[response_id]
    
    def get_all_responses(self) -> List[Dict[str, Any]]:
        """Get all response inspections"""
        result = list(self.responses.values())
        
        # Sort by timestamp (newest first)
        result.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return result
    
    def clear_all(self):
        """Clear all inspections"""
        self.responses = {}
    
    def delete_response(self, response_id: str) -> bool:
        """Delete a response inspection"""
        if response_id not in self.responses:
            return False
        
        del self.responses[response_id]
        return True
    
    def compare_responses(self, response_id1: str, response_id2: str) -> Dict[str, Any]:
        """Compare two responses"""
        response1 = self.get_response(response_id1)
        response2 = self.get_response(response_id2)
        
        if not response1 or not response2:
            return {
                'error': 'One or both responses not found'
            }
        
        # Compare status codes
        status_diff = response1['status_code'] == response2['status_code']
        
        # Compare headers
        headers1 = set(response1['headers'].keys())
        headers2 = set(response2['headers'].keys())
        common_headers = headers1.intersection(headers2)
        headers1_only = headers1 - headers2
        headers2_only = headers2 - headers1
        
        header_diffs = {}
        for header in common_headers:
            if response1['headers'][header] != response2['headers'][header]:
                header_diffs[header] = {
                    'response1': response1['headers'][header],
                    'response2': response2['headers'][header]
                }
        
        # Compare body
        body_diff = None
        if response1['body'] != response2['body']:
            differ = Differ()
            body1_lines = response1['body'].splitlines()
            body2_lines = response2['body'].splitlines()
            
            # Generate line-by-line diff
            diff = list(differ.compare(body1_lines, body2_lines))
            
            # Generate HTML diff for visualization
            html_diff = HtmlDiff().make_table(body1_lines, body2_lines)
            
            body_diff = {
                'diff': diff,
                'html_diff': html_diff
            }
        
        # Compare size
        size_diff = response1['size'] - response2['size']
        
        # Compare time
        time_diff = response1['time'] - response2['time']
        
        return {
            'response1': {
                'id': response_id1,
                'url': response1['url'],
                'status_code': response1['status_code'],
                'size': response1['size'],
                'time': response1['time']
            },
            'response2': {
                'id': response_id2,
                'url': response2['url'],
                'status_code': response2['status_code'],
                'size': response2['size'],
                'time': response2['time']
            },
            'status_same': status_diff,
            'headers1_only': list(headers1_only),
            'headers2_only': list(headers2_only),
            'header_diffs': header_diffs,
            'body_diff': body_diff,
            'size_diff': size_diff,
            'time_diff': time_diff
        }
    
    def extract_data(self, response_id: str, extractor_type: str, extractor_params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from a response"""
        response = self.get_response(response_id)
        
        if not response:
            return {
                'error': 'Response not found'
            }
        
        body = response['body']
        
        if extractor_type == 'regex':
            pattern = extractor_params.get('pattern', '')
            flags = 0
            if extractor_params.get('case_insensitive', False):
                flags |= re.IGNORECASE
            if extractor_params.get('multiline', False):
                flags |= re.MULTILINE
            if extractor_params.get('dotall', False):
                flags |= re.DOTALL
            
            try:
                matches = re.findall(pattern, body, flags)
                return {
                    'success': True,
                    'matches': matches,
                    'count': len(matches)
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        
        elif extractor_type == 'xpath':
            xpath = extractor_params.get('xpath', '')
            
            try:
                from lxml import etree
                
                # Parse HTML
                parser = etree.HTMLParser()
                tree = etree.fromstring(body, parser)
                
                # Execute XPath
                results = tree.xpath(xpath)
                
                # Convert results to strings
                string_results = []
                for result in results:
                    if isinstance(result, etree._Element):
                        string_results.append(etree.tostring(result, encoding='unicode'))
                    else:
                        string_results.append(str(result))
                
                return {
                    'success': True,
                    'matches': string_results,
                    'count': len(string_results)
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        
        elif extractor_type == 'css':
            css = extractor_params.get('css', '')
            
            try:
                from pyquery import PyQuery
                
                # Parse HTML
                pq = PyQuery(body)
                
                # Execute CSS selector
                results = pq(css)
                
                # Convert results to strings
                string_results = []
                for i in range(len(results)):
                    string_results.append(results.eq(i).outer_html())
                
                return {
                    'success': True,
                    'matches': string_results,
                    'count': len(string_results)
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        
        elif extractor_type == 'json':
            json_path = extractor_params.get('path', '')
            
            try:
                # Parse JSON
                data = json.loads(body)
                
                # Simple JSON path implementation
                if not json_path:
                    return {
                        'success': True,
                        'result': data
                    }
                
                # Split path by dots
                parts = json_path.split('.')
                current = data
                
                for part in parts:
                    # Handle array indexing
                    if '[' in part and part.endswith(']'):
                        name, index_str = part.split('[', 1)
                        index = int(index_str[:-1])
                        
                        if name:
                            current = current[name]
                        
                        current = current[index]
                    else:
                        current = current[part]
                
                return {
                    'success': True,
                    'result': current
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        
        else:
            return {
                'success': False,
                'error': f"Unknown extractor type: {extractor_type}"
            }
