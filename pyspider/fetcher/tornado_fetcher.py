#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2012-12-17 11:07:19



import os
import sys

import copy
import time
import json
import logging
import traceback
import functools
import threading
import tornado.ioloop
import tornado.httputil
import tornado.httpclient
import pyspider
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from urllib3.contrib.pyopenssl import inject_into_urllib3
import ssl
import requests

# OpenSSLをURLLib3に注入
inject_into_urllib3()


from six.moves.urllib.robotparser import RobotFileParser
from requests import cookies
from six.moves.urllib.parse import urljoin, urlsplit
from tornado import gen

try:
    import http.cookies as http_cookies
except ImportError:
    import Cookie as http_cookies
from tornado.curl_httpclient import CurlAsyncHTTPClient
from tornado.simple_httpclient import SimpleAsyncHTTPClient

from pyspider.libs import utils, dataurl, counter
from pyspider.libs.url import quote_chinese
from .cookie_utils import extract_cookies_to_jar
logger = logging.getLogger('fetcher')


class MyCurlAsyncHTTPClient(CurlAsyncHTTPClient):
    def __init__(self, *args, **kwargs):
        self.max_clients = kwargs.get('max_clients', 10)
        # In Python 3.13, we need to use a different approach
        # Call the parent class's __init__ method directly
        # First, get the parent class's __init__ method
        parent_init = CurlAsyncHTTPClient.__init__
        # Then call it with self as the first argument
        parent_init(self)

    def free_size(self):
        return len(self._free_list)

    def size(self):
        return len(self._curls) - self.free_size()


class MySimpleAsyncHTTPClient(SimpleAsyncHTTPClient):
    def __init__(self, *args, **kwargs):
        self.max_clients = kwargs.get('max_clients', 10)
        # In Python 3.13, we need to use a different approach
        # Call the parent class's __init__ method directly
        # First, get the parent class's __init__ method
        parent_init = SimpleAsyncHTTPClient.__init__
        # Then call it with self as the first argument
        parent_init(self)

    def free_size(self):
        return self.max_clients - self.size()

    def size(self):
        return len(self.active)

fetcher_output = {
    "status_code": int,
    "orig_url": str,
    "url": str,
    "headers": dict,
    "content": str,
    "cookies": dict,
}


class Fetcher(object):
    user_agent = "pyspider/0.3.10 (+http://pyspider.org/)"
    default_options = {
        'method': 'GET',
        'headers': {
        },
        'use_gzip': True,
        'timeout': 120,
        'connect_timeout': 20,
    }
    phantomjs_proxy = None
    splash_endpoint = None
    puppeteer_endpoint = 'http://localhost:22223'
    splash_lua_source = open(os.path.join(os.path.dirname(__file__), "splash_fetcher.lua")).read()
    robot_txt_age = 60*60  # 1h

    def __init__(self, inqueue, outqueue, poolsize=100, proxy=None, async_mode=True):
        self.inqueue = inqueue
        self.outqueue = outqueue

        self.poolsize = poolsize
        self._running = False
        self._quit = False
        self.proxy = proxy
        self.async_mode = async_mode
        self.ioloop = tornado.ioloop.IOLoop.current()

        self.robots_txt_cache = {}

        # binding io_loop to http_client here
        # In Python 3.13, we need to use AsyncHTTPClient directly to avoid event loop issues
        self.http_client = MyCurlAsyncHTTPClient(max_clients=self.poolsize)
        # We don't use HTTPClient anymore as it causes event loop issues in Python 3.13
        # if not self.async_mode:
        #     self.http_client = tornado.httpclient.HTTPClient(MyCurlAsyncHTTPClient, max_clients=self.poolsize)

        self._cnt = {
            '5m': counter.CounterManager(
                lambda: counter.TimebaseAverageWindowCounter(30, 10)),
            '1h': counter.CounterManager(
                lambda: counter.TimebaseAverageWindowCounter(60, 60)),
        }

        # SSLコンテキストの設定
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        self.ssl_context.set_ciphers('DEFAULT:@SECLEVEL=1')

        # requestsセッションの設定
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=self.poolsize,
            pool_maxsize=self.poolsize,
            max_retries=3,
            pool_block=False
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.verify = False

    def send_result(self, fetch_type, task, result):
        '''Send fetch result to processor'''
        if self.outqueue:
            try:
                self.outqueue.put((task, result))
            except Exception as e:
                logger.exception(e)

    def fetch(self, task, callback=None):
        """Fetch a task

        In Python 3.13, we need to handle the result differently to avoid asyncio issues
        """
        if self.async_mode:
            return self.async_fetch(task, callback)
        else:
            # In Python 3.13, we can't use result() directly due to asyncio changes
            # Create a synchronous wrapper around the async fetch
            try:
                # For debug mode, we need to handle the fetch differently
                # Create a direct fetch without using the async_fetch method
                url = task.get('url', 'data:,on_start')

                # Handle data URLs directly
                if url.startswith('data:'):
                    return self.data_fetch(url, task)

                # Use requests instead of urllib or tornado.httpclient.HTTPClient
                import requests
                import time

                # Prepare request
                method = task.get('fetch', {}).get('method', 'GET')
                headers = task.get('fetch', {}).get('headers', {})
                data = task.get('fetch', {}).get('data', None)
                timeout = task.get('fetch', {}).get('timeout', 120)
                allow_redirects = task.get('fetch', {}).get('allow_redirects', True)

                # Start timer
                start_time = time.time()

                try:
                    # Perform request
                    response = requests.request(
                        method=method,
                        url=url,
                        headers=headers,
                        data=data,
                        timeout=timeout,
                        allow_redirects=allow_redirects,
                        verify=False  # Disable SSL verification for simplicity
                    )

                    # Create result
                    result = {
                        'status_code': response.status_code,
                        'url': response.url,
                        'orig_url': url,
                        'headers': dict(response.headers),
                        'cookies': response.cookies,
                        'content': response.text,
                        'time': time.time() - start_time,
                        'save': task.get('fetch', {}).get('save'),
                        'error': None,
                        'traceback': None,
                    }

                    return result
                except requests.exceptions.RequestException as e:
                    # Handle all request exceptions
                    result = {
                        'status_code': 599,  # Use 599 for network errors
                        'url': url,
                        'orig_url': url,
                        'headers': {},
                        'cookies': {},
                        'content': str(e),
                        'time': time.time() - start_time,
                        'save': task.get('fetch', {}).get('save'),
                        'error': str(e),
                        'traceback': None,
                    }
                    return result
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise e

    def convert_response(self, response, task):
        """Convert tornado response to pyspider fetcher result format"""
        cookies = tornado.httputil.HTTPHeaders()
        for key, value in response.headers.get_all():
            if key.lower() == 'set-cookie':
                cookies.add('Set-Cookie', value)

        result = {
            'status_code': response.code,
            'url': response.effective_url or task.get('url'),
            'orig_url': task.get('url'),
            'headers': dict(response.headers),
            'cookies': cookies,
            'content': response.body or '',
            'time': response.request_time,
            'save': task.get('fetch', {}).get('save'),
        }

        try:
            if isinstance(result['content'], bytes):
                result['content'] = result['content'].decode('utf-8')
        except UnicodeDecodeError:
            pass

        return result

    @gen.coroutine
    def async_fetch(self, task, callback=None):
        '''Do one fetch

        In Python 3.13, we need to be careful with event loops and coroutines
        '''
        url = task.get('url', 'data:,')
        if callback is None:
            callback = self.send_result

        fetch_type = 'None'
        start_time = time.time()
        try:
            if url.startswith('data:'):
                fetch_type = 'data'
                result = yield gen.maybe_future(self.data_fetch(url, task))
            elif task.get('fetch', {}).get('fetch_type') in ('js', 'phantomjs'):
                fetch_type = 'phantomjs'
                result = yield self.phantomjs_fetch(url, task)
            elif task.get('fetch', {}).get('fetch_type') in ('splash', ):
                fetch_type = 'splash'
                result = yield self.splash_fetch(url, task)
            elif task.get('fetch', {}).get('fetch_type') in ('puppeteer', ):
                fetch_type = 'puppeteer'
                result = yield self.puppeteer_fetch(url, task)
            else:
                fetch_type = 'http'
                # In Python 3.13, we need to handle http_fetch differently to avoid event loop issues
                try:
                    # Create a Future that will be resolved by http_fetch
                    future = tornado.concurrent.Future()

                    # Call http_fetch without yielding
                    http_future = self.http_fetch(url, task)

                    # Set up a callback to resolve our future when http_fetch completes
                    def on_http_fetch_done(f):
                        try:
                            result = f.result()
                            future.set_result(result)
                        except Exception as e:
                            future.set_exception(e)

                    # Add the callback to the http_fetch future
                    http_future.add_done_callback(on_http_fetch_done)

                    # Now yield our future, not the http_fetch future directly
                    result = yield future
                except Exception as e:
                    logger.exception(e)
                    raise
        except Exception as e:
            logger.exception(e)
            result = self.handle_error(fetch_type, url, task, start_time, e)

        callback(fetch_type, task, result)
        self.on_result(fetch_type, task, result)
        raise gen.Return(result)

    def sync_fetch(self, task):
        '''Synchronization fetch, usually used in xmlrpc thread'''
        if not self._running:
            return self.ioloop.run_sync(functools.partial(self.async_fetch, task, lambda type_arg, _, result_arg: True))

        wait_result = threading.Condition()
        _result = {}

        def callback(type, task, result):
            wait_result.acquire()
            _result['type'] = type
            _result['task'] = task
            _result['result'] = result
            wait_result.notify()
            wait_result.release()

        wait_result.acquire()
        self.ioloop.add_callback(self.fetch, task, callback)
        while 'result' not in _result:
            wait_result.wait()
        wait_result.release()
        return _result['result']

    def data_fetch(self, url, task):
        '''A fake fetcher for dataurl'''
        self.on_fetch('data', task)
        result = {}
        result['orig_url'] = url
        result['content'] = dataurl.decode(url)
        result['headers'] = {}
        result['status_code'] = 200
        result['url'] = url
        result['cookies'] = {}
        result['time'] = 0
        result['save'] = task.get('fetch', {}).get('save')
        if len(result['content']) < 70:
            logger.info("[200] %s:%s %s 0s", task.get('project'), task.get('taskid'), url)
        else:
            logger.info(
                "[200] %s:%s data:,%s...[content:%d] 0s",
                task.get('project'), task.get('taskid'),
                result['content'][:70],
                len(result['content'])
            )

        return result

    def handle_error(self, fetch_type, url, task, start_time, error):
        result = {
            'status_code': getattr(error, 'code', 599),
            'error': utils.text(error),
            'traceback': traceback.format_exc() if sys.exc_info()[0] else None,
            'content': "",
            'time': time.time() - start_time,
            'orig_url': url,
            'url': url,
            "save": task.get('fetch', {}).get('save')
        }
        logger.error("[%d] %s:%s %s, %r %.2fs",
                     result['status_code'], task.get('project'), task.get('taskid'),
                     url, error, result['time'])
        return result

    allowed_options = ['method', 'data', 'connect_timeout', 'timeout', 'cookies', 'use_gzip', 'validate_cert']

    def pack_tornado_request_parameters(self, url, task):
        fetch = copy.deepcopy(self.default_options)
        fetch['url'] = url
        fetch['headers'] = tornado.httputil.HTTPHeaders(fetch['headers'])
        fetch['headers']['User-Agent'] = self.user_agent
        task_fetch = task.get('fetch', {})
        for each in self.allowed_options:
            if each in task_fetch:
                fetch[each] = task_fetch[each]
        fetch['headers'].update(task_fetch.get('headers', {}))

        if task.get('track'):
            track_headers = tornado.httputil.HTTPHeaders(
                task.get('track', {}).get('fetch', {}).get('headers') or {})
            track_ok = task.get('track', {}).get('process', {}).get('ok', False)
        else:
            track_headers = {}
            track_ok = False
        # proxy
        proxy_string = None
        if isinstance(task_fetch.get('proxy'), str):
            proxy_string = task_fetch['proxy']
        elif self.proxy and task_fetch.get('proxy', True):
            proxy_string = self.proxy
        if proxy_string:
            if '://' not in proxy_string:
                proxy_string = 'http://' + proxy_string
            proxy_splited = urlsplit(proxy_string)
            fetch['proxy_host'] = proxy_splited.hostname
            if proxy_splited.username:
                fetch['proxy_username'] = proxy_splited.username
            if proxy_splited.password:
                fetch['proxy_password'] = proxy_splited.password
            if False:
                for key in ('proxy_host', 'proxy_username', 'proxy_password'):
                    if key in fetch:
                        fetch[key] = fetch[key].encode('utf8')
            fetch['proxy_port'] = proxy_splited.port or 8080

        # etag
        if task_fetch.get('etag', True):
            _t = None
            if isinstance(task_fetch.get('etag'), str):
                _t = task_fetch.get('etag')
            elif track_ok:
                _t = track_headers.get('etag')
            if _t and 'If-None-Match' not in fetch['headers']:
                fetch['headers']['If-None-Match'] = _t
        # last modifed
        if task_fetch.get('last_modified', task_fetch.get('last_modifed', True)):
            last_modified = task_fetch.get('last_modified', task_fetch.get('last_modifed', True))
            _t = None
            if isinstance(last_modified, str):
                _t = last_modified
            elif track_ok:
                _t = track_headers.get('last-modified')
            if _t and 'If-Modified-Since' not in fetch['headers']:
                fetch['headers']['If-Modified-Since'] = _t
        # timeout
        if 'timeout' in fetch:
            fetch['request_timeout'] = fetch['timeout']
            del fetch['timeout']
        # data rename to body
        if 'data' in fetch:
            fetch['body'] = fetch['data']
            del fetch['data']

        return fetch

    @gen.coroutine
    def can_fetch(self, user_agent, url):
        parsed = urlsplit(url)
        domain = parsed.netloc
        if domain in self.robots_txt_cache:
            robot_txt = self.robots_txt_cache[domain]
            if time.time() - robot_txt.mtime() > self.robot_txt_age:
                robot_txt = None
        else:
            robot_txt = None

        if robot_txt is None:
            robot_txt = RobotFileParser()
            try:
                response = yield gen.maybe_future(self.http_client.fetch(
                    urljoin(url, '/robots.txt'), connect_timeout=10, request_timeout=30))
                content = response.body
            except tornado.httpclient.HTTPError as e:
                logger.error('load robots.txt from %s error: %r', domain, e)
                content = ''

            try:
                content = content.decode('utf8', 'ignore')
            except UnicodeDecodeError:
                content = ''

            robot_txt.parse(content.splitlines())
            self.robots_txt_cache[domain] = robot_txt

        raise gen.Return(robot_txt.can_fetch(user_agent, url))

    def clear_robot_txt_cache(self):
        now = time.time()
        for domain, robot_txt in self.robots_txt_cache.items():
            if now - robot_txt.mtime() > self.robot_txt_age:
                del self.robots_txt_cache[domain]

    @gen.coroutine
    def http_fetch(self, url, task):
        '''HTTP fetcher'''
        start_time = time.time()
        self.on_fetch('http', task)
        handle_error = lambda x: self.handle_error('http', url, task, start_time, x)

        # setup request parameters
        fetch = self.pack_tornado_request_parameters(url, task)
        task_fetch = task.get('fetch', {})

        session = cookies.RequestsCookieJar()
        # fix for tornado request obj
        if 'Cookie' in fetch['headers']:
            c = http_cookies.SimpleCookie()
            try:
                c.load(fetch['headers']['Cookie'])
            except AttributeError:
                c.load(utils.utf8(fetch['headers']['Cookie']))
            for key in c:
                session.set(key, c[key])
            del fetch['headers']['Cookie']
        if 'cookies' in fetch:
            session.update(fetch['cookies'])
            del fetch['cookies']

        max_redirects = task_fetch.get('max_redirects', 5)
        # we will handle redirects by hand to capture cookies
        fetch['follow_redirects'] = False

        # making requests
        while True:
            # robots.txt
            if task_fetch.get('robots_txt', False):
                can_fetch = yield self.can_fetch(fetch['headers']['User-Agent'], fetch['url'])
                if not can_fetch:
                    error = tornado.httpclient.HTTPError(403, 'Disallowed by robots.txt')
                    raise gen.Return(handle_error(error))

            try:
                request = tornado.httpclient.HTTPRequest(**fetch)
                # if cookie already in header, get_cookie_header wouldn't work
                old_cookie_header = request.headers.get('Cookie')
                if old_cookie_header:
                    del request.headers['Cookie']
                cookie_header = cookies.get_cookie_header(session, request)
                if cookie_header:
                    request.headers['Cookie'] = cookie_header
                elif old_cookie_header:
                    request.headers['Cookie'] = old_cookie_header
            except Exception as e:
                logger.exception(fetch)
                raise gen.Return(handle_error(e))

            try:
                # In Tornado 6.0+ with Python 3.13, we need to use a different approach
                # to avoid "Cannot run the event loop while another loop is running" error
                if not self.async_mode:
                    # For non-async mode, we need to create a Future and set its result
                    future = tornado.concurrent.Future()
                    try:
                        # Use AsyncHTTPClient directly without run_sync
                        response_future = self.http_client.fetch(request, raise_error=False)
                        # Wait for the response using a callback
                        def on_response(f):
                            try:
                                future.set_result(f.result())
                            except Exception as e:
                                future.set_exception(e)
                        response_future.add_done_callback(on_response)
                        response = yield future
                    except Exception as e:
                        future.set_exception(e)
                        raise
                else:
                    # For async mode, we can use the future directly
                    response = yield self.http_client.fetch(request, raise_error=False)
            except tornado.httpclient.HTTPError as e:
                if e.response:
                    response = e.response
                else:
                    raise gen.Return(handle_error(e))

            extract_cookies_to_jar(session, response.request, response.headers)
            if (response.code in (301, 302, 303, 307)
                    and response.headers.get('Location')
                    and task_fetch.get('allow_redirects', True)):
                if max_redirects <= 0:
                    error = tornado.httpclient.HTTPError(
                        599, 'Maximum (%d) redirects followed' % task_fetch.get('max_redirects', 5),
                        response)
                    raise gen.Return(handle_error(error))
                if response.code in (302, 303):
                    fetch['method'] = 'GET'
                    if 'body' in fetch:
                        del fetch['body']
                fetch['url'] = quote_chinese(urljoin(fetch['url'], response.headers['Location']))
                fetch['request_timeout'] -= time.time() - start_time
                if fetch['request_timeout'] < 0:
                    fetch['request_timeout'] = 0.1
                max_redirects -= 1
                continue

            result = {}
            result['orig_url'] = url
            result['content'] = response.body or ''
            result['headers'] = dict(response.headers)
            result['status_code'] = response.code
            result['url'] = response.effective_url or url
            result['time'] = time.time() - start_time
            result['cookies'] = session.get_dict()
            result['save'] = task_fetch.get('save')
            if response.error:
                result['error'] = utils.text(response.error)
            if 200 <= response.code < 300:
                logger.info("[%d] %s:%s %s %.2fs", response.code,
                            task.get('project'), task.get('taskid'),
                            url, result['time'])
            else:
                logger.warning("[%d] %s:%s %s %.2fs", response.code,
                               task.get('project'), task.get('taskid'),
                               url, result['time'])

            raise gen.Return(result)

    @gen.coroutine
    def phantomjs_fetch(self, url, task):
        '''Fetch with phantomjs proxy'''
        start_time = time.time()
        self.on_fetch('phantomjs', task)
        handle_error = lambda x: self.handle_error('phantomjs', url, task, start_time, x)

        # check phantomjs proxy is enabled
        if not self.phantomjs_proxy:
            result = {
                "orig_url": url,
                "content": "phantomjs is not enabled.",
                "headers": {},
                "status_code": 501,
                "url": url,
                "time": time.time() - start_time,
                "cookies": {},
                "save": task.get('fetch', {}).get('save')
            }
            logger.warning("[501] %s:%s %s 0s", task.get('project'), task.get('taskid'), url)
            raise gen.Return(result)

        # setup request parameters
        fetch = self.pack_tornado_request_parameters(url, task)
        task_fetch = task.get('fetch', {})
        for each in task_fetch:
            if each not in fetch:
                fetch[each] = task_fetch[each]

        # robots.txt
        if task_fetch.get('robots_txt', False):
            user_agent = fetch['headers']['User-Agent']
            can_fetch = yield self.can_fetch(user_agent, url)
            if not can_fetch:
                error = tornado.httpclient.HTTPError(403, 'Disallowed by robots.txt')
                raise gen.Return(handle_error(error))

        request_conf = {
            'follow_redirects': False
        }
        request_conf['connect_timeout'] = fetch.get('connect_timeout', 20)
        request_conf['request_timeout'] = fetch.get('request_timeout', 120) + 1

        session = cookies.RequestsCookieJar()
        if 'Cookie' in fetch['headers']:
            c = http_cookies.SimpleCookie()
            try:
                c.load(fetch['headers']['Cookie'])
            except AttributeError:
                c.load(utils.utf8(fetch['headers']['Cookie']))
            for key in c:
                session.set(key, c[key])
            del fetch['headers']['Cookie']
        if 'cookies' in fetch:
            session.update(fetch['cookies'])
            del fetch['cookies']

        request = tornado.httpclient.HTTPRequest(url=fetch['url'])
        cookie_header = cookies.get_cookie_header(session, request)
        if cookie_header:
            fetch['headers']['Cookie'] = cookie_header

        # making requests
        fetch['headers'] = dict(fetch['headers'])
        try:
            request = tornado.httpclient.HTTPRequest(
                url=self.phantomjs_proxy, method="POST",
                body=json.dumps(fetch), **request_conf)
        except Exception as e:
            raise gen.Return(handle_error(e))

        try:
            response = yield gen.maybe_future(self.http_client.fetch(request))
        except tornado.httpclient.HTTPError as e:
            if e.response:
                response = e.response
            else:
                raise gen.Return(handle_error(e))

        if not response.body:
            raise gen.Return(handle_error(Exception('no response from phantomjs: %r' % response)))

        result = {}
        try:
            result = json.loads(utils.text(response.body))
            assert 'status_code' in result, result
        except Exception as e:
            if response.error:
                result['error'] = utils.text(response.error)
            raise gen.Return(handle_error(e))

        if result.get('status_code', 200):
            logger.info("[%d] %s:%s %s %.2fs", result['status_code'],
                        task.get('project'), task.get('taskid'), url, result['time'])
        else:
            logger.error("[%d] %s:%s %s, %r %.2fs", result['status_code'],
                         task.get('project'), task.get('taskid'),
                         url, result['content'], result['time'])

        raise gen.Return(result)

    @gen.coroutine
    def splash_fetch(self, url, task):
        '''Fetch with splash'''
        start_time = time.time()
        self.on_fetch('splash', task)
        handle_error = lambda x: self.handle_error('splash', url, task, start_time, x)

        # check phantomjs proxy is enabled
        if not self.splash_endpoint:
            result = {
                "orig_url": url,
                "content": "splash is not enabled.",
                "headers": {},
                "status_code": 501,
                "url": url,
                "time": time.time() - start_time,
                "cookies": {},
                "save": task.get('fetch', {}).get('save')
            }
            logger.warning("[501] %s:%s %s 0s", task.get('project'), task.get('taskid'), url)
            raise gen.Return(result)

    @gen.coroutine
    def puppeteer_fetch(self, url, task):
        '''Fetch with puppeteer'''
        start_time = time.time()
        self.on_fetch('puppeteer', task)
        handle_error = lambda x: self.handle_error('puppeteer', url, task, start_time, x)

        # check puppeteer endpoint is enabled
        if not self.puppeteer_endpoint:
            result = {
                "orig_url": url,
                "content": "puppeteer is not enabled.",
                "headers": {},
                "status_code": 501,
                "url": url,
                "time": time.time() - start_time,
                "cookies": {},
                "save": task.get('fetch', {}).get('save')
            }
            logger.warning("[501] %s:%s %s 0s", task.get('project'), task.get('taskid'), url)
            raise gen.Return(result)

        # setup request parameters
        fetch = self.pack_tornado_request_parameters(url, task)
        task_fetch = task.get('fetch', {})
        for each in task_fetch:
            if each not in fetch:
                fetch[each] = task_fetch[each]

        # robots.txt
        if task_fetch.get('robots_txt', False):
            user_agent = fetch['headers']['User-Agent']
            can_fetch = yield self.can_fetch(user_agent, url)
            if not can_fetch:
                error = tornado.httpclient.HTTPError(403, 'Disallowed by robots.txt')
                raise gen.Return(handle_error(error))

        request_conf = {
            'follow_redirects': False,
            'headers': {
                'Content-Type': 'application/json',
            }
        }
        request_conf['connect_timeout'] = fetch.get('connect_timeout', 20)
        request_conf['request_timeout'] = fetch.get('request_timeout', 120) + 1

        session = cookies.RequestsCookieJar()
        if 'Cookie' in fetch['headers']:
            c = http_cookies.SimpleCookie()
            try:
                c.load(fetch['headers']['Cookie'])
            except AttributeError:
                c.load(utils.utf8(fetch['headers']['Cookie']))
            for key in c:
                session.set(key, c[key])
            del fetch['headers']['Cookie']
        if 'cookies' in fetch:
            session.update(fetch['cookies'])
            del fetch['cookies']

        request = tornado.httpclient.HTTPRequest(url=fetch['url'])
        cookie_header = cookies.get_cookie_header(session, request)
        if cookie_header:
            fetch['headers']['Cookie'] = cookie_header

        # making requests
        fetch['headers'] = dict(fetch['headers'])
        try:
            request = tornado.httpclient.HTTPRequest(
                url=self.puppeteer_endpoint, method="POST",
                body=json.dumps(fetch), **request_conf)
        except Exception as e:
            raise gen.Return(handle_error(e))

        try:
            response = yield gen.maybe_future(self.http_client.fetch(request))
        except tornado.httpclient.HTTPError as e:
            if e.response:
                response = e.response
            else:
                raise gen.Return(handle_error(e))

        if not response.body:
            raise gen.Return(handle_error(Exception('no response from puppeteer: %r' % response)))

        result = {}
        try:
            result = json.loads(utils.text(response.body))
            assert 'status_code' in result, result
        except Exception as e:
            if response.error:
                result['error'] = utils.text(response.error)
            raise gen.Return(handle_error(e))

        if result.get('status_code', 200):
            logger.info("[%d] %s:%s %s %.2fs", result['status_code'],
                        task.get('project'), task.get('taskid'), url, result['time'])
        else:
            logger.error("[%d] %s:%s %s, %r %.2fs", result['status_code'],
                         task.get('project'), task.get('taskid'),
                         url, result['content'], result['time'])

        raise gen.Return(result)

    @gen.coroutine
    def puppeteer_fetch(self, url, task):
        '''Fetch with puppeteer proxy'''
        start_time = time.time()
        self.on_fetch('puppeteer', task)
        handle_error = lambda x: self.handle_error('puppeteer', url, task, start_time, x)

        # check puppeteer proxy is enabled
        if not self.puppeteer_proxy:
            result = {
                "orig_url": url,
                "content": "puppeteer is not enabled.",
                "headers": {},
                "status_code": 501,
                "url": url,
                "time": time.time() - start_time,
                "cookies": {},
                "save": task.get('fetch', {}).get('save')
            }
            logger.warning("[501] %s:%s %s 0s", task.get('project'), task.get('taskid'), url)
            raise gen.Return(result)

        # setup request parameters
        fetch = self.pack_tornado_request_parameters(url, task)
        task_fetch = task.get('fetch', {})
        for each in task_fetch:
            if each not in fetch:
                fetch[each] = task_fetch[each]

        # robots.txt
        if task_fetch.get('robots_txt', False):
            user_agent = fetch['headers']['User-Agent']
            can_fetch = yield self.can_fetch(user_agent, url)
            if not can_fetch:
                error = tornado.httpclient.HTTPError(403, 'Disallowed by robots.txt')
                raise gen.Return(handle_error(error))

        request_conf = {
            'follow_redirects': False
        }
        request_conf['connect_timeout'] = fetch.get('connect_timeout', 20)
        request_conf['request_timeout'] = fetch.get('request_timeout', 120) + 1

        session = cookies.RequestsCookieJar()
        if 'Cookie' in fetch['headers']:
            c = http_cookies.SimpleCookie()
            try:
                c.load(fetch['headers']['Cookie'])
            except AttributeError:
                c.load(utils.utf8(fetch['headers']['Cookie']))
            for key in c:
                session.set(key, c[key])
            del fetch['headers']['Cookie']
        if 'cookies' in fetch:
            session.update(fetch['cookies'])
            del fetch['cookies']

        request = tornado.httpclient.HTTPRequest(url=fetch['url'])
        cookie_header = cookies.get_cookie_header(session, request)
        if cookie_header:
            fetch['headers']['Cookie'] = cookie_header

        logger.info("%s", self.puppeteer_proxy)
        # making requests
        fetch['headers'] = dict(fetch['headers'])
        headers = {}
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        try:
            request = tornado.httpclient.HTTPRequest(
                url=self.puppeteer_proxy, method="POST", headers=headers,
                body=json.dumps(fetch), **request_conf)
        except Exception as e:
            raise gen.Return(handle_error(e))

        try:
            response = yield gen.maybe_future(self.http_client.fetch(request))
        except tornado.httpclient.HTTPError as e:
            if e.response:
                response = e.response
            else:
                raise gen.Return(handle_error(e))

        if not response.body:
            raise gen.Return(handle_error(Exception('no response from puppeteer: %r' % response)))

        result = {}
        try:
            result = json.loads(utils.text(response.body))
            assert 'status_code' in result, result
        except Exception as e:
            if response.error:
                result['error'] = utils.text(response.error)
            raise gen.Return(handle_error(e))

        if result.get('status_code', 200):
            logger.info("[%d] %s:%s %s %.2fs", result['status_code'],
                        task.get('project'), task.get('taskid'), url, result['time'])
        else:
            logger.error("[%d] %s:%s %s, %r %.2fs", result['status_code'],
                         task.get('project'), task.get('taskid'),
                         url, result['content'], result['time'])

        raise gen.Return(result)

    @gen.coroutine
    def playwright_fetch(self, url, task):
        '''Fetch with playwright proxy'''
        start_time = time.time()
        self.on_fetch('playwright', task)
        handle_error = lambda x: self.handle_error('playwright', url, task, start_time, x)

        # Check if playwright proxy is enabled
        if not self.playwright_proxy:
            result = {
                "orig_url": url,
                "content": "playwright is not enabled.",
                "headers": {},
                "status_code": 501,
                "url": url,
                "time": time.time() - start_time,
                "cookies": {},
                "save": task.get('fetch', {}).get('save')
            }
            logger.warning("[501] %s:%s %s 0s", task.get('project'), task.get('taskid'), url)
            raise gen.Return(result)

        # Prepare request
        fetch = copy.deepcopy(task.get('fetch', {}))
        fetch['url'] = url
        fetch['headers'] = dict(fetch.get('headers', {}))

        # Set timeout
        request_conf = {
            'connect_timeout': fetch.get('connect_timeout', 20),
            'request_timeout': fetch.get('timeout', 120) + 1,
        }

        # Make request to playwright server
        try:
            request = tornado.httpclient.HTTPRequest(
                url=self.playwright_proxy,
                method="POST",
                headers={'Content-Type': 'application/json'},
                body=json.dumps(fetch),
                **request_conf
            )
        except Exception as e:
            raise gen.Return(handle_error(e))

        try:
            response = yield gen.maybe_future(self.http_client.fetch(request))
        except tornado.httpclient.HTTPError as e:
            if e.response:
                response = e.response
            else:
                raise gen.Return(handle_error(e))

        if not response.body:
            raise gen.Return(handle_error(Exception('no response from playwright')))

        try:
            result = json.loads(utils.text(response.body))
            if 'status_code' not in result:
                raise ValueError('status_code not in response')
        except Exception as e:
            raise gen.Return(handle_error(e))

        raise gen.Return(result)

    @gen.coroutine
    def py_playwright_fetch(self, url, task):
        '''Fetch with Python Playwright'''
        start_time = time.time()
        self.on_fetch('py_playwright', task)
        handle_error = lambda x: self.handle_error('py_playwright', url, task, start_time, x)

        # Check if py_playwright proxy is enabled
        if not self.py_playwright_proxy:
            result = {
                "orig_url": url,
                "content": "py_playwright is not enabled.",
                "headers": {},
                "status_code": 501,
                "url": url,
                "time": time.time() - start_time,
                "cookies": {},
                "save": task.get('fetch', {}).get('save')
            }
            logger.warning("[501] %s:%s %s 0s", task.get('project'), task.get('taskid'), url)
            raise gen.Return(result)

        # Prepare request
        fetch = copy.deepcopy(task.get('fetch', {}))
        fetch['url'] = url
        fetch['headers'] = dict(fetch.get('headers', {}))

        # Set timeout
        request_conf = {
            'connect_timeout': fetch.get('connect_timeout', 20),
            'request_timeout': fetch.get('timeout', 120) + 1,
        }

        try:
            request = tornado.httpclient.HTTPRequest(
                url=self.py_playwright_proxy,
                method="POST",
                headers={'Content-Type': 'application/json'},
                body=json.dumps(fetch),
                **request_conf
            )
        except Exception as e:
            raise gen.Return(handle_error(e))

        try:
            response = yield gen.maybe_future(self.http_client.fetch(request))
        except tornado.httpclient.HTTPError as e:
            if e.response:
                response = e.response
            else:
                raise gen.Return(handle_error(e))

        if not response.body:
            raise gen.Return(handle_error(Exception('no response from py_playwright')))

        try:
            result = json.loads(utils.text(response.body))
            if 'status_code' not in result:
                raise ValueError('status_code not in response')
        except Exception as e:
            raise gen.Return(handle_error(e))

        raise gen.Return(result)

    def run(self):
        '''Run loop'''
        logger.info("fetcher starting...")

        def queue_loop():
            if not self.outqueue or not self.inqueue:
                return
            while not self._quit:
                try:
                    if self.outqueue.full():
                        break
                    if self.http_client.free_size() <= 0:
                        break
                    task = self.inqueue.get_nowait()
                    # FIXME: decode unicode_obj should used after data selete from
                    # database, it's used here for performance
                    task = utils.decode_unicode_obj(task)
                    self.fetch(task)
                except Exception as empty_error:  # Handle queue.Empty
                    break
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.exception(e)
                    break

        tornado.ioloop.PeriodicCallback(queue_loop, 100).start()
        tornado.ioloop.PeriodicCallback(self.clear_robot_txt_cache, 10000).start()
        self._running = True

        try:
            self.ioloop.start()
        except KeyboardInterrupt:
            pass

        logger.info("fetcher exiting...")

    def quit(self):
        '''Quit fetcher'''
        self._running = False
        self._quit = True
        self.ioloop.add_callback(self.ioloop.stop)
        if hasattr(self, 'xmlrpc_server'):
            self.xmlrpc_ioloop.add_callback(self.xmlrpc_server.stop)
            self.xmlrpc_ioloop.add_callback(self.xmlrpc_ioloop.stop)

    def size(self):
        return self.http_client.size()

    def xmlrpc_run(self, port=24444, bind='127.0.0.1', log_requests=False):
        '''Run xmlrpc server'''
        import umsgpack
        from pyspider.libs.wsgi_xmlrpc import WSGIXMLRPCApplication
        try:
            from xmlrpc.client import Binary
        except ImportError:
            from xmlrpclib import Binary

        application = WSGIXMLRPCApplication()

        application.register_function(self.quit, '_quit')
        application.register_function(self.size)

        def sync_fetch(task):
            result = self.sync_fetch(task)
            result = Binary(umsgpack.packb(result))
            return result
        application.register_function(sync_fetch, 'fetch')

        def dump_counter(_time, _type):
            return self._cnt[_time].to_dict(_type)
        application.register_function(dump_counter, 'counter')

        import tornado.wsgi
        import tornado.ioloop
        import tornado.httpserver

        container = tornado.wsgi.WSGIContainer(application)
        self.xmlrpc_ioloop = tornado.ioloop.IOLoop.current()
        self.xmlrpc_server = tornado.httpserver.HTTPServer(container)
        self.xmlrpc_server.listen(port=port, address=bind)
        logger.info('fetcher.xmlrpc listening on %s:%s', bind, port)
        self.xmlrpc_ioloop.start()

    def on_fetch(self, fetch_type, task):
        '''Called before task fetch'''
        logger.info('on fetch %s:%s', fetch_type, task)

    def on_result(self, fetch_type, task, result):
        '''Called after task fetched'''
        status_code = result.get('status_code', 599)
        if status_code != 599:
            status_code = (int(status_code) // 100 * 100)  # Use integer division for Python 3
        self._cnt['5m'].event((task.get('project'), status_code), +1)
        self._cnt['1h'].event((task.get('project'), status_code), +1)

        if fetch_type in ('http', 'phantomjs') and result.get('time'):
            content_len = len(result.get('content', ''))
            self._cnt['5m'].event((task.get('project'), 'speed'),
                                  float(content_len) / result.get('time'))
            self._cnt['1h'].event((task.get('project'), 'speed'),
                                  float(content_len) / result.get('time'))
            self._cnt['5m'].event((task.get('project'), 'time'), result.get('time'))
            self._cnt['1h'].event((task.get('project'), 'time'), result.get('time'))
