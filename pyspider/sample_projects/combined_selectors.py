#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-27 15:00:00

"""
Sample project demonstrating combined selector features
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
        
        # GraphQL example
        self.crawl('https://countries.trevorblades.com/', callback=self.graphql_page)
    
    @config(age=10 * 24 * 60 * 60)
    def html_page(self, response):
        # 1. Selector Pipeline Example
        
        # 1.1 Extract with multiple selectors
        title = response.pipeline([
            {'type': 'css', 'selector': 'h1', 'attr': 'text'},
            {'type': 'xpath', 'selector': '//h1/text()'},
            {'type': 'css4', 'selector': 'h1:first-of-type', 'attr': 'text'},
            {'type': 'regex', 'pattern': '<h1>(.*?)</h1>'}
        ])
        self.logger.info(f"Title (Pipeline): {title}")
        
        # 1.2 Extract with transformers
        title_transformed = response.pipeline([
            {'type': 'css', 'selector': 'h1', 'attr': 'text'}
        ], [
            {'name': 'strip'},
            {'name': 'upper'}
        ])
        self.logger.info(f"Title (Transformed): {title_transformed}")
        
        # 1.3 Extract with fallbacks
        description = response.extract_with_fallbacks([
            {'type': 'css', 'selector': 'meta[name="description"]', 'attr': 'content'},
            {'type': 'css', 'selector': 'p', 'attr': 'text'},
            {'type': 'xpath', 'selector': '//p[1]/text()'}
        ])
        self.logger.info(f"Description (Fallbacks): {description}")
        
        # 1.4 Extract multiple fields
        data = response.extract_multiple({
            'fields': {
                'title': {
                    'selectors': [
                        {'type': 'css', 'selector': 'h1', 'attr': 'text'}
                    ],
                    'transformers': [
                        {'name': 'strip'}
                    ],
                    'combiner': 'first'
                },
                'links': {
                    'selectors': [
                        {'type': 'css', 'selector': 'a', 'attr': 'href'}
                    ],
                    'transformers': [
                        {'name': 'unique'}
                    ],
                    'combiner': 'all'
                },
                'paragraphs': {
                    'selectors': [
                        {'type': 'css', 'selector': 'p', 'attr': 'text'}
                    ],
                    'transformers': [
                        {'name': 'strip'},
                        {'name': 'filter_empty'}
                    ],
                    'combiner': 'all'
                }
            }
        })
        self.logger.info(f"Multiple Fields: {data}")
        
        # 1.5 Extract table
        table_data = response.extract_table_advanced({
            'table_selector': {'type': 'css', 'selector': 'table'},
            'row_selector': {'type': 'css', 'selector': 'tr'},
            'header_selector': {'type': 'css', 'selector': 'th'},
            'cell_selector': {'type': 'css', 'selector': 'td'},
            'header_transformers': [
                {'name': 'strip'},
                {'name': 'lower'}
            ],
            'cell_transformers': [
                {'name': 'strip'}
            ],
            'skip_rows': 0,
            'skip_empty': True
        })
        self.logger.info(f"Table Data: {table_data}")
        
        # 1.6 Extract list
        list_data = response.extract_list_advanced({
            'list_selector': {'type': 'css', 'selector': 'ul'},
            'item_selector': {'type': 'css', 'selector': 'li'},
            'fields': {
                'text': {
                    'selectors': [
                        {'type': 'css', 'selector': '', 'attr': 'text'}
                    ],
                    'transformers': [
                        {'name': 'strip'}
                    ]
                },
                'link': {
                    'selectors': [
                        {'type': 'css', 'selector': 'a', 'attr': 'href'}
                    ]
                }
            },
            'skip_empty': True
        })
        self.logger.info(f"List Data: {list_data}")
        
        # 2. CSS4 Selector Example
        
        # 2.1 CSS4 with pseudo-classes
        first_p = response.css4('p:first-of-type')
        self.logger.info(f"First paragraph (CSS4): {first_p}")
        
        # 2.2 CSS4 with attribute selectors
        links_with_rel = response.css4s('a[rel]', 'href')
        self.logger.info(f"Links with rel attribute (CSS4): {links_with_rel}")
        
        # 3. XQuery Example
        
        # 3.1 Basic XQuery
        xquery_result = response.xquery('//h1/text()')
        self.logger.info(f"XQuery Result: {xquery_result}")
        
        # 3.2 XQuery with namespaces
        xquery_with_ns = response.xquery_selector.extract_value('//h1')
        self.logger.info(f"XQuery with extract_value: {xquery_with_ns}")
        
        return {
            'title': title,
            'description': description,
            'data': data,
            'table_data': table_data,
            'list_data': list_data
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
        
        # 3. Pipeline Examples
        
        # 3.1 Extract with pipeline
        data = response.pipeline([
            {'type': 'jsonpath', 'path': '$[0:5]'}
        ], [
            {'name': 'map', 'args': [{'name': 'get', 'args': ['title']}]}
        ])
        self.logger.info(f"Pipeline Result: {data}")
        
        # 3.2 Extract multiple fields
        data_multiple = response.extract_multiple({
            'fields': {
                'titles': {
                    'selectors': [
                        {'type': 'jmespath', 'path': '[*].title'}
                    ],
                    'transformers': [
                        {'name': 'slice', 'args': [0, 5]}
                    ],
                    'combiner': 'first'
                },
                'user_ids': {
                    'selectors': [
                        {'type': 'jmespath', 'path': '[*].userId'}
                    ],
                    'transformers': [
                        {'name': 'unique'}
                    ],
                    'combiner': 'first'
                }
            }
        })
        self.logger.info(f"Multiple Fields: {data_multiple}")
        
        # 4. Advanced JSON Processing
        
        # 4.1 Extract keys
        keys = response.json_selector.extract_keys('$[0]')
        self.logger.info(f"Keys in first post: {keys}")
        
        # 4.2 Extract values for a specific key
        all_ids = response.json_selector.extract_values('id')
        self.logger.info(f"All post IDs: {all_ids}")
        
        # 4.3 Flatten nested JSON
        flattened = response.json_selector.flatten('$[0:2]')
        self.logger.info(f"Flattened posts: {flattened}")
        
        return {
            'first_title': first_title,
            'filtered_posts': filtered_posts,
            'first_title_jmes': first_title_jmes,
            'filtered_posts_jmes': filtered_posts_jmes,
            'data': data,
            'data_multiple': data_multiple
        }
    
    @config(age=10 * 24 * 60 * 60)
    def graphql_page(self, response):
        # 1. GraphQL Examples
        
        # 1.1 Basic GraphQL query
        query = """
        query {
          countries {
            name
            code
            capital
          }
        }
        """
        countries = response.graphql(query, path='countries')
        self.logger.info(f"Countries (first 3): {countries[:3]}")
        
        # 1.2 GraphQL query with variables
        query_with_vars = """
        query GetCountry($code: ID!) {
          country(code: $code) {
            name
            capital
            currency
            languages {
              name
            }
          }
        }
        """
        variables = {'code': 'US'}
        country = response.graphql(query_with_vars, variables, path='country')
        self.logger.info(f"Country: {country}")
        
        # 2. GraphQL Schema Introspection
        
        # 2.1 Get schema information
        schema = response.graphql_selector.introspect()
        query_fields = response.graphql_selector.get_query_fields()
        self.logger.info(f"Query Fields: {query_fields}")
        
        # 2.2 Suggest a query
        suggested_query = response.graphql_selector.suggest_query('country')
        self.logger.info(f"Suggested Query: {suggested_query}")
        
        return {
            'countries': countries[:3] if countries else [],
            'country': country,
            'query_fields': query_fields
        }
