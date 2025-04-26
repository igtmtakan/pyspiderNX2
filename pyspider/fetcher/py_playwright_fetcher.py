import asyncio
import json
import time
import os
from typing import Dict, Any, Optional, List, Union
from playwright.async_api import async_playwright, Browser, Page, Response
import logging

from pyspider.fetcher.playwright_actions import PlaywrightActions

logger = logging.getLogger('fetcher')

class PyPlaywrightFetcher:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.actions = None

    async def init(self):
        """Initialize playwright and browser"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            browser_options = {
                'args': [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--ignore-certificate-errors',
                    '--ignore-ssl-errors'
                ]
            }
            self.browser = await self.playwright.chromium.launch(**browser_options)
            logger.info("Browser initialized successfully")

    async def close(self):
        """Close browser and playwright"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def fetch(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch a URL using playwright"""
        start_time = time.time()

        try:
            await self.init()
            context = await self.browser.new_context(
                ignore_https_errors=True
            )
            page = await context.new_page()

            # Configure viewport
            await page.set_viewport_size({
                'width': task.get('js_viewport_width', 1024),
                'height': task.get('js_viewport_height', 768 * 3)
            })

            # Set headers
            if task.get('headers'):
                await page.set_extra_http_headers(task['headers'])

            # Handle image loading
            if task.get('load_images') == "false":
                await page.route("**/*", lambda route: route.abort()
                    if route.request.resource_type == "image"
                    else route.continue_())

            # Initialize actions
            self.actions = PlaywrightActions(page)

            # Navigate to page
            response: Response = await page.goto(
                task['url'],
                timeout=task.get('timeout', 20) * 1000,
                wait_until='networkidle'
            )

            # Perform actions if specified
            actions_result = None
            if task.get('actions'):
                logger.info('Performing actions')
                actions_result = await self.actions.perform_actions(task['actions'])

            # Record actions if requested
            if task.get('record_actions'):
                logger.info('Recording actions')
                await self.actions.start_recording()

                # Wait for recording timeout
                record_timeout = task.get('record_timeout', 60) * 1000
                await page.wait_for_timeout(record_timeout)

                # Stop recording and get actions
                actions_result = await self.actions.stop_recording()

                # Save recorded actions if path is provided
                if task.get('record_actions_path'):
                    self.actions.save_recorded_actions(task['record_actions_path'])

            # Execute custom JavaScript
            script_result = None
            if task.get('js_script'):
                logger.info('Executing custom JavaScript')
                script_result = await page.evaluate(task['js_script'])

            # Take screenshot if requested
            if task.get('screenshot_path'):
                await page.screenshot(path=task['screenshot_path'])

            # Get cookies
            cookies = {}
            raw_cookies = await context.cookies()
            for cookie in raw_cookies:
                cookies[cookie['name']] = cookie['value']

            # Prepare result
            result = {
                'orig_url': task['url'],
                'status_code': response.status if response else 599,
                'error': None,
                'content': await page.content(),
                'headers': dict(response.headers) if response else {},
                'url': page.url,
                'cookies': cookies,
                'time': time.time() - start_time,
                'js_script_result': script_result,
                'actions_result': actions_result,
                'save': task.get('save')
            }

            await context.close()
            return result

        except Exception as e:
            from pyspider.libs.error_types import NetworkError, TimeoutError

            logger.error(f"Error during fetch: {str(e)}")

            # Determine the specific error type
            if 'timeout' in str(e).lower():
                error_type = TimeoutError(str(e))
            elif any(net_err in str(e).lower() for net_err in ['network', 'connection', 'connect', 'socket', 'dns']):
                error_type = NetworkError(str(e))
            else:
                error_type = Exception(str(e))

            return {
                'orig_url': task['url'],
                'status_code': 599,
                'error': str(e),
                'error_type': error_type.__class__.__name__,
                'content': None,
                'headers': {},
                'url': task['url'],
                'cookies': {},
                'time': time.time() - start_time,
                'js_script_result': None,
                'save': task.get('save')
            }

async def create_fetcher():
    """Create and initialize a new PyPlaywrightFetcher instance"""
    fetcher = PyPlaywrightFetcher()
    await fetcher.init()
    return fetcher

if __name__ == "__main__":
    import asyncio

    async def main():
        fetcher = await create_fetcher()
        try:
            # Test fetch
            result = await fetcher.fetch({
                'url': 'https://example.com',
                'timeout': 20
            })
            print(f"Fetch result: {result['status_code']}")
        finally:
            await fetcher.close()

    asyncio.run(main())