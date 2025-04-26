#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-28 12:00:00

"""
Sample project demonstrating browser automation features
"""

from pyspider.libs.base_handler import *

class Handler(BaseHandler):
    crawl_config = {
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        },
        'fetch_type': 'playwright',
    }
    
    @every(minutes=24 * 60)
    def on_start(self):
        # Basic page fetch
        self.crawl('https://example.com/', callback=self.index_page)
        
        # Page with actions
        self.crawl('https://httpbin.org/forms/post', 
                  callback=self.form_page,
                  actions=[
                      {'type': 'fill', 'selector': 'input[name="custname"]', 'value': 'John Doe'},
                      {'type': 'fill', 'selector': 'input[name="custtel"]', 'value': '555-1234'},
                      {'type': 'fill', 'selector': 'input[name="custemail"]', 'value': 'john@example.com'},
                      {'type': 'select', 'selector': 'select[name="size"]', 'value': 'medium'},
                      {'type': 'check', 'selector': 'input[name="topping"][value="bacon"]'},
                      {'type': 'check', 'selector': 'input[name="topping"][value="cheese"]'},
                      {'type': 'fill', 'selector': 'textarea[name="delivery"]', 'value': '123 Main St'},
                      {'type': 'click', 'selector': 'button[type="submit"]'},
                      {'type': 'wait_for_navigation', 'options': {'timeout': 5000}}
                  ])
        
        # Page with conditional actions
        self.crawl('https://www.google.com/', 
                  callback=self.search_page,
                  actions=[
                      {'type': 'fill', 'selector': 'input[name="q"]', 'value': 'pyspider web crawler'},
                      {'type': 'press', 'selector': 'input[name="q"]', 'key': 'Enter'},
                      {'type': 'wait_for_selector', 'selector': '#search'},
                      {'type': 'wait_for_timeout', 'timeout': 2000},
                      {'type': 'screenshot', 'path': 'search_results.png'}
                  ])
        
        # Page with scroll actions
        self.crawl('https://news.ycombinator.com/', 
                  callback=self.scroll_page,
                  actions=[
                      {'type': 'wait_for_selector', 'selector': '.athing'},
                      {'type': 'scroll', 'y': 500},
                      {'type': 'wait_for_timeout', 'timeout': 1000},
                      {'type': 'scroll', 'y': 1000},
                      {'type': 'wait_for_timeout', 'timeout': 1000},
                      {'type': 'scroll', 'y': 1500},
                      {'type': 'wait_for_timeout', 'timeout': 1000}
                  ])
        
        # Page with JavaScript evaluation
        self.crawl('https://example.com/', 
                  callback=self.evaluate_page,
                  actions=[
                      {'type': 'evaluate', 'expression': 'document.title = "Modified Title"'},
                      {'type': 'evaluate', 'expression': 'document.body.style.backgroundColor = "lightyellow"'},
                      {'type': 'wait_for_timeout', 'timeout': 1000},
                      {'type': 'screenshot', 'path': 'modified_page.png'}
                  ])
    
    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        """Process a basic page"""
        return {
            'title': response.doc('title').text(),
            'url': response.url,
            'content_snippet': response.doc('p').text()
        }
    
    @config(age=10 * 24 * 60 * 60)
    def form_page(self, response):
        """Process a page after form submission"""
        # After form submission, we should be on a different page
        return {
            'url': response.url,
            'form_submitted': 'httpbin' in response.url,
            'response_data': response.json if hasattr(response, 'json') else None,
            'actions_result': response.get('actions_result')
        }
    
    @config(age=10 * 24 * 60 * 60)
    def search_page(self, response):
        """Process search results"""
        # Extract search results
        results = []
        for item in response.doc('#search .g'):
            results.append({
                'title': response.doc(item).css('h3').text(),
                'url': response.doc(item).css('a').attr('href'),
                'snippet': response.doc(item).css('.VwiC3b').text()
            })
        
        return {
            'query': 'pyspider web crawler',
            'results_count': len(results),
            'results': results[:5],  # First 5 results
            'actions_result': response.get('actions_result')
        }
    
    @config(age=10 * 24 * 60 * 60)
    def scroll_page(self, response):
        """Process a page after scrolling"""
        # Extract all items after scrolling
        items = []
        for item in response.doc('.athing'):
            items.append({
                'id': response.doc(item).attr('id'),
                'title': response.doc(item).css('.titleline > a').text(),
                'url': response.doc(item).css('.titleline > a').attr('href')
            })
        
        return {
            'items_count': len(items),
            'items': items,
            'actions_result': response.get('actions_result')
        }
    
    @config(age=10 * 24 * 60 * 60)
    def evaluate_page(self, response):
        """Process a page after JavaScript evaluation"""
        return {
            'title': response.doc('title').text(),  # Should be "Modified Title"
            'url': response.url,
            'actions_result': response.get('actions_result')
        }
