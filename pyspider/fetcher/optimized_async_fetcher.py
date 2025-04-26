#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-05-01 12:00:00

"""
Optimized asynchronous fetcher for PySpider
"""

import time
import json
import copy
import asyncio
import logging
import traceback
from typing import Dict, Any, Optional, List, Tuple, Union, Callable

import aiohttp
from aiohttp import ClientTimeout, TCPConnector

from pyspider.libs import utils
from pyspider.libs.url import quote_chinese
from pyspider.libs.metrics import metrics
from pyspider.libs.errors import (
    NetworkError, TimeoutError, HTTPError, ProxyError,
    DNSError, SSLError, convert_exception
)
from pyspider.libs.memory_optimizer import memory_optimizer
from pyspider.fetcher.connection_pool_optimizer import connection_pool_optimizer

logger = logging.getLogger('optimized_async_fetcher')

class OptimizedAsyncFetcher:
    """
    Optimized asynchronous fetcher using aiohttp with memory and connection pool optimization
    """

    def __init__(self,
                 user_agent: str = None,
                 poolsize: int = None,
                 proxy: str = None,
                 timeout: int = 60,
                 puppeteer_proxy: str = None,
                 playwright_proxy: str = None,
                 py_playwright_proxy: str = None,
                 splash_endpoint: str = None,
                 memory_check_interval: int = 60,
                 pool_check_interval: int = 30,
                 auto_optimize: bool = True):
        """
        Initialize OptimizedAsyncFetcher

        Args:
            user_agent: User agent
            poolsize: Connection pool size
            proxy: Proxy
            timeout: Default timeout in seconds
            puppeteer_proxy: Puppeteer proxy endpoint
            playwright_proxy: Playwright proxy endpoint
            py_playwright_proxy: Python Playwright proxy endpoint
            splash_endpoint: Splash endpoint
            memory_check_interval: Interval between memory checks in seconds
            pool_check_interval: Interval between pool size checks in seconds
            auto_optimize: Whether to automatically optimize resources
        """
        self.user_agent = user_agent
        self.proxy = proxy
        self.timeout = timeout
        self.puppeteer_proxy = puppeteer_proxy
        self.playwright_proxy = playwright_proxy
        self.py_playwright_proxy = py_playwright_proxy
        self.splash_endpoint = splash_endpoint

        # Initialize optimizers
        self.memory_optimizer = memory_optimizer
        self.memory_optimizer.check_interval = memory_check_interval

        self.connection_pool_optimizer = connection_pool_optimizer
        self.connection_pool_optimizer.check_interval = pool_check_interval

        # Set initial pool size
        if poolsize is not None:
            self.connection_pool_optimizer.current_pool_size = poolsize

        # Default options
        self.default_options = {
            'method': 'GET',
            'headers': {
                'User-Agent': self.user_agent or 'pyspider/1.0',
            },
            'timeout': self.timeout,
            'allow_redirects': True,
        }

        # Session and state
        self.session = None
        self.robots_txt_cache = {}
        self._active_connections = 0
        self._queue_size = 0
        self._initialized = False

        # Start optimizers if auto-optimize is enabled
        if auto_optimize:
            self.memory_optimizer.start()
            self.connection_pool_optimizer.start()

        logger.info(f"Optimized async fetcher initialized with poolsize={self.connection_pool_optimizer.current_pool_size}, "
                   f"timeout={timeout}s, auto_optimize={auto_optimize}")

    async def init(self):
        """
        Initialize the fetcher
        """
        if self._initialized:
            return

        # Get pool size from optimizer
        pool_size = self.connection_pool_optimizer.get_pool_size()

        # Create a ClientSession with an optimized connection pool
        connector = TCPConnector(limit=pool_size, ssl=False)
        self.session = aiohttp.ClientSession(connector=connector)

        self._initialized = True
        logger.info(f"Optimized async fetcher initialized with pool size {pool_size}")

    async def close(self):
        """
        Close the fetcher
        """
        if not self._initialized:
            return

        # Close session
        if self.session:
            await self.session.close()
            self.session = None

        # Stop optimizers
        self.memory_optimizer.stop()
        self.connection_pool_optimizer.stop()

        self._initialized = False
        logger.info("Optimized async fetcher closed")

    async def async_fetch(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch a task asynchronously

        Args:
            task: Task to fetch

        Returns:
            Fetch result
        """
        # Initialize session if needed
        if not self._initialized:
            await self.init()

        url = task.get('url', 'data:,')
        if url.startswith('data:'):
            return self.data_fetch(url, task)

        # Record metrics
        task_tags = {
            'project': task.get('project', ''),
            'taskid': task.get('taskid', '')
        }

        # Update queue size
        self._queue_size += 1
        self.connection_pool_optimizer.set_queue_size(self._queue_size)

        with metrics.timer('fetch_time', task_tags):
            try:
                # Update active connections
                self._active_connections += 1
                self.connection_pool_optimizer.set_active_connections(self._active_connections)

                # Choose fetch method based on fetch type
                fetch_type = task.get('fetch', {}).get('fetch_type', 'http')

                if fetch_type == 'http':
                    result = await self.http_fetch(url, task)
                elif fetch_type == 'puppeteer':
                    result = await self.puppeteer_fetch(url, task)
                elif fetch_type == 'playwright':
                    result = await self.playwright_fetch(url, task)
                elif fetch_type == 'py_playwright':
                    result = await self.py_playwright_fetch(url, task)
                elif fetch_type == 'splash':
                    result = await self.splash_fetch(url, task)
                else:
                    result = await self.http_fetch(url, task)

                # Record success metrics
                metrics.increment('fetch_success', tags=task_tags)

                # Log result
                if result.get('status_code', 200) < 300:
                    logger.info("[%d] %s:%s %s %.2fs",
                                result['status_code'],
                                task.get('project'), task.get('taskid'),
                                url, result['time'])
                else:
                    logger.warning("[%d] %s:%s %s %.2fs",
                                   result['status_code'],
                                   task.get('project'), task.get('taskid'),
                                   url, result['time'])

                return result
            except Exception as e:
                # Convert exception to PySpider exception
                error = convert_exception(e)

                # Record error metrics
                error_type = type(error).__name__
                metrics.increment(f'fetch_error_{error_type.lower()}', tags=task_tags)

                # Handle error
                result = self.handle_error(fetch_type, url, task, time.time(), error)

                # Log error
                logger.error("[%d] %s:%s %s, %r %.2fs",
                             result['status_code'], task.get('project'), task.get('taskid'),
                             url, error, result['time'])

                return result
            finally:
                # Update active connections and queue size
                self._active_connections -= 1
                self._queue_size -= 1
                self.connection_pool_optimizer.set_active_connections(self._active_connections)
                self.connection_pool_optimizer.set_queue_size(self._queue_size)

                # Check if memory optimization is needed
                if self._active_connections == 0 and self._queue_size == 0:
                    # No active tasks, good time to optimize memory
                    self.memory_optimizer.check_memory()

    def data_fetch(self, url: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch data URL

        Args:
            url: Data URL
            task: Task

        Returns:
            Fetch result
        """
        start_time = time.time()

        result = {
            'status_code': 200,
            'url': url,
            'orig_url': url,
            'content': url[5:],
            'headers': {},
            'cookies': {},
            'time': time.time() - start_time,
            'save': task.get('fetch', {}).get('save')
        }

        return result

    async def http_fetch(self, url: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch with aiohttp

        Args:
            url: URL to fetch
            task: Task

        Returns:
            Fetch result
        """
        start_time = time.time()

        # Check robots.txt
        if task.get('fetch', {}).get('robots_txt', False):
            can_fetch = await self.can_fetch(url, task)
            if not can_fetch:
                result = {
                    'status_code': 403,
                    'error': 'Disallowed by robots.txt',
                    'url': url,
                    'orig_url': url,
                    'content': 'Disallowed by robots.txt',
                    'headers': {},
                    'cookies': {},
                    'time': time.time() - start_time,
                    'save': task.get('fetch', {}).get('save')
                }
                return result

        # Prepare request parameters
        options = copy.deepcopy(self.default_options)
        fetch = copy.deepcopy(task.get('fetch', {}))

        # Update options with fetch parameters
        for key in fetch:
            if key in options:
                options[key] = fetch[key]

        # Handle headers
        headers = options.get('headers', {})
        if isinstance(headers, list):
            headers = dict(headers)
        if 'User-Agent' not in headers and fetch.get('user_agent'):
            headers['User-Agent'] = fetch['user_agent']
        options['headers'] = headers

        # Handle cookies
        cookies = {}
        if 'cookies' in fetch:
            cookies.update(fetch['cookies'])

        # Handle proxy
        proxy = None
        if fetch.get('proxy'):
            proxy = fetch['proxy']
        elif self.proxy and fetch.get('proxy', True):
            proxy = self.proxy

        # Handle timeout
        timeout = ClientTimeout(
            total=options.get('timeout', self.timeout),
            connect=fetch.get('connect_timeout', 20)
        )

        # Make request
        try:
            method = options.get('method', 'GET').upper()

            # Prepare URL
            url = quote_chinese(url)

            # Prepare request kwargs
            kwargs = {
                'method': method,
                'url': url,
                'headers': headers,
                'cookies': cookies,
                'timeout': timeout,
                'allow_redirects': options.get('allow_redirects', True),
                'max_redirects': options.get('max_redirects', 10),
                'ssl': options.get('verify_ssl', False)
            }

            # Add proxy if needed
            if proxy:
                kwargs['proxy'] = proxy

            # Add data if needed
            if method in ('POST', 'PUT', 'PATCH'):
                if 'data' in options:
                    kwargs['data'] = options['data']
                if 'json' in options:
                    kwargs['json'] = options['json']
                if 'files' in options:
                    # aiohttp doesn't support files directly, need to use FormData
                    form = aiohttp.FormData()
                    for key, value in options['files'].items():
                        form.add_field(key, value)
                    kwargs['data'] = form

            # Make request
            async with self.session.request(**kwargs) as response:
                # Get content
                content = await response.read()

                # Get cookies
                cookies = {}
                for cookie in response.cookies.values():
                    cookies[cookie.key] = cookie.value

                # Prepare result
                result = {
                    'status_code': response.status,
                    'url': str(response.url),
                    'orig_url': url,
                    'content': content,
                    'headers': dict(response.headers),
                    'cookies': cookies,
                    'time': time.time() - start_time,
                    'save': task.get('fetch', {}).get('save')
                }

                # Handle redirect
                if response.history:
                    result['redirect_url'] = str(response.url)

                return result
        except aiohttp.ClientError as e:
            # Convert exception
            error = convert_exception(e)
            raise error
        except asyncio.TimeoutError:
            raise TimeoutError(f"Timeout after {timeout.total} seconds")
        except Exception as e:
            raise e

    async def puppeteer_fetch(self, url: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch with puppeteer proxy

        Args:
            url: URL to fetch
            task: Task

        Returns:
            Fetch result
        """
        start_time = time.time()

        # Check if puppeteer proxy is enabled
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
            return result

        # Prepare request
        fetch = copy.deepcopy(task.get('fetch', {}))
        fetch['url'] = url
        fetch['headers'] = dict(fetch.get('headers', {}))

        # Set timeout
        timeout = ClientTimeout(
            total=fetch.get('timeout', 120) + 1,
            connect=fetch.get('connect_timeout', 20)
        )

        try:
            # Make request to puppeteer server
            async with self.session.post(
                self.puppeteer_proxy,
                json=fetch,
                headers={'Content-Type': 'application/json'},
                timeout=timeout
            ) as response:
                # Check response
                if response.status != 200:
                    text = await response.text()
                    raise HTTPError(response.status, f"Puppeteer proxy error: {text}")

                # Parse response
                result = await response.json()

                # Add time
                result['time'] = time.time() - start_time

                # Add save
                result['save'] = task.get('fetch', {}).get('save')

                return result
        except Exception as e:
            # Convert exception
            error = convert_exception(e)
            raise error

    async def playwright_fetch(self, url: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch with playwright proxy

        Args:
            url: URL to fetch
            task: Task

        Returns:
            Fetch result
        """
        start_time = time.time()

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
            return result

        # Prepare request
        fetch = copy.deepcopy(task.get('fetch', {}))
        fetch['url'] = url
        fetch['headers'] = dict(fetch.get('headers', {}))

        # Set timeout
        timeout = ClientTimeout(
            total=fetch.get('timeout', 120) + 1,
            connect=fetch.get('connect_timeout', 20)
        )

        try:
            # Make request to playwright server
            async with self.session.post(
                self.playwright_proxy,
                json=fetch,
                headers={'Content-Type': 'application/json'},
                timeout=timeout
            ) as response:
                # Check response
                if response.status != 200:
                    text = await response.text()
                    raise HTTPError(response.status, f"Playwright proxy error: {text}")

                # Parse response
                result = await response.json()

                # Add time
                result['time'] = time.time() - start_time

                # Add save
                result['save'] = task.get('fetch', {}).get('save')

                return result
        except Exception as e:
            # Convert exception
            error = convert_exception(e)
            raise error

    async def py_playwright_fetch(self, url: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch with Python Playwright

        Args:
            url: URL to fetch
            task: Task

        Returns:
            Fetch result
        """
        start_time = time.time()

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
            return result

        # Prepare request
        fetch = copy.deepcopy(task.get('fetch', {}))
        fetch['url'] = url
        fetch['headers'] = dict(fetch.get('headers', {}))

        # Set timeout
        timeout = ClientTimeout(
            total=fetch.get('timeout', 120) + 1,
            connect=fetch.get('connect_timeout', 20)
        )

        try:
            # Make request to py_playwright server
            async with self.session.post(
                self.py_playwright_proxy,
                json=fetch,
                headers={'Content-Type': 'application/json'},
                timeout=timeout
            ) as response:
                # Check response
                if response.status != 200:
                    text = await response.text()
                    raise HTTPError(response.status, f"Python Playwright proxy error: {text}")

                # Parse response
                result = await response.json()

                # Add time
                result['time'] = time.time() - start_time

                # Add save
                result['save'] = task.get('fetch', {}).get('save')

                return result
        except Exception as e:
            # Convert exception
            error = convert_exception(e)
            raise error

    async def splash_fetch(self, url: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch with splash

        Args:
            url: URL to fetch
            task: Task

        Returns:
            Fetch result
        """
        start_time = time.time()

        # Check if splash is enabled
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
            return result

        # Prepare request
        fetch = copy.deepcopy(task.get('fetch', {}))
        fetch['url'] = url
        fetch['headers'] = dict(fetch.get('headers', {}))

        # Set timeout
        timeout = ClientTimeout(
            total=fetch.get('timeout', 120) + 1,
            connect=fetch.get('connect_timeout', 20)
        )

        # Add Lua script
        fetch['lua_source'] = """
        function main(splash, args)
            splash:init_cookies(args.cookies)
            assert(splash:go{
                url=args.url,
                headers=args.headers,
                http_method=args.method,
                body=args.body,
                timeout=args.timeout
            })
            assert(splash:wait(args.wait))

            local entries = splash:history()
            local last_entry = entries[#entries]
            local response = {
                url = splash:url(),
                cookies = splash:get_cookies(),
                headers = last_entry.response.headers,
                status_code = last_entry.response.status,
                content = splash:html()
            }
            return response
        end
        """

        try:
            # Make request to splash server
            async with self.session.post(
                self.splash_endpoint,
                json=fetch,
                headers={'Content-Type': 'application/json'},
                timeout=timeout
            ) as response:
                # Check response
                if response.status != 200:
                    text = await response.text()
                    raise HTTPError(response.status, f"Splash error: {text}")

                # Parse response
                data = await response.json()

                # Prepare result
                result = {
                    'status_code': data.get('status_code', response.status),
                    'url': data.get('url', url),
                    'orig_url': url,
                    'content': data.get('content', ''),
                    'headers': data.get('headers', {}),
                    'cookies': data.get('cookies', {}),
                    'time': time.time() - start_time,
                    'save': task.get('fetch', {}).get('save')
                }

                return result
        except Exception as e:
            # Convert exception
            error = convert_exception(e)
            raise error

    def handle_error(self, fetch_type: str, url: str, task: Dict[str, Any],
                     start_time: float, error: Exception) -> Dict[str, Any]:
        """
        Handle fetch error

        Args:
            fetch_type: Fetch type
            url: URL
            task: Task
            start_time: Start time
            error: Error

        Returns:
            Error result
        """
        result = {
            'status_code': getattr(error, 'status_code', 599),
            'error': str(error),
            'traceback': traceback.format_exc() if error.__traceback__ else None,
            'content': "",
            'time': time.time() - start_time,
            'orig_url': url,
            'url': url,
            "save": task.get('fetch', {}).get('save')
        }

        return result

    async def can_fetch(self, url: str, task: Dict[str, Any]) -> bool:
        """
        Check if URL can be fetched according to robots.txt

        Args:
            url: URL to check
            task: Task

        Returns:
            True if URL can be fetched, False otherwise
        """
        from urllib.parse import urlparse, urljoin
        from urllib.robotparser import RobotFileParser

        parsed_url = urlparse(url)
        robots_url = urljoin(url, '/robots.txt')
        user_agent = task.get('fetch', {}).get('user_agent', self.user_agent)

        # Check cache
        key = (parsed_url.netloc, user_agent)
        if key in self.robots_txt_cache:
            rp, last_check = self.robots_txt_cache[key]
            # Cache for 1 day
            if time.time() - last_check < 24 * 60 * 60:
                return rp.can_fetch(user_agent, url)

        # Fetch robots.txt
        rp = RobotFileParser()
        rp.url = robots_url

        try:
            # Create a simple task for fetching robots.txt
            robots_task = {
                'url': robots_url,
                'fetch': {
                    'method': 'GET',
                    'headers': {
                        'User-Agent': user_agent or 'pyspider/%s' % utils.__version__,
                    },
                    'timeout': 10,
                    'robots_txt': False  # Avoid infinite recursion
                }
            }

            # Fetch robots.txt
            result = await self.http_fetch(robots_url, robots_task)

            if result['status_code'] == 200:
                # Parse robots.txt
                rp.parse(result['content'].decode('utf-8', 'ignore').splitlines())
            else:
                # If robots.txt is not available, allow all
                rp = RobotFileParser()
                rp.allow_all = True
        except Exception as e:
            logger.error("Error fetching robots.txt: %s", e)
            # If error, allow all
            rp = RobotFileParser()
            rp.allow_all = True

        # Update cache
        self.robots_txt_cache[key] = (rp, time.time())

        # Check if URL can be fetched
        return rp.can_fetch(user_agent, url)

    async def clear_robots_txt_cache(self) -> None:
        """
        Clear robots.txt cache
        """
        self.robots_txt_cache = {}

    def get_stats(self) -> Dict[str, Any]:
        """
        Get fetcher statistics

        Returns:
            Fetcher statistics
        """
        return {
            'active_connections': self._active_connections,
            'queue_size': self._queue_size,
            'pool_size': self.connection_pool_optimizer.get_pool_size(),
            'memory': self.memory_optimizer.get_memory_usage(),
            'pool': self.connection_pool_optimizer.get_pool_stats()
        }

    def xmlrpc_run(self, port=24444, bind='127.0.0.1'):
        """
        Run XML-RPC server for compatibility with standard fetcher

        Args:
            port: Port to listen on
            bind: Address to bind to
        """
        import tornado.ioloop
        import tornado.web
        import tornado.wsgi
        import tornado.httpserver
        from pyspider.libs.wsgi_xmlrpc import WSGIXMLRPCApplication
        import umsgpack

        application = WSGIXMLRPCApplication()

        application.register_function(self.fetch_sync, 'fetch')
        application.register_function(self.get_stats, 'get_stats')

        container = tornado.wsgi.WSGIContainer(application)
        self.xmlrpc_ioloop = tornado.ioloop.IOLoop.current()
        self.xmlrpc_server = tornado.httpserver.HTTPServer(container)
        self.xmlrpc_server.listen(port=port, address=bind)

        logger.info("fetcher.xmlrpc listening on %s:%s", bind, port)
        self.xmlrpc_ioloop.start()

    def fetch_sync(self, task):
        """
        Synchronous fetch for XML-RPC compatibility

        Args:
            task: Task to fetch

        Returns:
            Fetch result
        """
        import asyncio
        import umsgpack

        # Create event loop if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Fetch task
        result = loop.run_until_complete(self.async_fetch(task))

        # Pack result for XML-RPC
        return {"data": umsgpack.packb(result)}

    def run(self):
        """
        Run the fetcher

        This method is called by the PySpider framework to start the fetcher.
        It initializes the fetcher and starts processing tasks from the input queue.
        """
        import asyncio

        # Create event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Initialize fetcher
        loop.run_until_complete(self.init())

        try:
            # Process tasks from input queue
            if hasattr(self, 'inqueue') and self.inqueue:
                logger.info("Fetcher starting to process tasks from queue")

                async def process_queue():
                    while True:
                        try:
                            # Get task from queue
                            task = await loop.run_in_executor(None, self.inqueue.get)

                            # Process task
                            try:
                                result = await self.async_fetch(task)

                                # Put result in output queue
                                if hasattr(self, 'outqueue') and self.outqueue:
                                    await loop.run_in_executor(None, lambda: self.outqueue.put(result))
                            except Exception as e:
                                logger.error(f"Error processing task: {e}")
                        except Exception as e:
                            logger.error(f"Error getting task from queue: {e}")
                            await asyncio.sleep(1)

                # Run queue processing
                loop.run_until_complete(process_queue())
            else:
                # No input queue, just keep the process running
                logger.info("Fetcher running without input queue")
                loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Fetcher stopped by user")
        except Exception as e:
            logger.error(f"Fetcher error: {e}")
        finally:
            # Close fetcher
            loop.run_until_complete(self.close())

            # Close event loop
            loop.close()
