#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-25 15:00:00

import re
import logging
import lxml.etree
from pyquery import PyQuery
from typing import List, Dict, Union, Optional, Callable, Any, Tuple

from pyspider.libs.json_selector import JsonSelector
from pyspider.libs.css4_selector import CSS4Selector

logger = logging.getLogger('advanced_selector')

class AdvancedSelector:
    """
    Advanced selector for flexible data extraction using XPath, CSS, and RegEx
    """

    def __init__(self, response=None, html=None, url=None, json_data=None):
        """
        Initialize the selector with response or HTML/JSON content

        Args:
            response: PySpider response object
            html: HTML content as string
            url: URL for making links absolute
            json_data: JSON data as dict or list
        """
        self.response = response
        self._html = html
        self._url = url
        self._doc = None
        self._etree = None
        self._json_data = json_data
        self._json_selector = None
        self._css4_selector = None

        if response:
            self._html = response.content
            self._url = response.url
            self._doc = response.doc
            self._etree = response.etree
            try:
                self._json_data = response.json
            except Exception:
                self._json_data = None
        elif html:
            try:
                self._doc = PyQuery(html)
                if url:
                    self._doc.make_links_absolute(url)
                self._etree = lxml.etree.HTML(html)
            except Exception as e:
                logger.error(f"Error initializing selector: {e}")

    @property
    def doc(self):
        """Get PyQuery document"""
        return self._doc

    @property
    def etree(self):
        """Get lxml etree"""
        return self._etree

    @property
    def json_selector(self):
        """Get JSON selector"""
        if self._json_selector is None:
            self._json_selector = JsonSelector(response=self.response, json_data=self._json_data)
        return self._json_selector

    @property
    def css4_selector(self):
        """Get CSS4 selector"""
        if self._css4_selector is None:
            self._css4_selector = CSS4Selector(response=self.response, html=self._html, url=self._url)
        return self._css4_selector

    def css(self, selector: str, attr: str = None, default: Any = None) -> Union[List[str], str, None]:
        """
        Extract data using CSS selector

        Args:
            selector: CSS selector
            attr: Attribute to extract, None for text
            default: Default value if not found

        Returns:
            Extracted data
        """
        if not self._doc:
            return default

        try:
            elements = self._doc(selector)
            if not elements:
                return default

            if attr:
                if attr == 'html':
                    return [PyQuery(e).outer_html() for e in elements]
                elif attr == 'text':
                    return [PyQuery(e).text() for e in elements]
                else:
                    return [PyQuery(e).attr(attr) for e in elements]
            else:
                return [PyQuery(e).text() for e in elements]
        except Exception as e:
            logger.error(f"Error in CSS selector '{selector}': {e}")
            return default

    def css_first(self, selector: str, attr: str = None, default: Any = None) -> Union[str, None]:
        """
        Extract first element using CSS selector

        Args:
            selector: CSS selector
            attr: Attribute to extract, None for text
            default: Default value if not found

        Returns:
            Extracted data
        """
        result = self.css(selector, attr, [default])
        return result[0] if result else default

    def xpath(self, xpath: str, default: Any = None) -> Union[List[str], None]:
        """
        Extract data using XPath

        Args:
            xpath: XPath expression
            default: Default value if not found

        Returns:
            Extracted data
        """
        if not self._etree:
            return default

        try:
            elements = self._etree.xpath(xpath)
            if not elements:
                return default

            result = []
            for element in elements:
                if isinstance(element, lxml.etree._Element):
                    result.append(lxml.etree.tostring(element, encoding='unicode'))
                elif isinstance(element, lxml.etree._ElementUnicodeResult):
                    result.append(str(element))
                else:
                    result.append(element)

            return result
        except Exception as e:
            logger.error(f"Error in XPath '{xpath}': {e}")
            return default

    def xpath_first(self, xpath: str, default: Any = None) -> Union[str, None]:
        """
        Extract first element using XPath

        Args:
            xpath: XPath expression
            default: Default value if not found

        Returns:
            Extracted data
        """
        result = self.xpath(xpath, [default])
        return result[0] if result else default

    def regex(self, pattern: str, text: str = None, group: int = 0, default: Any = None) -> Union[List[str], str, None]:
        """
        Extract data using regular expression

        Args:
            pattern: Regular expression pattern
            text: Text to search in, None for HTML content
            group: Group to extract
            default: Default value if not found

        Returns:
            Extracted data
        """
        if text is None:
            text = self._html

        if not text:
            return default

        try:
            matches = re.findall(pattern, text)
            if not matches:
                return default

            if isinstance(matches[0], tuple):
                return [match[group] if len(match) > group else match[0] for match in matches]
            else:
                return matches
        except Exception as e:
            logger.error(f"Error in regex '{pattern}': {e}")
            return default

    def regex_first(self, pattern: str, text: str = None, group: int = 0, default: Any = None) -> Union[str, None]:
        """
        Extract first match using regular expression

        Args:
            pattern: Regular expression pattern
            text: Text to search in, None for HTML content
            group: Group to extract
            default: Default value if not found

        Returns:
            Extracted data
        """
        result = self.regex(pattern, text, group, [default])
        return result[0] if result else default

    def select(self, selectors: List[Dict], default: Any = None) -> Any:
        """
        Try multiple selectors in order until one succeeds

        Args:
            selectors: List of selector configurations
                [
                    {'type': 'css', 'selector': 'h1', 'attr': 'text'},
                    {'type': 'xpath', 'selector': '//h1/text()'},
                    {'type': 'regex', 'pattern': '<h1>(.*?)</h1>'},
                    {'type': 'css4', 'selector': 'h1:first-child', 'attr': 'text'},
                    {'type': 'jsonpath', 'path': '$.store.book[*].author'},
                    {'type': 'jmespath', 'path': 'store.book[*].author'}
                ]
            default: Default value if all selectors fail

        Returns:
            Extracted data
        """
        for selector in selectors:
            selector_type = selector.get('type', 'css')

            if selector_type == 'css':
                result = self.css_first(
                    selector.get('selector', ''),
                    selector.get('attr'),
                    None
                )
            elif selector_type == 'xpath':
                result = self.xpath_first(
                    selector.get('selector', ''),
                    None
                )
            elif selector_type == 'regex':
                result = self.regex_first(
                    selector.get('pattern', ''),
                    selector.get('text'),
                    selector.get('group', 0),
                    None
                )
            elif selector_type == 'css4':
                result = self.css4_selector.css4_first(
                    selector.get('selector', ''),
                    selector.get('attr'),
                    None
                )
            elif selector_type == 'jsonpath':
                result = self.json_selector.jsonpath_value(
                    selector.get('path', ''),
                    None
                )
            elif selector_type == 'jmespath':
                result = self.json_selector.jmespath(
                    selector.get('path', ''),
                    None
                )
            else:
                logger.warning(f"Unknown selector type: {selector_type}")
                continue

            if result is not None:
                return result

        return default

    def select_all(self, selectors: List[Dict], default: Any = None) -> List[Any]:
        """
        Try multiple selectors in order until one succeeds, returning all matches

        Args:
            selectors: List of selector configurations
            default: Default value if all selectors fail

        Returns:
            List of extracted data
        """
        for selector in selectors:
            selector_type = selector.get('type', 'css')

            if selector_type == 'css':
                result = self.css(
                    selector.get('selector', ''),
                    selector.get('attr'),
                    None
                )
            elif selector_type == 'xpath':
                result = self.xpath(
                    selector.get('selector', ''),
                    None
                )
            elif selector_type == 'regex':
                result = self.regex(
                    selector.get('pattern', ''),
                    selector.get('text'),
                    selector.get('group', 0),
                    None
                )
            elif selector_type == 'css4':
                result = self.css4_selector.css4(
                    selector.get('selector', ''),
                    selector.get('attr'),
                    None
                )
            elif selector_type == 'jsonpath':
                result = self.json_selector.jsonpath(
                    selector.get('path', ''),
                    None
                )
            elif selector_type == 'jmespath':
                # JMESPath already returns all matches
                result = self.json_selector.jmespath(
                    selector.get('path', ''),
                    None
                )
                # Ensure result is a list
                if result is not None and not isinstance(result, list):
                    result = [result]
            else:
                logger.warning(f"Unknown selector type: {selector_type}")
                continue

            if result:
                return result

        return default

    def extract_table(self, table_selector: str, header_selector: str = None, row_selector: str = 'tr', cell_selector: str = 'td,th') -> List[Dict]:
        """
        Extract data from HTML table

        Args:
            table_selector: CSS selector for table
            header_selector: CSS selector for header row, None for first row
            row_selector: CSS selector for rows
            cell_selector: CSS selector for cells

        Returns:
            List of dictionaries with table data
        """
        if not self._doc:
            return []

        try:
            table = self._doc(table_selector)
            if not table:
                return []

            # Extract headers
            if header_selector:
                header_row = table.find(header_selector)
            else:
                header_row = table.find('tr').eq(0)

            headers = [PyQuery(h).text().strip() for h in header_row.find(cell_selector)]

            # Extract rows
            result = []
            for row_idx, row in enumerate(table.find(row_selector)):
                # Skip header row
                if row_idx == 0 and not header_selector:
                    continue

                row_data = {}
                for cell_idx, cell in enumerate(PyQuery(row).find(cell_selector)):
                    if cell_idx < len(headers):
                        header = headers[cell_idx]
                        row_data[header] = PyQuery(cell).text().strip()
                    else:
                        row_data[f'column_{cell_idx}'] = PyQuery(cell).text().strip()

                result.append(row_data)

            return result
        except Exception as e:
            logger.error(f"Error extracting table: {e}")
            return []

    def extract_list(self, list_selector: str, item_selector: str, attr: str = None) -> List[str]:
        """
        Extract data from HTML list

        Args:
            list_selector: CSS selector for list (ul, ol)
            item_selector: CSS selector for list items
            attr: Attribute to extract, None for text

        Returns:
            List of extracted data
        """
        if not self._doc:
            return []

        try:
            list_element = self._doc(list_selector)
            if not list_element:
                return []

            items = list_element.find(item_selector)

            result = []
            for item in items:
                if attr:
                    if attr == 'html':
                        result.append(PyQuery(item).html())
                    elif attr == 'text':
                        result.append(PyQuery(item).text())
                    else:
                        result.append(PyQuery(item).attr(attr))
                else:
                    result.append(PyQuery(item).text())

            return result
        except Exception as e:
            logger.error(f"Error extracting list: {e}")
            return []

    def clean_text(self, text: str) -> str:
        """
        Clean text by removing extra whitespace

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Replace multiple whitespace with a single space
        text = re.sub(r'\s+', ' ', text)
        # Remove leading and trailing whitespace
        text = text.strip()

        return text

    # JSON selector methods

    def jsonpath(self, path: str, default: Any = None) -> List[Any]:
        """
        Extract data using JSONPath

        Args:
            path: JSONPath expression
            default: Default value if not found

        Returns:
            List of extracted data
        """
        return self.json_selector.jsonpath(path, default)

    def jsonpath_first(self, path: str, default: Any = None) -> Any:
        """
        Extract first element using JSONPath

        Args:
            path: JSONPath expression
            default: Default value if not found

        Returns:
            Extracted data
        """
        return self.json_selector.jsonpath_first(path, default)

    def jmespath(self, path: str, default: Any = None) -> Any:
        """
        Extract data using JMESPath

        Args:
            path: JMESPath expression
            default: Default value if not found

        Returns:
            Extracted data
        """
        return self.json_selector.jmespath(path, default)

    # CSS4 selector methods

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
        return self.css4_selector.css4(selector, attr, default)

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
        return self.css4_selector.css4_first(selector, attr, default)
