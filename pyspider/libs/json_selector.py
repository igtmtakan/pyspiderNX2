#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-26 10:00:00

import json
import logging
from typing import List, Dict, Union, Optional, Any, Tuple

import jmespath
from jsonpath_ng import parse as jsonpath_parse
from jsonpath_ng.exceptions import JsonPathParserError

logger = logging.getLogger('json_selector')

class JsonSelector:
    """
    JSON selector for flexible data extraction using JSONPath and JMESPath
    """
    
    def __init__(self, response=None, json_data=None):
        """
        Initialize the selector with response or JSON data
        
        Args:
            response: PySpider response object
            json_data: JSON data as dict or list
        """
        self.response = response
        self._json_data = json_data
        
        if response:
            try:
                self._json_data = response.json
            except Exception as e:
                logger.error(f"Error initializing JSON selector from response: {e}")
                self._json_data = None
    
    @property
    def json_data(self):
        """Get JSON data"""
        return self._json_data
    
    def jsonpath(self, path: str, default: Any = None) -> List[Any]:
        """
        Extract data using JSONPath
        
        Args:
            path: JSONPath expression
            default: Default value if not found
            
        Returns:
            List of extracted data
        """
        if not self._json_data:
            return default
        
        try:
            jsonpath_expr = jsonpath_parse(path)
            matches = jsonpath_expr.find(self._json_data)
            
            if not matches:
                return default
            
            return [match.value for match in matches]
        except JsonPathParserError as e:
            logger.error(f"Error parsing JSONPath '{path}': {e}")
            return default
        except Exception as e:
            logger.error(f"Error in JSONPath '{path}': {e}")
            return default
    
    def jsonpath_first(self, path: str, default: Any = None) -> Any:
        """
        Extract first element using JSONPath
        
        Args:
            path: JSONPath expression
            default: Default value if not found
            
        Returns:
            Extracted data
        """
        result = self.jsonpath(path, [default])
        return result[0] if result else default
    
    def jsonpath_value(self, path: str, default: Any = None) -> Any:
        """
        Extract value using JSONPath and return the raw value
        
        Args:
            path: JSONPath expression
            default: Default value if not found
            
        Returns:
            Extracted value
        """
        result = self.jsonpath(path)
        if not result:
            return default
        
        # If result is a list with a single item, return that item
        if len(result) == 1:
            return result[0]
        
        # Otherwise return the whole list
        return result
    
    def jmespath(self, path: str, default: Any = None) -> Any:
        """
        Extract data using JMESPath
        
        Args:
            path: JMESPath expression
            default: Default value if not found
            
        Returns:
            Extracted data
        """
        if not self._json_data:
            return default
        
        try:
            result = jmespath.search(path, self._json_data)
            
            if result is None:
                return default
            
            return result
        except jmespath.exceptions.ParseError as e:
            logger.error(f"Error parsing JMESPath '{path}': {e}")
            return default
        except Exception as e:
            logger.error(f"Error in JMESPath '{path}': {e}")
            return default
    
    def select(self, selectors: List[Dict], default: Any = None) -> Any:
        """
        Try multiple selectors in order until one succeeds
        
        Args:
            selectors: List of selector configurations
                [
                    {'type': 'jsonpath', 'path': '$.store.book[*].author'},
                    {'type': 'jmespath', 'path': 'store.book[*].author'}
                ]
            default: Default value if all selectors fail
            
        Returns:
            Extracted data
        """
        for selector in selectors:
            selector_type = selector.get('type', 'jsonpath')
            
            if selector_type == 'jsonpath':
                result = self.jsonpath_value(
                    selector.get('path', ''), 
                    None
                )
            elif selector_type == 'jmespath':
                result = self.jmespath(
                    selector.get('path', ''), 
                    None
                )
            else:
                logger.warning(f"Unknown selector type: {selector_type}")
                continue
            
            if result is not None:
                return result
        
        return default
    
    def extract_keys(self, path: str = None) -> List[str]:
        """
        Extract keys from JSON object at the given path
        
        Args:
            path: JSONPath expression to locate the object, None for root
            
        Returns:
            List of keys
        """
        if not self._json_data:
            return []
        
        try:
            if path:
                obj = self.jsonpath_value(path)
            else:
                obj = self._json_data
            
            if not obj:
                return []
            
            # If result is a list, get keys from the first item
            if isinstance(obj, list):
                if not obj or not isinstance(obj[0], dict):
                    return []
                return list(obj[0].keys())
            
            # If result is a dict, get its keys
            if isinstance(obj, dict):
                return list(obj.keys())
            
            return []
        except Exception as e:
            logger.error(f"Error extracting keys: {e}")
            return []
    
    def extract_values(self, key: str, path: str = None) -> List[Any]:
        """
        Extract values for a specific key from JSON objects
        
        Args:
            key: Key to extract values for
            path: JSONPath expression to locate the objects, None for root
            
        Returns:
            List of values
        """
        if not self._json_data:
            return []
        
        try:
            if path:
                objects = self.jsonpath_value(path)
            else:
                objects = self._json_data
            
            if not objects:
                return []
            
            # Ensure objects is a list
            if not isinstance(objects, list):
                objects = [objects]
            
            # Extract values for the key
            result = []
            for obj in objects:
                if isinstance(obj, dict) and key in obj:
                    result.append(obj[key])
            
            return result
        except Exception as e:
            logger.error(f"Error extracting values: {e}")
            return []
    
    def flatten(self, path: str = None) -> List[Dict]:
        """
        Flatten nested JSON objects into a list of flat dictionaries
        
        Args:
            path: JSONPath expression to locate the objects, None for root
            
        Returns:
            List of flattened dictionaries
        """
        if not self._json_data:
            return []
        
        try:
            if path:
                objects = self.jsonpath_value(path)
            else:
                objects = self._json_data
            
            if not objects:
                return []
            
            # Ensure objects is a list
            if not isinstance(objects, list):
                objects = [objects]
            
            # Flatten objects
            result = []
            for obj in objects:
                if isinstance(obj, dict):
                    flat_obj = self._flatten_dict(obj)
                    result.append(flat_obj)
            
            return result
        except Exception as e:
            logger.error(f"Error flattening objects: {e}")
            return []
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """
        Flatten a nested dictionary
        
        Args:
            d: Dictionary to flatten
            parent_key: Parent key for nested dictionaries
            sep: Separator for keys
            
        Returns:
            Flattened dictionary
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            elif isinstance(v, list):
                # For lists, create entries with index in the key
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(self._flatten_dict(item, f"{new_key}[{i}]", sep).items())
                    else:
                        items.append((f"{new_key}[{i}]", item))
            else:
                items.append((new_key, v))
        
        return dict(items)
    
    def to_json_string(self, obj: Any = None, indent: int = None) -> str:
        """
        Convert object to JSON string
        
        Args:
            obj: Object to convert, None for the entire JSON data
            indent: Indentation level for pretty printing
            
        Returns:
            JSON string
        """
        if obj is None:
            obj = self._json_data
        
        if obj is None:
            return "{}"
        
        try:
            return json.dumps(obj, indent=indent, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error converting to JSON string: {e}")
            return "{}"
