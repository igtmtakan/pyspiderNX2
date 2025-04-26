#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-25 16:00:00

import re
import json
import logging
import lxml.etree
from typing import List, Dict, Union, Optional, Any
from pyquery import PyQuery

logger = logging.getLogger('structured_data')

class StructuredDataExtractor:
    """
    Extract structured data from HTML (JSON-LD, Microdata, RDFa)
    """
    
    def __init__(self, response=None, html=None, url=None):
        """
        Initialize the extractor with response or HTML content
        
        Args:
            response: PySpider response object
            html: HTML content as string
            url: URL for making links absolute
        """
        self.response = response
        self._html = html
        self._url = url
        self._doc = None
        self._etree = None
        
        if response:
            self._html = response.content
            self._url = response.url
            self._doc = response.doc
            self._etree = response.etree
        elif html:
            try:
                self._doc = PyQuery(html)
                if url:
                    self._doc.make_links_absolute(url)
                self._etree = lxml.etree.HTML(html)
            except Exception as e:
                logger.error(f"Error initializing extractor: {e}")
    
    def extract_all(self) -> Dict[str, List[Dict]]:
        """
        Extract all structured data from HTML
        
        Returns:
            Dictionary with structured data by type
        """
        result = {
            'json_ld': self.extract_json_ld(),
            'microdata': self.extract_microdata(),
            'rdfa': self.extract_rdfa(),
            'opengraph': self.extract_opengraph(),
            'twitter_cards': self.extract_twitter_cards(),
            'meta_tags': self.extract_meta_tags()
        }
        
        return result
    
    def extract_json_ld(self) -> List[Dict]:
        """
        Extract JSON-LD data from HTML
        
        Returns:
            List of JSON-LD objects
        """
        if not self._doc:
            return []
        
        result = []
        
        try:
            # Find all script tags with type="application/ld+json"
            script_tags = self._doc('script[type="application/ld+json"]')
            
            for script in script_tags:
                try:
                    json_data = json.loads(PyQuery(script).text())
                    if isinstance(json_data, list):
                        result.extend(json_data)
                    else:
                        result.append(json_data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Error decoding JSON-LD: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error extracting JSON-LD: {e}")
        
        return result
    
    def extract_microdata(self) -> List[Dict]:
        """
        Extract Microdata from HTML
        
        Returns:
            List of Microdata objects
        """
        if not self._doc:
            return []
        
        result = []
        
        try:
            # Find all elements with itemscope attribute
            itemscope_elements = self._doc('[itemscope]')
            
            for element in itemscope_elements:
                # Skip nested itemscope elements
                if PyQuery(element).parents('[itemscope]'):
                    continue
                
                item_data = self._extract_microdata_item(PyQuery(element))
                if item_data:
                    result.append(item_data)
        except Exception as e:
            logger.error(f"Error extracting Microdata: {e}")
        
        return result
    
    def _extract_microdata_item(self, element: PyQuery) -> Dict:
        """
        Extract Microdata from a single itemscope element
        
        Args:
            element: PyQuery element with itemscope
            
        Returns:
            Dictionary with Microdata
        """
        item_data = {}
        
        # Get item type
        item_type = element.attr('itemtype')
        if item_type:
            item_data['@type'] = item_type
        
        # Get item id
        item_id = element.attr('itemid')
        if item_id:
            item_data['@id'] = item_id
        
        # Get item properties
        for prop_element in element.find('[itemprop]'):
            prop_element = PyQuery(prop_element)
            prop_name = prop_element.attr('itemprop')
            
            # Skip if no property name
            if not prop_name:
                continue
            
            # Handle nested itemscope
            if prop_element.attr('itemscope') is not None:
                prop_value = self._extract_microdata_item(prop_element)
            else:
                prop_value = self._extract_microdata_value(prop_element)
            
            # Add property to item data
            if prop_name in item_data:
                if not isinstance(item_data[prop_name], list):
                    item_data[prop_name] = [item_data[prop_name]]
                item_data[prop_name].append(prop_value)
            else:
                item_data[prop_name] = prop_value
        
        return item_data
    
    def _extract_microdata_value(self, element: PyQuery) -> Any:
        """
        Extract value from a Microdata property element
        
        Args:
            element: PyQuery element with itemprop
            
        Returns:
            Property value
        """
        tag_name = element.prop('tagName').lower()
        
        # Handle different tag types
        if tag_name == 'meta':
            return element.attr('content')
        elif tag_name == 'img':
            return element.attr('src')
        elif tag_name == 'a':
            return element.attr('href')
        elif tag_name == 'link':
            return element.attr('href')
        elif tag_name == 'time':
            datetime = element.attr('datetime')
            if datetime:
                return datetime
        elif tag_name == 'data':
            value = element.attr('value')
            if value:
                return value
        
        # Default to text content
        return element.text()
    
    def extract_rdfa(self) -> List[Dict]:
        """
        Extract RDFa data from HTML
        
        Returns:
            List of RDFa objects
        """
        if not self._doc:
            return []
        
        result = []
        
        try:
            # Find all elements with typeof attribute
            typeof_elements = self._doc('[typeof]')
            
            for element in typeof_elements:
                # Skip nested typeof elements
                if PyQuery(element).parents('[typeof]'):
                    continue
                
                item_data = self._extract_rdfa_item(PyQuery(element))
                if item_data:
                    result.append(item_data)
        except Exception as e:
            logger.error(f"Error extracting RDFa: {e}")
        
        return result
    
    def _extract_rdfa_item(self, element: PyQuery) -> Dict:
        """
        Extract RDFa from a single typeof element
        
        Args:
            element: PyQuery element with typeof
            
        Returns:
            Dictionary with RDFa data
        """
        item_data = {}
        
        # Get item type
        item_type = element.attr('typeof')
        if item_type:
            item_data['@type'] = item_type
        
        # Get item id
        item_id = element.attr('resource') or element.attr('about')
        if item_id:
            item_data['@id'] = item_id
        
        # Get item properties
        for prop_element in element.find('[property]'):
            prop_element = PyQuery(prop_element)
            prop_name = prop_element.attr('property')
            
            # Skip if no property name
            if not prop_name:
                continue
            
            # Handle nested typeof
            if prop_element.attr('typeof') is not None:
                prop_value = self._extract_rdfa_item(prop_element)
            else:
                prop_value = self._extract_rdfa_value(prop_element)
            
            # Add property to item data
            if prop_name in item_data:
                if not isinstance(item_data[prop_name], list):
                    item_data[prop_name] = [item_data[prop_name]]
                item_data[prop_name].append(prop_value)
            else:
                item_data[prop_name] = prop_value
        
        return item_data
    
    def _extract_rdfa_value(self, element: PyQuery) -> Any:
        """
        Extract value from a RDFa property element
        
        Args:
            element: PyQuery element with property
            
        Returns:
            Property value
        """
        # Check for content attribute
        content = element.attr('content')
        if content:
            return content
        
        tag_name = element.prop('tagName').lower()
        
        # Handle different tag types
        if tag_name == 'meta':
            return element.attr('content')
        elif tag_name == 'img':
            return element.attr('src')
        elif tag_name == 'a':
            return element.attr('href')
        elif tag_name == 'link':
            return element.attr('href')
        elif tag_name == 'time':
            datetime = element.attr('datetime')
            if datetime:
                return datetime
        
        # Default to text content
        return element.text()
    
    def extract_opengraph(self) -> Dict:
        """
        Extract Open Graph metadata from HTML
        
        Returns:
            Dictionary with Open Graph data
        """
        if not self._doc:
            return {}
        
        result = {}
        
        try:
            # Find all meta tags with property starting with "og:"
            meta_tags = self._doc('meta[property^="og:"]')
            
            for meta in meta_tags:
                meta = PyQuery(meta)
                property_name = meta.attr('property')
                if not property_name:
                    continue
                
                # Remove "og:" prefix
                property_name = property_name[3:]
                content = meta.attr('content')
                
                if property_name in result:
                    if not isinstance(result[property_name], list):
                        result[property_name] = [result[property_name]]
                    result[property_name].append(content)
                else:
                    result[property_name] = content
        except Exception as e:
            logger.error(f"Error extracting Open Graph: {e}")
        
        return result
    
    def extract_twitter_cards(self) -> Dict:
        """
        Extract Twitter Card metadata from HTML
        
        Returns:
            Dictionary with Twitter Card data
        """
        if not self._doc:
            return {}
        
        result = {}
        
        try:
            # Find all meta tags with name starting with "twitter:"
            meta_tags = self._doc('meta[name^="twitter:"]')
            
            for meta in meta_tags:
                meta = PyQuery(meta)
                property_name = meta.attr('name')
                if not property_name:
                    continue
                
                # Remove "twitter:" prefix
                property_name = property_name[8:]
                content = meta.attr('content')
                
                if property_name in result:
                    if not isinstance(result[property_name], list):
                        result[property_name] = [result[property_name]]
                    result[property_name].append(content)
                else:
                    result[property_name] = content
        except Exception as e:
            logger.error(f"Error extracting Twitter Cards: {e}")
        
        return result
    
    def extract_meta_tags(self) -> Dict:
        """
        Extract standard meta tags from HTML
        
        Returns:
            Dictionary with meta tag data
        """
        if not self._doc:
            return {}
        
        result = {}
        
        try:
            # Find all meta tags with name or property attribute
            meta_tags = self._doc('meta[name], meta[property]')
            
            for meta in meta_tags:
                meta = PyQuery(meta)
                name = meta.attr('name') or meta.attr('property')
                if not name:
                    continue
                
                # Skip Open Graph and Twitter Card tags
                if name.startswith('og:') or name.startswith('twitter:'):
                    continue
                
                content = meta.attr('content')
                
                if name in result:
                    if not isinstance(result[name], list):
                        result[name] = [result[name]]
                    result[name].append(content)
                else:
                    result[name] = content
        except Exception as e:
            logger.error(f"Error extracting meta tags: {e}")
        
        return result
