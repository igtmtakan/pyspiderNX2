#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-05-01 12:00:00

"""
Playwright manager for PySpider
"""

import os
import time
import asyncio
import logging
import traceback
from typing import Dict, Any, Optional, List, Tuple, Union, Callable

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext, Response
    has_playwright = True
except ImportError:
    has_playwright = False

from pyspider.libs.metrics import metrics
from pyspider.libs.errors import (
    NetworkError, TimeoutError, HTTPError, ProxyError, 
    DNSError, SSLError, ProcessError, ScriptError, ParseError
)

logger = logging.getLogger('playwright_manager')

class PlaywrightManager:
    """
    Playwright manager for PySpider
    """
    
    def __init__(self, 
                 browser_type: str = 'chromium',
                 headless: bool = True,
                 max_pages: int = 10,
                 user_agent: str = None,
                 proxy: str = None,
                 timeout: int = 60,
                 viewport: Dict[str, int] = None,
                 ignore_https_errors: bool = True,
                 slow_mo: int = 0):
        """
        Initialize PlaywrightManager
        
        Args:
            browser_type: Browser type (chromium, firefox, webkit)
            headless: Whether to run browser in headless mode
            max_pages: Maximum number of pages to keep in pool
            user_agent: User agent
            proxy: Proxy
            timeout: Default timeout in seconds
            viewport: Viewport size
            ignore_https_errors: Whether to ignore HTTPS errors
            slow_mo: Slow down operations by the specified amount of milliseconds
        """
        if not has_playwright:
            logger.error("Playwright is not installed. Please install it with 'pip install playwright'")
            return
            
        self.browser_type = browser_type
        self.headless = headless
        self.max_pages = max_pages
        self.user_agent = user_agent
        self.proxy = proxy
        self.timeout = timeout * 1000  # Convert to milliseconds
        self.viewport = viewport or {'width': 1280, 'height': 800}
        self.ignore_https_errors = ignore_https_errors
        self.slow_mo = slow_mo
        
        self._playwright = None
        self._browser = None
        self._page_pool = []
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def init(self):
        """
        Initialize Playwright and browser
        """
        if not has_playwright:
            logger.error("Playwright is not installed. Please install it with 'pip install playwright'")
            return
            
        if self._initialized:
            return
        
        logger.info(f"Initializing Playwright with {self.browser_type} browser")
        
        # Start Playwright
        self._playwright = await async_playwright().start()
        
        # Select browser type
        if self.browser_type == 'chromium':
            browser_factory = self._playwright.chromium
        elif self.browser_type == 'firefox':
            browser_factory = self._playwright.firefox
        elif self.browser_type == 'webkit':
            browser_factory = self._playwright.webkit
        else:
            raise ValueError(f"Unsupported browser type: {self.browser_type}")
        
        # Launch browser
        browser_args = []
        if self.browser_type == 'chromium':
            browser_args = [
                '--disable-gpu',
                '--disable-dev-shm-usage',
                '--disable-setuid-sandbox',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials'
            ]
        
        # Prepare launch options
        launch_options = {
            'headless': self.headless,
            'args': browser_args,
            'slow_mo': self.slow_mo,
            'timeout': self.timeout
        }
        
        # Launch browser
        self._browser = await browser_factory.launch(**launch_options)
        
        # Initialize page pool
        for _ in range(min(3, self.max_pages)):  # Start with a few pages
            page = await self._create_new_page()
            self._page_pool.append(page)
        
        self._initialized = True
        logger.info(f"Playwright initialized with {len(self._page_pool)} pages in pool")
        
        # Record metrics
        metrics.gauge('playwright_pages', len(self._page_pool))
    
    async def close(self):
        """
        Close Playwright and browser
        """
        if not has_playwright:
            return
            
        if not self._initialized:
            return
        
        logger.info("Closing Playwright")
        
        # Close all pages in pool
        for page in self._page_pool:
            await page.close()
        self._page_pool = []
        
        # Close browser
        if self._browser:
            await self._browser.close()
            self._browser = None
        
        # Close Playwright
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        
        self._initialized = False
        logger.info("Playwright closed")
    
    async def _create_new_page(self) -> Page:
        """
        Create a new page
        
        Returns:
            Page
        """
        if not has_playwright:
            raise ImportError("Playwright is not installed")
            
        # Create browser context
        context_options = {
            'viewport': self.viewport,
            'ignore_https_errors': self.ignore_https_errors
        }
        
        # Add user agent if provided
        if self.user_agent:
            context_options['user_agent'] = self.user_agent
        
        # Add proxy if provided
        if self.proxy:
            context_options['proxy'] = {
                'server': self.proxy
            }
        
        # Create context
        context = await self._browser.new_context(**context_options)
        
        # Create page
        page = await context.new_page()
        
        # Set default timeout
        page.set_default_timeout(self.timeout)
        
        return page
    
    async def get_page(self) -> Tuple[Page, bool]:
        """
        Get a page from pool or create a new one
        
        Returns:
            Tuple of (page, is_new)
        """
        if not has_playwright:
            raise ImportError("Playwright is not installed")
            
        async with self._lock:
            if not self._initialized:
                await self.init()
            
            # Try to get a page from pool
            if self._page_pool:
                page = self._page_pool.pop()
                return page, False
            
            # Create a new page if pool is empty
            page = await self._create_new_page()
            
            # Record metrics
            metrics.gauge('playwright_pages', len(self._page_pool))
            metrics.increment('playwright_pages_created')
            
            return page, True
    
    async def release_page(self, page: Page, error: bool = False):
        """
        Release a page back to pool or close it if there was an error
        
        Args:
            page: Page to release
            error: Whether there was an error
        """
        if not has_playwright:
            return
            
        async with self._lock:
            if not self._initialized:
                return
            
            # Close page if there was an error or pool is full
            if error or len(self._page_pool) >= self.max_pages:
                await page.close()
                metrics.increment('playwright_pages_closed')
            else:
                # Clear cookies and cache
                context = page.context
                await context.clear_cookies()
                
                # Navigate to about:blank to release resources
                try:
                    await page.goto('about:blank', wait_until='load', timeout=5000)
                except Exception:
                    # If navigation fails, close the page
                    await page.close()
                    metrics.increment('playwright_pages_closed')
                    return
                
                # Add page back to pool
                self._page_pool.append(page)
            
            # Record metrics
            metrics.gauge('playwright_pages', len(self._page_pool))
    
    async def fetch(self, url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Fetch a URL using Playwright
        
        Args:
            url: URL to fetch
            options: Fetch options
            
        Returns:
            Fetch result
        """
        if not has_playwright:
            return {
                'status_code': 501,
                'error': "Playwright is not installed. Please install it with 'pip install playwright'",
                'content': "",
                'time': 0,
                'orig_url': url,
                'url': url,
                'save': options.get('save') if options else None
            }
            
        options = options or {}
        start_time = time.time()
        page = None
        is_new_page = False
        
        # Record metrics
        metrics.increment('playwright_requests')
        
        try:
            # Get page
            page, is_new_page = await self.get_page()
            
            # Set timeout
            timeout = options.get('timeout', self.timeout)
            
            # Set headers
            if options.get('headers'):
                await page.set_extra_http_headers(options['headers'])
            
            # Set cookies
            if options.get('cookies'):
                cookies = []
                for name, value in options['cookies'].items():
                    cookies.append({
                        'name': name,
                        'value': value,
                        'url': url
                    })
                await page.context.add_cookies(cookies)
            
            # Navigate to URL
            response = await page.goto(
                url,
                timeout=timeout,
                wait_until=options.get('wait_until', 'networkidle'),
                referer=options.get('referer')
            )
            
            if not response:
                raise NetworkError(f"Failed to get response for {url}")
            
            # Wait for selector if provided
            if options.get('wait_for'):
                await page.wait_for_selector(
                    options['wait_for'],
                    timeout=timeout,
                    state=options.get('wait_for_state', 'visible')
                )
            
            # Execute JavaScript if provided
            result = None
            if options.get('script'):
                result = await page.evaluate(options['script'])
            
            # Take screenshot if requested
            screenshot = None
            if options.get('screenshot'):
                screenshot = await page.screenshot(
                    type=options.get('screenshot_type', 'png'),
                    full_page=options.get('full_page', False),
                    path=options.get('screenshot_path')
                )
            
            # Get content
            content = await page.content()
            
            # Get cookies
            cookies = await page.context.cookies()
            cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            
            # Prepare result
            fetch_result = {
                'status_code': response.status,
                'url': page.url,
                'orig_url': url,
                'content': content,
                'headers': dict(response.headers),
                'cookies': cookies_dict,
                'time': time.time() - start_time,
                'save': options.get('save')
            }
            
            # Add screenshot if taken
            if screenshot:
                fetch_result['screenshot'] = screenshot
            
            # Add JavaScript result if executed
            if result is not None:
                fetch_result['script_result'] = result
            
            # Record success metrics
            metrics.increment('playwright_success')
            
            # Release page
            await self.release_page(page)
            
            return fetch_result
        except Exception as e:
            # Record error metrics
            metrics.increment('playwright_error')
            
            # Convert exception
            if 'Timeout' in str(e):
                error = TimeoutError(f"Playwright timeout: {str(e)}")
            elif 'Navigation failed' in str(e):
                error = NetworkError(f"Playwright navigation failed: {str(e)}")
            else:
                error = e
            
            # Release page with error
            if page:
                await self.release_page(page, error=True)
            
            # Prepare error result
            error_result = {
                'status_code': 599,
                'error': str(error),
                'traceback': traceback.format_exc(),
                'content': "",
                'time': time.time() - start_time,
                'orig_url': url,
                'url': url,
                'save': options.get('save')
            }
            
            # Log error
            logger.error(f"Playwright error: {error}", exc_info=True)
            
            return error_result
    
    async def execute_actions(self, url: str, actions: List[Dict[str, Any]], options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a series of actions on a page
        
        Args:
            url: URL to navigate to
            actions: List of actions to execute
            options: Fetch options
            
        Returns:
            Execution result
        """
        if not has_playwright:
            return {
                'status_code': 501,
                'error': "Playwright is not installed. Please install it with 'pip install playwright'",
                'content': "",
                'time': 0,
                'orig_url': url,
                'url': url,
                'save': options.get('save') if options else None
            }
            
        options = options or {}
        start_time = time.time()
        page = None
        is_new_page = False
        
        # Record metrics
        metrics.increment('playwright_actions')
        
        try:
            # Get page
            page, is_new_page = await self.get_page()
            
            # Set timeout
            timeout = options.get('timeout', self.timeout)
            
            # Set headers
            if options.get('headers'):
                await page.set_extra_http_headers(options['headers'])
            
            # Set cookies
            if options.get('cookies'):
                cookies = []
                for name, value in options['cookies'].items():
                    cookies.append({
                        'name': name,
                        'value': value,
                        'url': url
                    })
                await page.context.add_cookies(cookies)
            
            # Navigate to URL
            response = await page.goto(
                url,
                timeout=timeout,
                wait_until=options.get('wait_until', 'networkidle'),
                referer=options.get('referer')
            )
            
            if not response:
                raise NetworkError(f"Failed to get response for {url}")
            
            # Execute actions
            action_results = []
            for action in actions:
                action_type = action.get('type')
                action_result = {'type': action_type, 'success': False}
                
                try:
                    if action_type == 'click':
                        await page.click(
                            action['selector'],
                            button=action.get('button', 'left'),
                            click_count=action.get('click_count', 1),
                            delay=action.get('delay', 0),
                            timeout=action.get('timeout', timeout)
                        )
                        action_result['success'] = True
                    
                    elif action_type == 'type':
                        await page.type(
                            action['selector'],
                            action['text'],
                            delay=action.get('delay', 0),
                            timeout=action.get('timeout', timeout)
                        )
                        action_result['success'] = True
                    
                    elif action_type == 'fill':
                        await page.fill(
                            action['selector'],
                            action['value'],
                            timeout=action.get('timeout', timeout)
                        )
                        action_result['success'] = True
                    
                    elif action_type == 'select':
                        await page.select_option(
                            action['selector'],
                            value=action.get('value'),
                            label=action.get('label'),
                            index=action.get('index'),
                            timeout=action.get('timeout', timeout)
                        )
                        action_result['success'] = True
                    
                    elif action_type == 'wait_for_selector':
                        await page.wait_for_selector(
                            action['selector'],
                            state=action.get('state', 'visible'),
                            timeout=action.get('timeout', timeout)
                        )
                        action_result['success'] = True
                    
                    elif action_type == 'wait_for_navigation':
                        await page.wait_for_navigation(
                            url=action.get('url'),
                            wait_until=action.get('wait_until', 'networkidle'),
                            timeout=action.get('timeout', timeout)
                        )
                        action_result['success'] = True
                    
                    elif action_type == 'wait_for_load_state':
                        await page.wait_for_load_state(
                            state=action.get('state', 'networkidle'),
                            timeout=action.get('timeout', timeout)
                        )
                        action_result['success'] = True
                    
                    elif action_type == 'screenshot':
                        screenshot = await page.screenshot(
                            type=action.get('type', 'png'),
                            full_page=action.get('full_page', False),
                            path=action.get('path')
                        )
                        action_result['success'] = True
                        action_result['screenshot'] = screenshot
                    
                    elif action_type == 'evaluate':
                        result = await page.evaluate(action['script'])
                        action_result['success'] = True
                        action_result['result'] = result
                    
                    elif action_type == 'scroll':
                        if 'selector' in action:
                            element = await page.query_selector(action['selector'])
                            if element:
                                await element.scroll_into_view_if_needed()
                                action_result['success'] = True
                        else:
                            await page.evaluate(f"window.scrollBy({action.get('x', 0)}, {action.get('y', 100)})")
                            action_result['success'] = True
                    
                    elif action_type == 'hover':
                        await page.hover(
                            action['selector'],
                            position=action.get('position'),
                            timeout=action.get('timeout', timeout)
                        )
                        action_result['success'] = True
                    
                    elif action_type == 'press':
                        await page.press(
                            action['selector'],
                            action['key'],
                            delay=action.get('delay', 0),
                            timeout=action.get('timeout', timeout)
                        )
                        action_result['success'] = True
                    
                    elif action_type == 'wait':
                        await asyncio.sleep(action.get('time', 1))
                        action_result['success'] = True
                    
                    else:
                        action_result['error'] = f"Unknown action type: {action_type}"
                
                except Exception as e:
                    action_result['error'] = str(e)
                    action_result['traceback'] = traceback.format_exc()
                    
                    # Log error
                    logger.error(f"Action error: {e}", exc_info=True)
                    
                    # Break if action is required
                    if action.get('required', False):
                        break
                
                action_results.append(action_result)
            
            # Get content
            content = await page.content()
            
            # Get cookies
            cookies = await page.context.cookies()
            cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            
            # Prepare result
            result = {
                'status_code': response.status,
                'url': page.url,
                'orig_url': url,
                'content': content,
                'headers': dict(response.headers),
                'cookies': cookies_dict,
                'time': time.time() - start_time,
                'save': options.get('save'),
                'actions': action_results
            }
            
            # Take final screenshot if requested
            if options.get('screenshot'):
                result['screenshot'] = await page.screenshot(
                    type=options.get('screenshot_type', 'png'),
                    full_page=options.get('full_page', False),
                    path=options.get('screenshot_path')
                )
            
            # Record success metrics
            metrics.increment('playwright_actions_success')
            
            # Release page
            await self.release_page(page)
            
            return result
        except Exception as e:
            # Record error metrics
            metrics.increment('playwright_actions_error')
            
            # Convert exception
            if 'Timeout' in str(e):
                error = TimeoutError(f"Playwright timeout: {str(e)}")
            elif 'Navigation failed' in str(e):
                error = NetworkError(f"Playwright navigation failed: {str(e)}")
            else:
                error = e
            
            # Release page with error
            if page:
                await self.release_page(page, error=True)
            
            # Prepare error result
            error_result = {
                'status_code': 599,
                'error': str(error),
                'traceback': traceback.format_exc(),
                'content': "",
                'time': time.time() - start_time,
                'orig_url': url,
                'url': url,
                'save': options.get('save'),
                'actions': []
            }
            
            # Log error
            logger.error(f"Playwright actions error: {error}", exc_info=True)
            
            return error_result
