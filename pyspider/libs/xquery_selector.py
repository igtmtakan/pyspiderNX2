#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-27 11:00:00

import logging
import re
import os
import tempfile
import subprocess
from typing import List, Dict, Union, Optional, Any, Tuple

import lxml.etree as etree

logger = logging.getLogger('xquery_selector')

class XQuerySelector:
    """
    XQuery selector for querying XML documents using XQuery
    """

    def __init__(self, response=None, xml=None, url=None):
        """
        Initialize the selector with response or XML content

        Args:
            response: PySpider response object
            xml: XML content as string
            url: URL for making links absolute
        """
        self.response = response
        self._xml = xml
        self._url = url
        self._etree = None
        self._namespaces = {}

        if response:
            self._xml = response.content
            self._url = response.url

            # Try to get etree from response
            if hasattr(response, 'etree'):
                self._etree = response.etree

        if not self._etree and self._xml:
            try:
                self._etree = etree.fromstring(self._xml)

                # Extract namespaces
                nsmap = self._etree.nsmap
                if nsmap:
                    for prefix, uri in nsmap.items():
                        if prefix is None:
                            self._namespaces['ns'] = uri
                        else:
                            self._namespaces[prefix] = uri
            except Exception as e:
                logger.error(f"Error parsing XML: {e}")
                self._etree = None

    @property
    def etree(self):
        """Get lxml etree"""
        return self._etree

    @property
    def namespaces(self):
        """Get XML namespaces"""
        return self._namespaces

    def register_namespace(self, prefix: str, uri: str):
        """
        Register a namespace

        Args:
            prefix: Namespace prefix
            uri: Namespace URI
        """
        self._namespaces[prefix] = uri

    def xpath(self, xpath: str, namespaces: Dict = None, default: Any = None) -> List[Any]:
        """
        Execute an XPath query

        Args:
            xpath: XPath expression
            namespaces: Namespace dict for XML documents
            default: Default value if not found

        Returns:
            List of results
        """
        if not self._etree:
            return default

        try:
            # Use provided namespaces or default ones
            ns = namespaces or self._namespaces

            # Execute XPath query
            result = self._etree.xpath(xpath, namespaces=ns)

            if not result:
                return default

            return result
        except Exception as e:
            logger.error(f"Error executing XPath query '{xpath}': {e}")
            return default

    def xpath_first(self, xpath: str, namespaces: Dict = None, default: Any = None) -> Any:
        """
        Execute an XPath query and return the first result

        Args:
            xpath: XPath expression
            namespaces: Namespace dict for XML documents
            default: Default value if not found

        Returns:
            First result
        """
        result = self.xpath(xpath, namespaces, [default])
        return result[0] if result else default

    def xquery(self, query: str, namespaces: Dict = None, default: Any = None) -> str:
        """
        Execute an XQuery query using lxml's XSLT extension

        Args:
            query: XQuery expression
            namespaces: Namespace dict for XML documents
            default: Default value if not found

        Returns:
            Query result as string
        """
        if not self._etree:
            return default

        try:
            # Use provided namespaces or default ones
            ns = namespaces or self._namespaces

            # Convert XQuery to XSLT
            xslt = self._xquery_to_xslt(query, ns)

            # Execute XSLT transformation
            transform = etree.XSLT(xslt)
            result = transform(self._etree)

            if not result:
                return default

            return str(result)
        except Exception as e:
            logger.error(f"Error executing XQuery query: {e}")

            # Try using Saxon-HE as a fallback
            try:
                return self._xquery_with_saxon(query, ns)
            except Exception as e2:
                logger.error(f"Error executing XQuery with Saxon: {e2}")
                return default

    def _xquery_to_xslt(self, query: str, namespaces: Dict):
        """
        Convert an XQuery expression to XSLT

        Args:
            query: XQuery expression
            namespaces: Namespace dict

        Returns:
            XSLT document as ElementTree
        """
        # Basic XQuery to XSLT conversion
        # This is a simplified approach and won't work for all XQuery features

        # Add namespaces
        ns_decls = ""
        for prefix, uri in namespaces.items():
            ns_decls += f'xmlns:{prefix}="{uri}" '

        # Check if query is a FLWOR expression
        if any(keyword in query for keyword in ['for', 'let', 'where', 'order by', 'return']):
            # We can't convert complex FLWOR expressions to XSLT 1.0
            # Fall back to Saxon-HE
            raise ValueError("Complex XQuery FLWOR expressions require Saxon-HE")

        # Create XSLT template
        xslt = f"""
        <xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" {ns_decls}>
            <xsl:output method="xml" indent="yes"/>
            <xsl:template match="/">
                <result>
                    <xsl:copy-of select="{query}"/>
                </result>
            </xsl:template>
        </xsl:stylesheet>
        """

        return etree.fromstring(xslt)

    def _xquery_with_saxon(self, query: str, namespaces: Dict) -> str:
        """
        Execute an XQuery query using Saxon-HE

        Args:
            query: XQuery expression
            namespaces: Namespace dict

        Returns:
            Query result as string
        """
        # Check if Saxon is available
        try:
            subprocess.run(['java', '-version'], capture_output=True, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            raise RuntimeError("Java is not available, cannot use Saxon-HE")

        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as xml_file:
            xml_file.write(etree.tostring(self._etree))
            xml_path = xml_file.name

        with tempfile.NamedTemporaryFile(suffix='.xq', delete=False) as query_file:
            # Add namespace declarations
            ns_decls = ""
            for prefix, uri in namespaces.items():
                ns_decls += f'declare namespace {prefix} = "{uri}";\n'

            # Add XQuery version declaration for XQuery 3.1 features
            xquery_version = 'declare xquery version "3.1";\n'

            # Add Saxon-specific extensions for advanced features
            saxon_extensions = '''
            declare namespace saxon = "http://saxon.sf.net/";
            declare namespace array = "http://www.w3.org/2005/xpath-functions/array";
            declare namespace map = "http://www.w3.org/2005/xpath-functions/map";
            declare namespace math = "http://www.w3.org/2005/xpath-functions/math";
            '''

            full_query = xquery_version + saxon_extensions + ns_decls + query
            query_file.write(full_query.encode('utf-8'))
            query_path = query_file.name

        try:
            # Execute Saxon with XQuery 3.1 support
            cmd = [
                'java', '-cp', 'saxon-he.jar', 'net.sf.saxon.Query',
                '-qversion:3.1',
                f'-s:{xml_path}', f'-q:{query_path}'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        finally:
            # Clean up temporary files
            os.unlink(xml_path)
            os.unlink(query_path)

    def xquery31(self, query: str, namespaces: Dict = None, default: Any = None) -> str:
        """
        Execute an XQuery 3.1 query using Saxon-HE

        Args:
            query: XQuery 3.1 expression
            namespaces: Namespace dict for XML documents
            default: Default value if not found

        Returns:
            Query result as string
        """
        if not self._etree:
            return default

        try:
            # Use provided namespaces or default ones
            ns = namespaces or self._namespaces

            # Execute XQuery with Saxon-HE
            return self._xquery_with_saxon(query, ns)
        except Exception as e:
            logger.error(f"Error executing XQuery 3.1 query: {e}")
            return default

    def execute_flwor(self, query: str, namespaces: Dict = None, default: Any = None) -> str:
        """
        Execute a FLWOR expression using XQuery

        Args:
            query: FLWOR expression
            namespaces: Namespace dict for XML documents
            default: Default value if not found

        Returns:
            Query result as string
        """
        # FLWOR expressions require XQuery 3.1
        return self.xquery31(query, namespaces, default)

    def extract_value(self, xpath: str, namespaces: Dict = None, default: str = "") -> str:
        """
        Extract a text value using XPath

        Args:
            xpath: XPath expression
            namespaces: Namespace dict for XML documents
            default: Default value if not found

        Returns:
            Text value
        """
        result = self.xpath(xpath, namespaces)

        if not result:
            return default

        # Handle different result types
        if isinstance(result[0], str):
            return result[0]
        elif isinstance(result[0], etree._Element):
            return result[0].text or default
        else:
            return str(result[0])

    def extract_values(self, xpath: str, namespaces: Dict = None) -> List[str]:
        """
        Extract text values using XPath

        Args:
            xpath: XPath expression
            namespaces: Namespace dict for XML documents

        Returns:
            List of text values
        """
        result = self.xpath(xpath, namespaces)

        if not result:
            return []

        values = []
        for item in result:
            if isinstance(item, str):
                values.append(item)
            elif isinstance(item, etree._Element):
                values.append(item.text or "")
            else:
                values.append(str(item))

        return values

    def extract_attribute(self, xpath: str, attribute: str, namespaces: Dict = None, default: str = "") -> str:
        """
        Extract an attribute value using XPath

        Args:
            xpath: XPath expression
            attribute: Attribute name
            namespaces: Namespace dict for XML documents
            default: Default value if not found

        Returns:
            Attribute value
        """
        result = self.xpath(xpath, namespaces)

        if not result:
            return default

        if isinstance(result[0], etree._Element):
            return result[0].get(attribute, default)
        else:
            return default

    def extract_attributes(self, xpath: str, attribute: str, namespaces: Dict = None) -> List[str]:
        """
        Extract attribute values using XPath

        Args:
            xpath: XPath expression
            attribute: Attribute name
            namespaces: Namespace dict for XML documents

        Returns:
            List of attribute values
        """
        result = self.xpath(xpath, namespaces)

        if not result:
            return []

        values = []
        for item in result:
            if isinstance(item, etree._Element):
                values.append(item.get(attribute, ""))

        return values

    def extract_xml(self, xpath: str, namespaces: Dict = None, default: str = "") -> str:
        """
        Extract XML content using XPath

        Args:
            xpath: XPath expression
            namespaces: Namespace dict for XML documents
            default: Default value if not found

        Returns:
            XML content as string
        """
        result = self.xpath(xpath, namespaces)

        if not result:
            return default

        if isinstance(result[0], etree._Element):
            return etree.tostring(result[0], encoding='unicode')
        else:
            return default

    def extract_xmls(self, xpath: str, namespaces: Dict = None) -> List[str]:
        """
        Extract XML contents using XPath

        Args:
            xpath: XPath expression
            namespaces: Namespace dict for XML documents

        Returns:
            List of XML contents as strings
        """
        result = self.xpath(xpath, namespaces)

        if not result:
            return []

        values = []
        for item in result:
            if isinstance(item, etree._Element):
                values.append(etree.tostring(item, encoding='unicode'))

        return values
