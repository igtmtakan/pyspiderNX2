#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-26 11:00:00

import logging
from typing import List, Dict, Union, Optional, Any, Tuple

import soupsieve
from bs4 import BeautifulSoup
from pyquery import PyQuery

logger = logging.getLogger('css4_selector')

class CSS4Selector:
    """
    CSS4 selector for advanced CSS selection using soupsieve
    """
    
    def __init__(self, response=None, html=None, url=None):
        """
        Initialize the selector with response or HTML content
        
        Args:
            response: PySpider response object
            html: HTML content as string
            url: URL for making links absolute
        """
        self.response = response
        self._html = html
        self._url = url
        self._doc = None
        self._soup = None
        
        if response:
            self._html = response.content
            self._url = response.url
            self._doc = response.doc
        elif html:
            try:
                self._doc = PyQuery(html)
                if url:
                    self._doc.make_links_absolute(url)
            except Exception as e:
                logger.error(f"Error initializing CSS4 selector with PyQuery: {e}")
        
        # Initialize BeautifulSoup for soupsieve
        try:
            if isinstance(self._html, bytes):
                self._soup = BeautifulSoup(self._html, 'lxml')
            else:
                self._soup = BeautifulSoup(self._html or "", 'lxml')
        except Exception as e:
            logger.error(f"Error initializing CSS4 selector with BeautifulSoup: {e}")
            self._soup = None
    
    @property
    def soup(self):
        """Get BeautifulSoup object"""
        return self._soup
    
    def select(self, selector: str, namespaces: Dict = None, default: Any = None) -> List[Any]:
        """
        Select elements using CSS4 selector
        
        Args:
            selector: CSS4 selector
            namespaces: Namespace dict for XML documents
            default: Default value if not found
            
        Returns:
            List of BeautifulSoup elements
        """
        if not self._soup:
            return default
        
        try:
            # Compile the selector
            compiled = soupsieve.compile(selector)
            
            # Select elements
            elements = compiled.select(self._soup, namespaces=namespaces)
            
            if not elements:
                return default
            
            return elements
        except soupsieve.SelectorSyntaxError as e:
            logger.error(f"Error parsing CSS4 selector '{selector}': {e}")
            return default
        except Exception as e:
            logger.error(f"Error in CSS4 selector '{selector}': {e}")
            return default
    
    def select_one(self, selector: str, namespaces: Dict = None, default: Any = None) -> Any:
        """
        Select first element using CSS4 selector
        
        Args:
            selector: CSS4 selector
            namespaces: Namespace dict for XML documents
            default: Default value if not found
            
        Returns:
            BeautifulSoup element
        """
        if not self._soup:
            return default
        
        try:
            # Compile the selector
            compiled = soupsieve.compile(selector)
            
            # Select first element
            element = compiled.select_one(self._soup, namespaces=namespaces)
            
            if not element:
                return default
            
            return element
        except soupsieve.SelectorSyntaxError as e:
            logger.error(f"Error parsing CSS4 selector '{selector}': {e}")
            return default
        except Exception as e:
            logger.error(f"Error in CSS4 selector '{selector}': {e}")
            return default
    
    def filter(self, elements, selector: str, namespaces: Dict = None, default: Any = None) -> List[Any]:
        """
        Filter elements using CSS4 selector
        
        Args:
            elements: List of BeautifulSoup elements
            selector: CSS4 selector
            namespaces: Namespace dict for XML documents
            default: Default value if not found
            
        Returns:
            Filtered list of BeautifulSoup elements
        """
        if not elements:
            return default
        
        try:
            # Compile the selector
            compiled = soupsieve.compile(selector)
            
            # Filter elements
            filtered = [element for element in elements if compiled.match(element)]
            
            if not filtered:
                return default
            
            return filtered
        except soupsieve.SelectorSyntaxError as e:
            logger.error(f"Error parsing CSS4 selector '{selector}': {e}")
            return default
        except Exception as e:
            logger.error(f"Error in CSS4 selector '{selector}': {e}")
            return default
    
    def match(self, element, selector: str, namespaces: Dict = None) -> bool:
        """
        Check if element matches CSS4 selector
        
        Args:
            element: BeautifulSoup element
            selector: CSS4 selector
            namespaces: Namespace dict for XML documents
            
        Returns:
            True if element matches selector
        """
        if not element:
            return False
        
        try:
            # Compile the selector
            compiled = soupsieve.compile(selector)
            
            # Check if element matches selector
            return compiled.match(element)
        except soupsieve.SelectorSyntaxError as e:
            logger.error(f"Error parsing CSS4 selector '{selector}': {e}")
            return False
        except Exception as e:
            logger.error(f"Error in CSS4 selector '{selector}': {e}")
            return False
    
    def closest(self, element, selector: str, namespaces: Dict = None, default: Any = None) -> Any:
        """
        Find closest ancestor matching CSS4 selector
        
        Args:
            element: BeautifulSoup element
            selector: CSS4 selector
            namespaces: Namespace dict for XML documents
            default: Default value if not found
            
        Returns:
            Closest ancestor element
        """
        if not element:
            return default
        
        try:
            # Compile the selector
            compiled = soupsieve.compile(selector)
            
            # Find closest ancestor
            ancestor = soupsieve.closest(element, compiled, namespaces=namespaces)
            
            if not ancestor:
                return default
            
            return ancestor
        except soupsieve.SelectorSyntaxError as e:
            logger.error(f"Error parsing CSS4 selector '{selector}': {e}")
            return default
        except Exception as e:
            logger.error(f"Error in CSS4 selector '{selector}': {e}")
            return default
    
    def extract_text(self, elements, separator: str = ' ', strip: bool = True) -> str:
        """
        Extract text from elements
        
        Args:
            elements: BeautifulSoup element or list of elements
            separator: Separator for text from multiple elements
            strip: Whether to strip whitespace
            
        Returns:
            Extracted text
        """
        if not elements:
            return ""
        
        try:
            # Handle single element
            if not isinstance(elements, list):
                elements = [elements]
            
            # Extract text from elements
            texts = []
            for element in elements:
                text = element.get_text(strip=strip)
                if text:
                    texts.append(text)
            
            return separator.join(texts)
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
    
    def extract_attr(self, elements, attr: str, default: str = "") -> Union[str, List[str]]:
        """
        Extract attribute from elements
        
        Args:
            elements: BeautifulSoup element or list of elements
            attr: Attribute name
            default: Default value if attribute not found
            
        Returns:
            Attribute value or list of values
        """
        if not elements:
            return default
        
        try:
            # Handle single element
            if not isinstance(elements, list):
                return elements.get(attr, default)
            
            # Extract attribute from elements
            values = []
            for element in elements:
                value = element.get(attr, default)
                if value:
                    values.append(value)
            
            return values
        except Exception as e:
            logger.error(f"Error extracting attribute: {e}")
            return default
    
    def css4(self, selector: str, attr: str = None, default: Any = None) -> Union[List[str], str, None]:
        """
        Extract data using CSS4 selector
        
        Args:
            selector: CSS4 selector
            attr: Attribute to extract, None for text
            default: Default value if not found
            
        Returns:
            Extracted data
        """
        elements = self.select(selector)
        
        if not elements:
            return default
        
        if attr:
            if attr == 'text':
                return [self.extract_text(element) for element in elements]
            elif attr == 'html':
                return [str(element) for element in elements]
            else:
                return self.extract_attr(elements, attr)
        else:
            return [self.extract_text(element) for element in elements]
    
    def css4_first(self, selector: str, attr: str = None, default: Any = None) -> Union[str, None]:
        """
        Extract first element using CSS4 selector
        
        Args:
            selector: CSS4 selector
            attr: Attribute to extract, None for text
            default: Default value if not found
            
        Returns:
            Extracted data
        """
        element = self.select_one(selector)
        
        if not element:
            return default
        
        if attr:
            if attr == 'text':
                return self.extract_text(element)
            elif attr == 'html':
                return str(element)
            else:
                return self.extract_attr(element, attr)
        else:
            return self.extract_text(element)
    
    def select_with_pseudo(self, selector: str, attr: str = None, default: Any = None) -> Union[List[str], str, None]:
        """
        Select elements using CSS4 selector with pseudo-classes
        
        Args:
            selector: CSS4 selector with pseudo-classes
            attr: Attribute to extract, None for text
            default: Default value if not found
            
        Returns:
            Extracted data
        """
        return self.css4(selector, attr, default)
