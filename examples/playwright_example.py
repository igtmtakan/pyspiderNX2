#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-05-01 12:00:00

"""
Example of using PlaywrightManager
"""

import os
import sys
import time
import asyncio
import logging
import argparse
from typing import Dict, Any, Optional, List, Tuple, Union, Callable

# Add pyspider to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspider.fetcher.playwright_manager import PlaywrightManager
from pyspider.libs.errors import (
    NetworkError, TimeoutError, HTTPError, ProxyError, 
    DNSError, SSLError, ProcessError, ScriptError, ParseError
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger('playwright_example')

async def simple_fetch_example(manager: PlaywrightManager, url: str):
    """
    Simple fetch example
    
    Args:
        manager: PlaywrightManager instance
        url: URL to fetch
    """
    logger.info(f"Fetching {url}")
    
    # Fetch URL
    result = await manager.fetch(url)
    
    # Log result
    logger.info(f"Status code: {result['status_code']}")
    logger.info(f"URL: {result['url']}")
    logger.info(f"Content length: {len(result['content'])}")
    logger.info(f"Time: {result['time']:.2f}s")
    
    return result

async def actions_example(manager: PlaywrightManager, url: str):
    """
    Actions example
    
    Args:
        manager: PlaywrightManager instance
        url: URL to navigate to
    """
    logger.info(f"Executing actions on {url}")
    
    # Define actions
    actions = [
        # Wait for page to load
        {
            'type': 'wait_for_load_state',
            'state': 'networkidle'
        },
        
        # Take screenshot
        {
            'type': 'screenshot',
            'full_page': True,
            'path': 'screenshot.png'
        },
        
        # Scroll down
        {
            'type': 'scroll',
            'y': 500
        },
        
        # Wait for a moment
        {
            'type': 'wait',
            'time': 1
        },
        
        # Execute JavaScript
        {
            'type': 'evaluate',
            'script': 'return document.title'
        }
    ]
    
    # Execute actions
    result = await manager.execute_actions(url, actions)
    
    # Log result
    logger.info(f"Status code: {result['status_code']}")
    logger.info(f"URL: {result['url']}")
    logger.info(f"Content length: {len(result['content'])}")
    logger.info(f"Time: {result['time']:.2f}s")
    
    # Log action results
    for i, action_result in enumerate(result['actions']):
        logger.info(f"Action {i+1} ({action_result['type']}): {'Success' if action_result['success'] else 'Failed'}")
        if 'result' in action_result:
            logger.info(f"  Result: {action_result['result']}")
        if 'error' in action_result:
            logger.info(f"  Error: {action_result['error']}")
    
    return result

async def form_submission_example(manager: PlaywrightManager, url: str):
    """
    Form submission example
    
    Args:
        manager: PlaywrightManager instance
        url: URL to navigate to
    """
    logger.info(f"Submitting form on {url}")
    
    # Define actions
    actions = [
        # Wait for page to load
        {
            'type': 'wait_for_load_state',
            'state': 'networkidle'
        },
        
        # Fill form fields
        {
            'type': 'fill',
            'selector': 'input[name="q"]',
            'value': 'pyspider playwright example'
        },
        
        # Submit form
        {
            'type': 'press',
            'selector': 'input[name="q"]',
            'key': 'Enter'
        },
        
        # Wait for navigation
        {
            'type': 'wait_for_navigation',
            'wait_until': 'networkidle'
        },
        
        # Take screenshot
        {
            'type': 'screenshot',
            'full_page': True,
            'path': 'search_results.png'
        }
    ]
    
    # Execute actions
    result = await manager.execute_actions(url, actions)
    
    # Log result
    logger.info(f"Status code: {result['status_code']}")
    logger.info(f"URL: {result['url']}")
    logger.info(f"Content length: {len(result['content'])}")
    logger.info(f"Time: {result['time']:.2f}s")
    
    return result

async def error_handling_example(manager: PlaywrightManager, url: str):
    """
    Error handling example
    
    Args:
        manager: PlaywrightManager instance
        url: URL to navigate to
    """
    logger.info(f"Testing error handling on {url}")
    
    # Define actions with errors
    actions = [
        # Wait for page to load
        {
            'type': 'wait_for_load_state',
            'state': 'networkidle'
        },
        
        # Try to click non-existent element
        {
            'type': 'click',
            'selector': '#non-existent-element',
            'timeout': 5000  # 5 seconds timeout
        },
        
        # This action should still execute
        {
            'type': 'evaluate',
            'script': 'return document.title'
        },
        
        # Try to wait for non-existent element with required flag
        {
            'type': 'wait_for_selector',
            'selector': '#another-non-existent-element',
            'timeout': 5000,  # 5 seconds timeout
            'required': True  # This will stop execution if it fails
        },
        
        # This action should not execute
        {
            'type': 'screenshot',
            'full_page': True,
            'path': 'error_screenshot.png'
        }
    ]
    
    # Execute actions
    result = await manager.execute_actions(url, actions)
    
    # Log result
    logger.info(f"Status code: {result['status_code']}")
    logger.info(f"URL: {result['url']}")
    
    # Log action results
    for i, action_result in enumerate(result['actions']):
        logger.info(f"Action {i+1} ({action_result['type']}): {'Success' if action_result['success'] else 'Failed'}")
        if 'error' in action_result:
            logger.info(f"  Error: {action_result['error']}")
    
    return result

async def main():
    """
    Main function
    """
    # Parse arguments
    parser = argparse.ArgumentParser(description='Playwright example')
    parser.add_argument('--url', default='https://example.com', help='URL to fetch')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--browser', default='chromium', choices=['chromium', 'firefox', 'webkit'], help='Browser type')
    parser.add_argument('--example', default='simple', choices=['simple', 'actions', 'form', 'error'], help='Example to run')
    args = parser.parse_args()
    
    # Create PlaywrightManager
    manager = PlaywrightManager(
        browser_type=args.browser,
        headless=args.headless,
        max_pages=5,
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        timeout=60
    )
    
    try:
        # Initialize manager
        await manager.init()
        
        # Run example
        if args.example == 'simple':
            await simple_fetch_example(manager, args.url)
        elif args.example == 'actions':
            await actions_example(manager, args.url)
        elif args.example == 'form':
            await form_submission_example(manager, 'https://www.google.com')
        elif args.example == 'error':
            await error_handling_example(manager, args.url)
    finally:
        # Close manager
        await manager.close()

if __name__ == '__main__':
    asyncio.run(main())
