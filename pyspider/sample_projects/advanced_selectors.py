#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-26 12:00:00

"""
Sample project demonstrating advanced selector features
"""

from pyspider.libs.base_handler import *

class Handler(BaseHandler):
    crawl_config = {
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    }
    
    @every(minutes=24 * 60)
    def on_start(self):
        # HTML example
        self.crawl('https://example.com/', callback=self.html_page)
        
        # JSON example
        self.crawl('https://jsonplaceholder.typicode.com/posts', callback=self.json_page)
    
    @config(age=10 * 24 * 60 * 60)
    def html_page(self, response):
        # 1. Basic Selectors
        
        # 1.1 XPath Examples
        title_xpath = response.xpath('//h1/text()')
        self.logger.info(f"Title (XPath): {title_xpath}")
        
        # 1.2 CSS Examples
        title_css = response.css('h1')
        self.logger.info(f"Title (CSS): {title_css}")
        
        # 1.3 RegEx Examples
        title_regex = response.regex(r'<h1>(.*?)</h1>')
        self.logger.info(f"Title (RegEx): {title_regex}")
        
        # 2. Advanced CSS4 Selectors
        
        # 2.1 CSS4 with pseudo-classes
        first_p = response.css4('p:first-of-type')
        self.logger.info(f"First paragraph (CSS4): {first_p}")
        
        # 2.2 CSS4 with attribute selectors
        links_with_rel = response.css4s('a[rel]', 'href')
        self.logger.info(f"Links with rel attribute (CSS4): {links_with_rel}")
        
        # 2.3 CSS4 with complex selectors
        complex_selector = response.css4('div > p:not(:first-child)')
        self.logger.info(f"Complex selector (CSS4): {complex_selector}")
        
        # 3. Combined Selectors
        
        combined_result = response.advanced.select([
            {'type': 'css4', 'selector': 'h1:first-child', 'attr': 'text'},
            {'type': 'css', 'selector': 'h1', 'attr': 'text'},
            {'type': 'xpath', 'selector': '//h1/text()'},
            {'type': 'regex', 'pattern': '<h1>(.*?)</h1>'}
        ])
        self.logger.info(f"Title (Combined): {combined_result}")
        
        return {
            'title': title_xpath or title_css or title_regex,
            'first_paragraph': first_p,
            'links_with_rel': links_with_rel,
            'complex_selector': complex_selector
        }
    
    @config(age=10 * 24 * 60 * 60)
    def json_page(self, response):
        # 1. JSONPath Examples
        
        # 1.1 Basic JSONPath
        first_title = response.jsonpath('$[0].title')
        self.logger.info(f"First title (JSONPath): {first_title}")
        
        # 1.2 JSONPath with filter
        filtered_posts = response.jsonpaths('$[?(@.userId==1)].title')
        self.logger.info(f"Posts by user 1 (JSONPath): {filtered_posts}")
        
        # 2. JMESPath Examples
        
        # 2.1 Basic JMESPath
        first_title_jmes = response.jmespath('[0].title')
        self.logger.info(f"First title (JMESPath): {first_title_jmes}")
        
        # 2.2 JMESPath with filter
        filtered_posts_jmes = response.jmespath("[?userId==`1`].title")
        self.logger.info(f"Posts by user 1 (JMESPath): {filtered_posts_jmes}")
        
        # 2.3 JMESPath with projection
        titles_jmes = response.jmespath('[*].title')
        self.logger.info(f"All titles (JMESPath): {titles_jmes}")
        
        # 3. Combined Selectors
        
        combined_result = response.advanced.select([
            {'type': 'jsonpath', 'path': '$[0].title'},
            {'type': 'jmespath', 'path': '[0].title'}
        ])
        self.logger.info(f"First title (Combined): {combined_result}")
        
        # 4. Advanced JSON Processing
        
        # 4.1 Extract keys
        keys = response.advanced.json_selector.extract_keys('$[0]')
        self.logger.info(f"Keys in first post: {keys}")
        
        # 4.2 Extract values for a specific key
        all_ids = response.advanced.json_selector.extract_values('id')
        self.logger.info(f"All post IDs: {all_ids}")
        
        # 4.3 Flatten nested JSON
        flattened = response.advanced.json_selector.flatten('$[0:2]')
        self.logger.info(f"Flattened posts: {flattened}")
        
        return {
            'first_title': first_title,
            'filtered_posts': filtered_posts,
            'first_title_jmes': first_title_jmes,
            'filtered_posts_jmes': filtered_posts_jmes,
            'titles_jmes': titles_jmes,
            'keys': keys,
            'all_ids': all_ids
        }
