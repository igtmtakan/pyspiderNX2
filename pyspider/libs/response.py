#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2012-11-02 11:16:02

import html.parser
import email.parser
import re
import json
import chardet
import lxml.html
import lxml.etree
import os
from tblib import Traceback
from pyquery import PyQuery
from requests.structures import CaseInsensitiveDict
from requests import HTTPError
from pyspider.libs import utils
from pyspider.libs.advanced_selector import AdvancedSelector
from pyspider.libs.structured_data import StructuredDataExtractor
from pyspider.libs.multimedia import MultimediaProcessor
from pyspider.libs.json_selector import JsonSelector
from pyspider.libs.css4_selector import CSS4Selector
from pyspider.libs.graphql_selector import GraphQLSelector
from pyspider.libs.xquery_selector import XQuerySelector
from pyspider.libs.selector_pipeline import SelectorPipeline
from pyspider.libs.selector_error_handler import SelectorErrorHandler


class Response(object):

    def __init__(self, status_code=None, url=None, orig_url=None, headers=CaseInsensitiveDict(),
                 content='', cookies=None, error=None, traceback=None, save=None, js_script_result=None, time=0):
        if cookies is None:
            cookies = {}
        self.status_code = status_code
        self.url = url
        self.orig_url = orig_url
        self.headers = headers
        self.content = content
        self.cookies = cookies
        self.error = error
        self.traceback = traceback
        self.save = save
        self.js_script_result = js_script_result
        self.time = time

        # Advanced selectors
        self._advanced_selector = None
        self._structured_data = None
        self._multimedia = None
        self._json_selector = None
        self._css4_selector = None
        self._graphql_selector = None
        self._xquery_selector = None
        self._selector_pipeline = None
        self._selector_error_handler = None

    def __repr__(self):
        return u'<Response [%d]>' % self.status_code

    def __bool__(self):
        """Returns true if `status_code` is 200 and no error"""
        return self.ok

    def __nonzero__(self):
        """Returns true if `status_code` is 200 and no error."""
        return self.ok

    @property
    def ok(self):
        """Return true if `status_code` is 200 and no error."""
        try:
            self.raise_for_status()
        except:
            return False
        return True

    @property
    def encoding(self):
        """
        encoding of Response.content.

        if Response.encoding is None, encoding will be guessed
        by header or content or chardet if available.
        """
        if hasattr(self, '_encoding'):
            return self._encoding

        # content is unicode
        if isinstance(self.content, str):
            return 'unicode'

        # Try charset from content-type or content
        encoding = get_encoding(self.headers, self.content)

        # Fallback to auto-detected encoding.
        if not encoding and chardet is not None:
            encoding = chardet.detect(self.content[:600])['encoding']

        if encoding and encoding.lower() == 'gb2312':
            encoding = 'gb18030'

        self._encoding = encoding or 'utf-8'
        return self._encoding

    @encoding.setter
    def encoding(self, value):
        """
        set encoding of content manually
        it will overwrite the guessed encoding
        """
        self._encoding = value
        self._text = None

    @property
    def text(self):
        """
        Content of the response, in unicode.

        if Response.encoding is None and chardet module is available, encoding
        will be guessed.
        """
        if hasattr(self, '_text') and self._text:
            return self._text
        if not self.content:
            return u''
        if isinstance(self.content, str):
            return self.content

        content = None
        encoding = self.encoding

        # Decode unicode from given encoding.
        try:
            content = self.content.decode(encoding, 'replace')
        except LookupError:
            # A LookupError is raised if the encoding was not found which could
            # indicate a misspelling or similar mistake.
            #
            # So we try blindly encoding.
            content = self.content.decode('utf-8', 'replace')

        self._text = content
        return content

    @property
    def json(self):
        """Returns the json-encoded content of the response, if any."""
        if hasattr(self, '_json'):
            return self._json
        try:
            self._json = json.loads(self.text or self.content)
        except ValueError:
            self._json = None
        return self._json

    @property
    def doc(self):
        """Returns a PyQuery object of the response's content"""
        if hasattr(self, '_doc'):
            return self._doc
        elements = self.etree
        doc = self._doc = PyQuery(elements)
        doc.make_links_absolute(utils.text(self.url))
        return doc

    @property
    def etree(self):
        """Returns a lxml object of the response's content that can be selected by xpath"""
        if not hasattr(self, '_elements'):
            try:
                # Python 3.13 compatibility: ensure encoding is a string, not bytes
                encoding = self.encoding
                if isinstance(encoding, bytes):
                    encoding = encoding.decode('utf-8')
                parser = lxml.html.HTMLParser(encoding=encoding)
                # Python 3.13 compatibility: ensure content is bytes
                content = self.content
                if isinstance(content, str):
                    content = content.encode(encoding or 'utf-8')
                self._elements = lxml.html.fromstring(content, parser=parser)
            except (LookupError, ValueError):
                # lxml would raise LookupError when encoding not supported
                # or ValueError for Unicode strings with encoding declaration
                # try fromstring without encoding instead.
                # on windows, unicode is not availabe as encoding for lxml
                content = self.content
                if isinstance(content, str):
                    content = content.encode('utf-8')
                self._elements = lxml.html.fromstring(content)
        if isinstance(self._elements, lxml.etree._ElementTree):
            self._elements = self._elements.getroot()
        return self._elements

    def raise_for_status(self, allow_redirects=True):
        """Raises stored :class:`HTTPError` or :class:`URLError`, if one occurred."""

        if self.status_code == 304:
            return
        elif self.error:
            if self.traceback:
                # Python 3.13 compatibility: use a different approach for re-raising exceptions
                try:
                    raise Exception(f"HTTP 599: {self.error}")
                except Exception as e:
                    raise e
            http_error = HTTPError(f"HTTP 599: {self.error}")
        elif (self.status_code >= 300) and (self.status_code < 400) and not allow_redirects:
            http_error = HTTPError(f"HTTP {self.status_code}: Redirection")
        elif (self.status_code >= 400) and (self.status_code < 500):
            http_error = HTTPError(f"HTTP {self.status_code}: Client Error")
        elif (self.status_code >= 500) and (self.status_code < 600):
            http_error = HTTPError(f"HTTP {self.status_code}: Server Error")
        else:
            return

        http_error.response = self
        raise http_error

    def isok(self):
        try:
            self.raise_for_status()
            return True
        except Exception:
            return False

    @property
    def ok(self):
        return self.isok()

    @property
    def advanced(self):
        """Returns an AdvancedSelector object for advanced data extraction"""
        if self._advanced_selector is None:
            self._advanced_selector = AdvancedSelector(response=self)
        return self._advanced_selector

    @property
    def structured_data(self):
        """Returns a StructuredDataExtractor object for extracting structured data"""
        if self._structured_data is None:
            self._structured_data = StructuredDataExtractor(response=self)
        return self._structured_data

    @property
    def multimedia(self):
        """Returns a MultimediaProcessor object for processing multimedia files"""
        if self._multimedia is None:
            self._multimedia = MultimediaProcessor(response=self)
        return self._multimedia

    @property
    def json_selector(self):
        """Returns a JsonSelector object for JSON data extraction"""
        if self._json_selector is None:
            self._json_selector = JsonSelector(response=self)
        return self._json_selector

    @property
    def css4_selector(self):
        """Returns a CSS4Selector object for advanced CSS selection"""
        if self._css4_selector is None:
            self._css4_selector = CSS4Selector(response=self)
        return self._css4_selector

    @property
    def graphql_selector(self):
        """Returns a GraphQLSelector object for GraphQL queries"""
        if self._graphql_selector is None:
            self._graphql_selector = GraphQLSelector(response=self)
        return self._graphql_selector

    @property
    def xquery_selector(self):
        """Returns an XQuerySelector object for XQuery queries"""
        if self._xquery_selector is None:
            self._xquery_selector = XQuerySelector(response=self)
        return self._xquery_selector

    @property
    def selector_pipeline(self):
        """Returns a SelectorPipeline object for combining selectors"""
        if self._selector_pipeline is None:
            self._selector_pipeline = SelectorPipeline(response=self)
        return self._selector_pipeline

    @property
    def selector_error_handler(self):
        """Returns a SelectorErrorHandler object for handling selector errors"""
        if self._selector_error_handler is None:
            self._selector_error_handler = SelectorErrorHandler(response=self)
        return self._selector_error_handler

    def xpath(self, xpath, default=None):
        """Shortcut for advanced.xpath_first"""
        return self.advanced.xpath_first(xpath, default)

    def xpaths(self, xpath, default=None):
        """Shortcut for advanced.xpath"""
        return self.advanced.xpath(xpath, default)

    def css(self, selector, attr=None, default=None):
        """Shortcut for advanced.css_first"""
        return self.advanced.css_first(selector, attr, default)

    def csss(self, selector, attr=None, default=None):
        """Shortcut for advanced.css"""
        return self.advanced.css(selector, attr, default)

    def regex(self, pattern, text=None, group=0, default=None):
        """Shortcut for advanced.regex_first"""
        return self.advanced.regex_first(pattern, text, group, default)

    def regexs(self, pattern, text=None, group=0, default=None):
        """Shortcut for advanced.regex"""
        return self.advanced.regex(pattern, text, group, default)

    def css4(self, selector, attr=None, default=None):
        """Shortcut for advanced.css4_first"""
        return self.advanced.css4_first(selector, attr, default)

    def css4s(self, selector, attr=None, default=None):
        """Shortcut for advanced.css4"""
        return self.advanced.css4(selector, attr, default)

    def jsonpath(self, path, default=None):
        """Shortcut for advanced.jsonpath_first"""
        return self.advanced.jsonpath_first(path, default)

    def jsonpaths(self, path, default=None):
        """Shortcut for advanced.jsonpath"""
        return self.advanced.jsonpath(path, default)

    def jmespath(self, path, default=None):
        """Shortcut for advanced.jmespath"""
        return self.advanced.jmespath(path, default)

    def extract_table(self, table_selector, header_selector=None, row_selector='tr', cell_selector='td,th'):
        """Shortcut for advanced.extract_table"""
        return self.advanced.extract_table(table_selector, header_selector, row_selector, cell_selector)

    def extract_list(self, list_selector, item_selector, attr=None):
        """Shortcut for advanced.extract_list"""
        return self.advanced.extract_list(list_selector, item_selector, attr)

    def graphql(self, query, variables=None, path=None, default=None):
        """Shortcut for graphql_selector.query"""
        return self.graphql_selector.query(query, variables, path, default)

    def graphql_subscribe(self, query, variables=None, callback=None):
        """Shortcut for graphql_selector.subscribe"""
        return self.graphql_selector.subscribe(query, variables, callback)

    def graphql_unsubscribe(self, subscription_id):
        """Shortcut for graphql_selector.unsubscribe"""
        return self.graphql_selector.unsubscribe(subscription_id)

    def xquery(self, query, namespaces=None, default=None):
        """Shortcut for xquery_selector.xquery"""
        return self.xquery_selector.xquery(query, namespaces, default)

    def xquery31(self, query, namespaces=None, default=None):
        """Shortcut for xquery_selector.xquery31"""
        return self.xquery_selector.xquery31(query, namespaces, default)

    def execute_flwor(self, query, namespaces=None, default=None):
        """Shortcut for xquery_selector.execute_flwor"""
        return self.xquery_selector.execute_flwor(query, namespaces, default)

    def pipeline(self, selectors, transformers=None, combiner='first'):
        """Shortcut for selector_pipeline.extract"""
        return self.selector_pipeline.extract(selectors, transformers, combiner)

    def extract_with_fallbacks(self, selectors, transformers=None):
        """Shortcut for selector_pipeline.extract_with_fallbacks"""
        return self.selector_pipeline.extract_with_fallbacks(selectors, transformers)

    def extract_multiple(self, config):
        """Shortcut for selector_pipeline.extract_multiple"""
        return self.selector_pipeline.extract_multiple(config)

    def extract_table_advanced(self, config):
        """Shortcut for selector_pipeline.extract_table"""
        return self.selector_pipeline.extract_table(config)

    def extract_list_advanced(self, config):
        """Shortcut for selector_pipeline.extract_list"""
        return self.selector_pipeline.extract_list(config)

    def load_transformer_module(self, module_path):
        """Shortcut for selector_pipeline.load_transformer_module"""
        return self.selector_pipeline.load_transformer_module(module_path)

    def register_transformer(self, name, func):
        """Shortcut for selector_pipeline.register_transformer"""
        return self.selector_pipeline.register_transformer(name, func)

    def create_pipeline(self, steps):
        """Shortcut for selector_pipeline.create_pipeline"""
        return self.selector_pipeline.create_pipeline(steps)

    def execute_pipeline(self, pipeline_config, input_data=None):
        """Shortcut for selector_pipeline.execute_pipeline"""
        return self.selector_pipeline.execute_pipeline(pipeline_config, input_data)


def rebuild_response(r):
    response = Response(
        status_code=r.get('status_code', 599),
        url=r.get('url', ''),
        headers=CaseInsensitiveDict(r.get('headers', {})),
        content=r.get('content', ''),
        cookies=r.get('cookies', {}),
        error=r.get('error'),
        traceback=r.get('traceback'),
        time=r.get('time', 0),
        orig_url=r.get('orig_url', r.get('url', '')),
        js_script_result=r.get('js_script_result'),
        save=r.get('save'),
    )
    return response


def get_encoding(headers, content):
    """Get encoding from request headers or page head."""
    encoding = None

    content_type = headers.get('content-type')
    if content_type:
        parser = email.parser.HeaderParser()
        header = parser.parsestr('Content-Type: ' + content_type)
        params = dict(header.get_params())
        if 'charset' in params:
            encoding = params['charset'].strip("'\"")

    if not encoding:
        content = utils.pretty_unicode(content[:1000])

        charset_re = re.compile(r'<meta.*?charset=["\']*(.+?)["\'>]',
                                flags=re.I)
        pragma_re = re.compile(r'<meta.*?content=["\']*;?charset=(.+?)["\'>]',
                               flags=re.I)
        xml_re = re.compile(r'^<\?xml.*?encoding=["\']*(.+?)["\'>]')
        encoding = (charset_re.findall(content) +
                    pragma_re.findall(content) +
                    xml_re.findall(content))
        encoding = encoding and encoding[0] or None

    return encoding
