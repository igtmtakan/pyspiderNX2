#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-05-01 12:00:00

"""
Example of using OptimizedAsyncFetcher
"""

import os
import sys
import time
import asyncio
import logging
import argparse
from typing import Dict, Any, List

# Add pyspider to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspider.fetcher.optimized_async_fetcher import OptimizedAsyncFetcher
from pyspider.libs.metrics import metrics
from pyspider.libs.errors import (
    NetworkError, TimeoutError, HTTPError, ProxyError, 
    DNSError, SSLError, ProcessError, ScriptError, ParseError
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger('optimized_fetcher_example')

class OptimizedFetcherExample:
    """
    Example of using OptimizedAsyncFetcher
    """
    
    def __init__(self, 
                 poolsize: int = 50,
                 timeout: int = 60,
                 user_agent: str = None,
                 proxy: str = None):
        """
        Initialize OptimizedFetcherExample
        
        Args:
            poolsize: Connection pool size
            timeout: Default timeout in seconds
            user_agent: User agent
            proxy: Proxy
        """
        self.fetcher = OptimizedAsyncFetcher(
            poolsize=poolsize,
            timeout=timeout,
            user_agent=user_agent or 'PySpider/1.0 OptimizedFetcherExample',
            proxy=proxy,
            auto_optimize=True
        )
    
    async def fetch_url(self, url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Fetch a URL
        
        Args:
            url: URL to fetch
            options: Fetch options
            
        Returns:
            Fetch result
        """
        task = {
            'taskid': f'example-{int(time.time())}',
            'project': 'example',
            'url': url,
            'fetch': options or {}
        }
        
        return await self.fetcher.async_fetch(task)
    
    async def fetch_multiple(self, urls: List[str], concurrency: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch multiple URLs concurrently
        
        Args:
            urls: URLs to fetch
            concurrency: Maximum number of concurrent requests
            
        Returns:
            List of fetch results
        """
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrency)
        
        async def fetch_with_semaphore(url):
            async with semaphore:
                return await self.fetch_url(url)
        
        # Create tasks
        tasks = [fetch_with_semaphore(url) for url in urls]
        
        # Wait for all tasks to complete
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def benchmark(self, url: str, num_requests: int = 100, concurrency: int = 10) -> Dict[str, Any]:
        """
        Benchmark fetcher performance
        
        Args:
            url: URL to fetch
            num_requests: Number of requests to make
            concurrency: Maximum number of concurrent requests
            
        Returns:
            Benchmark results
        """
        logger.info(f"Starting benchmark with {num_requests} requests to {url} (concurrency: {concurrency})")
        
        # Create URLs
        urls = [f"{url}?id={i}" for i in range(num_requests)]
        
        # Start timer
        start_time = time.time()
        
        # Fetch URLs
        results = await self.fetch_multiple(urls, concurrency)
        
        # Calculate statistics
        end_time = time.time()
        total_time = end_time - start_time
        
        # Count successes and failures
        successes = 0
        failures = 0
        status_codes = {}
        
        for result in results:
            if isinstance(result, Exception):
                failures += 1
            else:
                status_code = result.get('status_code', 0)
                if 200 <= status_code < 300:
                    successes += 1
                else:
                    failures += 1
                
                # Count status codes
                status_codes[status_code] = status_codes.get(status_code, 0) + 1
        
        # Calculate requests per second
        requests_per_second = num_requests / total_time if total_time > 0 else 0
        
        # Get fetcher stats
        fetcher_stats = self.fetcher.get_stats()
        
        # Prepare results
        results = {
            'url': url,
            'num_requests': num_requests,
            'concurrency': concurrency,
            'total_time': total_time,
            'requests_per_second': requests_per_second,
            'successes': successes,
            'failures': failures,
            'success_rate': successes / num_requests if num_requests > 0 else 0,
            'status_codes': status_codes,
            'fetcher_stats': fetcher_stats
        }
        
        # Log results
        logger.info(f"Benchmark completed in {total_time:.2f} seconds")
        logger.info(f"Requests per second: {requests_per_second:.2f}")
        logger.info(f"Success rate: {results['success_rate'] * 100:.2f}%")
        logger.info(f"Status codes: {status_codes}")
        
        return results
    
    async def run(self):
        """
        Run the example
        """
        try:
            # Initialize fetcher
            await self.fetcher.init()
            
            # Fetch a single URL
            url = "https://example.com"
            logger.info(f"Fetching {url}")
            result = await self.fetch_url(url)
            
            logger.info(f"Status code: {result['status_code']}")
            logger.info(f"Content length: {len(result['content'])}")
            logger.info(f"Time: {result['time']:.2f}s")
            
            # Wait a bit
            await asyncio.sleep(1)
            
            # Run benchmark
            await self.benchmark("https://httpbin.org/get", num_requests=50, concurrency=10)
        finally:
            # Close fetcher
            await self.fetcher.close()

async def main():
    """
    Main function
    """
    # Parse arguments
    parser = argparse.ArgumentParser(description='Optimized fetcher example')
    parser.add_argument('--poolsize', type=int, default=50, help='Connection pool size')
    parser.add_argument('--timeout', type=int, default=60, help='Default timeout in seconds')
    parser.add_argument('--user-agent', help='User agent')
    parser.add_argument('--proxy', help='Proxy')
    args = parser.parse_args()
    
    # Create example
    example = OptimizedFetcherExample(
        poolsize=args.poolsize,
        timeout=args.timeout,
        user_agent=args.user_agent,
        proxy=args.proxy
    )
    
    # Run example
    await example.run()

if __name__ == '__main__':
    asyncio.run(main())
