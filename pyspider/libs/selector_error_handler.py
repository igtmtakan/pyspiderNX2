#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-27 13:00:00

import re
import logging
import difflib
import traceback
from typing import List, Dict, Union, Optional, Any, Tuple

logger = logging.getLogger('selector_error_handler')

class SelectorError(Exception):
    """Base class for selector errors"""
    
    def __init__(self, message, selector=None, selector_type=None, details=None, suggestions=None):
        self.message = message
        self.selector = selector
        self.selector_type = selector_type
        self.details = details or {}
        self.suggestions = suggestions or []
        super().__init__(message)
    
    def __str__(self):
        result = f"{self.message}"
        if self.selector:
            result += f" (selector: {self.selector})"
        if self.selector_type:
            result += f" (type: {self.selector_type})"
        if self.suggestions:
            result += f"\nSuggestions: {', '.join(self.suggestions)}"
        return result

class SelectorSyntaxError(SelectorError):
    """Error for selector syntax issues"""
    pass

class SelectorNotFoundError(SelectorError):
    """Error for selectors that don't match any elements"""
    pass

class SelectorTypeError(SelectorError):
    """Error for invalid selector types"""
    pass

class SelectorAttributeError(SelectorError):
    """Error for attribute access issues"""
    pass

class SelectorErrorHandler:
    """
    Error handler for selector operations
    """
    
    def __init__(self, response=None):
        """
        Initialize the error handler with response
        
        Args:
            response: PySpider response object
        """
        self.response = response
        self._error_history = []
        self._max_history = 100
    
    def handle_error(self, error: Exception, selector: str = None, selector_type: str = None) -> SelectorError:
        """
        Handle a selector error
        
        Args:
            error: Original exception
            selector: Selector string
            selector_type: Selector type
            
        Returns:
            SelectorError object
        """
        # Get error details
        error_type = type(error).__name__
        error_message = str(error)
        error_traceback = traceback.format_exc()
        
        # Create error details
        details = {
            'error_type': error_type,
            'error_message': error_message,
            'error_traceback': error_traceback
        }
        
        # Create selector error based on error type
        selector_error = None
        
        if 'syntax' in error_message.lower() or 'parse' in error_message.lower():
            suggestions = self._suggest_syntax_fix(selector, selector_type, error_message)
            selector_error = SelectorSyntaxError(
                f"Syntax error in {selector_type} selector: {error_message}",
                selector=selector,
                selector_type=selector_type,
                details=details,
                suggestions=suggestions
            )
        elif 'not found' in error_message.lower() or 'no matches' in error_message.lower():
            suggestions = self._suggest_alternative_selectors(selector, selector_type)
            selector_error = SelectorNotFoundError(
                f"No elements found for {selector_type} selector: {error_message}",
                selector=selector,
                selector_type=selector_type,
                details=details,
                suggestions=suggestions
            )
        elif 'attribute' in error_message.lower():
            suggestions = self._suggest_attribute_fix(selector, selector_type, error_message)
            selector_error = SelectorAttributeError(
                f"Attribute error in {selector_type} selector: {error_message}",
                selector=selector,
                selector_type=selector_type,
                details=details,
                suggestions=suggestions
            )
        elif 'type' in error_message.lower():
            suggestions = self._suggest_type_fix(selector_type)
            selector_error = SelectorTypeError(
                f"Invalid selector type: {error_message}",
                selector=selector,
                selector_type=selector_type,
                details=details,
                suggestions=suggestions
            )
        else:
            suggestions = self._suggest_general_fix(selector, selector_type, error_message)
            selector_error = SelectorError(
                f"Error in {selector_type} selector: {error_message}",
                selector=selector,
                selector_type=selector_type,
                details=details,
                suggestions=suggestions
            )
        
        # Add to error history
        self._add_to_history(selector_error)
        
        return selector_error
    
    def _add_to_history(self, error: SelectorError):
        """
        Add error to history
        
        Args:
            error: SelectorError object
        """
        self._error_history.append(error)
        
        # Limit history size
        if len(self._error_history) > self._max_history:
            self._error_history = self._error_history[-self._max_history:]
    
    def get_error_history(self) -> List[SelectorError]:
        """
        Get error history
        
        Returns:
            List of SelectorError objects
        """
        return self._error_history
    
    def clear_error_history(self):
        """Clear error history"""
        self._error_history = []
    
    def _suggest_syntax_fix(self, selector: str, selector_type: str, error_message: str) -> List[str]:
        """
        Suggest fixes for syntax errors
        
        Args:
            selector: Selector string
            selector_type: Selector type
            error_message: Error message
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        if selector_type == 'css':
            # Check for common CSS syntax errors
            if '{' in selector or '}' in selector:
                suggestions.append("Remove CSS style braces {} from selector")
            if ':' in selector and not any(pseudo in selector for pseudo in ['first-child', 'last-child', 'nth-child', 'not']):
                suggestions.append("Check pseudo-class syntax, use :: for pseudo-elements")
            if '[' in selector and ']' not in selector:
                suggestions.append("Missing closing bracket ] in attribute selector")
            if '(' in selector and ')' not in selector:
                suggestions.append("Missing closing parenthesis ) in selector")
            
            # Suggest CSS4 selector
            suggestions.append("Try using CSS4 selector type for advanced CSS selectors")
        
        elif selector_type == 'xpath':
            # Check for common XPath syntax errors
            if '//' not in selector and not selector.startswith('.'):
                suggestions.append("XPath should usually start with // for absolute path or . for relative path")
            if '[' in selector and ']' not in selector:
                suggestions.append("Missing closing bracket ] in predicate")
            if '(' in selector and ')' not in selector:
                suggestions.append("Missing closing parenthesis ) in function")
            if '@' in selector and not re.search(r'@[\w-]+', selector):
                suggestions.append("Check attribute syntax, should be @attribute-name")
            
            # Suggest XQuery
            suggestions.append("Try using XQuery for more complex XML queries")
        
        elif selector_type == 'jsonpath':
            # Check for common JSONPath syntax errors
            if not selector.startswith('$'):
                suggestions.append("JSONPath should start with $ to represent the root object")
            if '[' in selector and ']' not in selector:
                suggestions.append("Missing closing bracket ] in array index or filter")
            if '(' in selector and ')' not in selector:
                suggestions.append("Missing closing parenthesis ) in function or filter")
            
            # Suggest JMESPath
            suggestions.append("Try using JMESPath for a more standardized JSON query language")
        
        elif selector_type == 'jmespath':
            # Check for common JMESPath syntax errors
            if '[' in selector and ']' not in selector:
                suggestions.append("Missing closing bracket ] in array index or filter")
            if '{' in selector and '}' not in selector:
                suggestions.append("Missing closing brace } in multiselect hash")
            if '(' in selector and ')' not in selector:
                suggestions.append("Missing closing parenthesis ) in function")
            
            # Suggest JSONPath
            suggestions.append("Try using JSONPath for more flexible JSON queries")
        
        elif selector_type == 'regex':
            # Check for common regex syntax errors
            if '(' in selector and ')' not in selector:
                suggestions.append("Missing closing parenthesis ) in capturing group")
            if '[' in selector and ']' not in selector:
                suggestions.append("Missing closing bracket ] in character class")
            if '{' in selector and '}' not in selector:
                suggestions.append("Missing closing brace } in quantifier")
            if '\\' in selector:
                suggestions.append("Check escape sequences, use raw strings r'pattern' for regex")
            
            # Suggest other selector types
            suggestions.append("Try using CSS or XPath selectors for HTML parsing")
        
        # Add general suggestions
        suggestions.append("Check for typos in the selector")
        suggestions.append("Simplify the selector and build it up gradually")
        
        return suggestions
    
    def _suggest_alternative_selectors(self, selector: str, selector_type: str) -> List[str]:
        """
        Suggest alternative selectors when no elements are found
        
        Args:
            selector: Selector string
            selector_type: Selector type
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        if not self.response:
            suggestions.append("Response object not available for analysis")
            return suggestions
        
        if selector_type == 'css':
            # Suggest more general CSS selectors
            parts = selector.split(' ')
            if len(parts) > 1:
                suggestions.append(f"Try a more general selector: '{parts[-1]}'")
            
            # Suggest case-insensitive selector
            if selector.lower() != selector:
                suggestions.append(f"Try case-insensitive selector: '{selector.lower()}'")
            
            # Suggest XPath alternative
            if '#' in selector:
                # ID selector
                id_value = selector.split('#')[1].split(' ')[0].split('.')[0]
                suggestions.append(f"Try XPath: '//[@id=\"{id_value}\"]'")
            elif '.' in selector:
                # Class selector
                class_value = selector.split('.')[1].split(' ')[0]
                suggestions.append(f"Try XPath: '//*[contains(@class, \"{class_value}\")]'")
            else:
                # Tag selector
                tag = selector.split(' ')[0].split('[')[0].split(':')[0]
                suggestions.append(f"Try XPath: '//{tag}'")
        
        elif selector_type == 'xpath':
            # Suggest more general XPath selectors
            if '//' in selector:
                parts = selector.split('//')
                if len(parts) > 1:
                    tag = parts[1].split('[')[0].split('/')[0]
                    suggestions.append(f"Try a more general XPath: '//{tag}'")
            
            # Suggest case-insensitive XPath
            if '@' in selector and '=' in selector:
                suggestions.append("Try case-insensitive comparison: 'translate(@attr, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'value''")
            
            # Suggest CSS alternative
            if '@id' in selector:
                # ID selector
                match = re.search(r'@id\s*=\s*[\'"]([^\'"]+)[\'"]', selector)
                if match:
                    id_value = match.group(1)
                    suggestions.append(f"Try CSS: '#{id_value}'")
            elif '@class' in selector:
                # Class selector
                match = re.search(r'contains\(@class\s*,\s*[\'"]([^\'"]+)[\'"]', selector)
                if match:
                    class_value = match.group(1)
                    suggestions.append(f"Try CSS: '.{class_value}'")
            else:
                # Tag selector
                match = re.search(r'//([a-zA-Z0-9_-]+)', selector)
                if match:
                    tag = match.group(1)
                    suggestions.append(f"Try CSS: '{tag}'")
        
        elif selector_type == 'jsonpath':
            # Suggest more general JSONPath selectors
            if '.' in selector:
                parts = selector.split('.')
                if len(parts) > 1:
                    suggestions.append(f"Try a more general JSONPath: '{'.'.join(parts[:-1])}'")
            
            # Suggest JMESPath alternative
            if selector.startswith('$'):
                jmespath_selector = selector[1:]
                if jmespath_selector.startswith('.'):
                    jmespath_selector = jmespath_selector[1:]
                suggestions.append(f"Try JMESPath: '{jmespath_selector}'")
        
        elif selector_type == 'jmespath':
            # Suggest more general JMESPath selectors
            if '.' in selector:
                parts = selector.split('.')
                if len(parts) > 1:
                    suggestions.append(f"Try a more general JMESPath: '{'.'.join(parts[:-1])}'")
            
            # Suggest JSONPath alternative
            jsonpath_selector = '$'
            if selector:
                jsonpath_selector += '.' + selector
            suggestions.append(f"Try JSONPath: '{jsonpath_selector}'")
        
        # Add general suggestions
        suggestions.append("Check if the content is loaded dynamically with JavaScript")
        suggestions.append("Inspect the page source to verify the element exists")
        suggestions.append("Try a different selector type")
        
        return suggestions
    
    def _suggest_attribute_fix(self, selector: str, selector_type: str, error_message: str) -> List[str]:
        """
        Suggest fixes for attribute errors
        
        Args:
            selector: Selector string
            selector_type: Selector type
            error_message: Error message
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        if selector_type == 'css':
            # Check for common attribute issues in CSS
            if '@' in selector:
                suggestions.append("CSS uses [attr=value] syntax, not @attr")
            
            # Suggest alternative attributes
            if 'href' in error_message:
                suggestions.append("Try 'src' attribute instead of 'href' for images, scripts, etc.")
            elif 'src' in error_message:
                suggestions.append("Try 'href' attribute instead of 'src' for links")
            elif 'class' in error_message:
                suggestions.append("Try 'className' attribute in some contexts")
            elif 'text' in error_message:
                suggestions.append("Use 'textContent' or 'innerText' instead of 'text' for element text")
            
            # Suggest not using attribute
            suggestions.append("Try without specifying an attribute to get the text content")
        
        elif selector_type == 'xpath':
            # Check for common attribute issues in XPath
            if '[' in selector and '@' not in selector and 'text()' not in selector:
                suggestions.append("Use @ prefix for attributes in XPath predicates")
            
            # Suggest alternative attributes
            if 'href' in error_message:
                suggestions.append("Try '@src' attribute instead of '@href' for images, scripts, etc.")
            elif 'src' in error_message:
                suggestions.append("Try '@href' attribute instead of '@src' for links")
            
            # Suggest text() function
            suggestions.append("Use 'text()' function to get the text content")
        
        # Add general suggestions
        suggestions.append("Check the HTML source to verify the attribute exists")
        suggestions.append("Try selecting the element first, then access the attribute separately")
        
        return suggestions
    
    def _suggest_type_fix(self, selector_type: str) -> List[str]:
        """
        Suggest fixes for type errors
        
        Args:
            selector_type: Selector type
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Suggest valid selector types
        valid_types = ['css', 'xpath', 'regex', 'css4', 'jsonpath', 'jmespath', 'graphql', 'xquery']
        
        if selector_type not in valid_types:
            closest_matches = difflib.get_close_matches(selector_type, valid_types, n=3, cutoff=0.6)
            
            if closest_matches:
                for match in closest_matches:
                    suggestions.append(f"Did you mean '{match}'?")
            
            suggestions.append(f"Valid selector types: {', '.join(valid_types)}")
        else:
            # Suggest alternative selector types
            if selector_type == 'css':
                suggestions.append("Try 'xpath' for more powerful HTML/XML queries")
                suggestions.append("Try 'css4' for advanced CSS selectors")
            elif selector_type == 'xpath':
                suggestions.append("Try 'css' for simpler HTML queries")
                suggestions.append("Try 'xquery' for more powerful XML queries")
            elif selector_type == 'jsonpath':
                suggestions.append("Try 'jmespath' for a more standardized JSON query language")
            elif selector_type == 'jmespath':
                suggestions.append("Try 'jsonpath' for more flexible JSON queries")
        
        return suggestions
    
    def _suggest_general_fix(self, selector: str, selector_type: str, error_message: str) -> List[str]:
        """
        Suggest general fixes for errors
        
        Args:
            selector: Selector string
            selector_type: Selector type
            error_message: Error message
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Add general suggestions
        suggestions.append("Check the selector syntax")
        suggestions.append("Simplify the selector and build it up gradually")
        suggestions.append("Try a different selector type")
        suggestions.append("Check if the content is loaded dynamically with JavaScript")
        suggestions.append("Inspect the page source to verify the element exists")
        
        return suggestions
    
    def auto_fix_selector(self, selector: str, selector_type: str) -> Tuple[str, str]:
        """
        Attempt to automatically fix a selector
        
        Args:
            selector: Selector string
            selector_type: Selector type
            
        Returns:
            Tuple of (fixed_selector, fixed_selector_type)
        """
        fixed_selector = selector
        fixed_selector_type = selector_type
        
        if selector_type == 'css':
            # Fix common CSS syntax errors
            if '{' in selector or '}' in selector:
                fixed_selector = re.sub(r'\{[^}]*\}', '', selector)
            
            # Check if it's an advanced CSS selector
            advanced_css_features = [
                ':not', ':first-of-type', ':last-of-type', ':nth-of-type',
                ':nth-last-of-type', ':only-of-type', ':empty', ':checked',
                ':enabled', ':disabled', ':target', ':scope'
            ]
            
            if any(feature in selector for feature in advanced_css_features):
                fixed_selector_type = 'css4'
        
        elif selector_type == 'xpath':
            # Fix common XPath syntax errors
            if not selector.startswith('/') and not selector.startswith('.'):
                fixed_selector = '//' + selector
            
            # Balance brackets and parentheses
            if selector.count('[') > selector.count(']'):
                fixed_selector += ']' * (selector.count('[') - selector.count(']'))
            if selector.count('(') > selector.count(')'):
                fixed_selector += ')' * (selector.count('(') - selector.count(')'))
        
        elif selector_type == 'jsonpath':
            # Fix common JSONPath syntax errors
            if not selector.startswith('$'):
                fixed_selector = '$.' + selector
            
            # Balance brackets and parentheses
            if selector.count('[') > selector.count(']'):
                fixed_selector += ']' * (selector.count('[') - selector.count(']'))
            if selector.count('(') > selector.count(')'):
                fixed_selector += ')' * (selector.count('(') - selector.count(')'))
        
        elif selector_type == 'jmespath':
            # Fix common JMESPath syntax errors
            if selector.startswith('$.'):
                fixed_selector = selector[2:]
            
            # Balance brackets, braces, and parentheses
            if selector.count('[') > selector.count(']'):
                fixed_selector += ']' * (selector.count('[') - selector.count(']'))
            if selector.count('{') > selector.count('}'):
                fixed_selector += '}' * (selector.count('{') - selector.count('}'))
            if selector.count('(') > selector.count(')'):
                fixed_selector += ')' * (selector.count('(') - selector.count(')'))
        
        elif selector_type == 'regex':
            # Fix common regex syntax errors
            if selector.count('(') > selector.count(')'):
                fixed_selector += ')' * (selector.count('(') - selector.count(')'))
            if selector.count('[') > selector.count(']'):
                fixed_selector += ']' * (selector.count('[') - selector.count(']'))
            if selector.count('{') > selector.count('}'):
                fixed_selector += '}' * (selector.count('{') - selector.count('}'))
        
        return fixed_selector, fixed_selector_type
    
    def get_error_details(self, error: SelectorError) -> Dict:
        """
        Get detailed information about an error
        
        Args:
            error: SelectorError object
            
        Returns:
            Dictionary with error details
        """
        return {
            'message': error.message,
            'selector': error.selector,
            'selector_type': error.selector_type,
            'details': error.details,
            'suggestions': error.suggestions,
            'fixed_selector': self.auto_fix_selector(error.selector, error.selector_type)[0] if error.selector else None,
            'fixed_selector_type': self.auto_fix_selector(error.selector, error.selector_type)[1] if error.selector else None
        }
    
    def format_error(self, error: SelectorError) -> str:
        """
        Format an error for display
        
        Args:
            error: SelectorError object
            
        Returns:
            Formatted error string
        """
        details = self.get_error_details(error)
        
        result = f"Error: {details['message']}\n"
        result += f"Selector: {details['selector']}\n"
        result += f"Type: {details['selector_type']}\n"
        
        if details['suggestions']:
            result += "Suggestions:\n"
            for i, suggestion in enumerate(details['suggestions']):
                result += f"  {i+1}. {suggestion}\n"
        
        if details['fixed_selector'] != details['selector'] or details['fixed_selector_type'] != details['selector_type']:
            result += "Auto-fixed:\n"
            result += f"  Selector: {details['fixed_selector']}\n"
            result += f"  Type: {details['fixed_selector_type']}\n"
        
        return result
