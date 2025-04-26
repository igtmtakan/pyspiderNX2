#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-28 17:00:00

"""
Sample project demonstrating advanced selector pipeline features
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
        # E-commerce product page
        self.crawl('https://www.amazon.com/dp/B08N5KWB9H/', callback=self.product_page)
        
        # News article page
        self.crawl('https://www.bbc.com/news/world-us-canada-56163220', callback=self.news_page)
        
        # Job listing page
        self.crawl('https://www.indeed.com/jobs?q=python+developer&l=Remote', callback=self.job_listing_page)
    
    def on_init(self):
        """Load custom transformers"""
        # Load custom transformers from module
        self.response.load_transformer_module('pyspider/sample_projects/custom_transformers.py')
        
        # Register additional transformers
        self.response.register_transformer('word_count', lambda x: len(x.split()) if isinstance(x, str) else 0)
        self.response.register_transformer('character_count', lambda x: len(x) if isinstance(x, str) else 0)
    
    @config(age=10 * 24 * 60 * 60)
    def product_page(self, response):
        """Process e-commerce product page with advanced selectors"""
        # 1. Basic extraction with pipeline
        product_info = response.pipeline([
            {'type': 'css', 'selector': '#productTitle', 'attr': 'text'}
        ], [
            {'name': 'strip'},
            {'name': 'truncate', 'args': [100]}
        ])
        self.logger.info(f"Product title: {product_info}")
        
        # 2. Extract with fallbacks
        price = response.extract_with_fallbacks([
            {'type': 'css', 'selector': '#priceblock_ourprice', 'attr': 'text'},
            {'type': 'css', 'selector': '#priceblock_dealprice', 'attr': 'text'},
            {'type': 'css', 'selector': '.a-price .a-offscreen', 'attr': 'text'}
        ], [
            {'name': 'strip'},
            {'name': 'extract_price'}
        ])
        self.logger.info(f"Product price: {price}")
        
        # 3. Extract multiple fields
        product_data = response.extract_multiple({
            'fields': {
                'title': {
                    'selectors': [
                        {'type': 'css', 'selector': '#productTitle', 'attr': 'text'}
                    ],
                    'transformers': [
                        {'name': 'strip'},
                        {'name': 'truncate', 'args': [100]}
                    ],
                    'combiner': 'first'
                },
                'price': {
                    'selectors': [
                        {'type': 'css', 'selector': '#priceblock_ourprice', 'attr': 'text'},
                        {'type': 'css', 'selector': '#priceblock_dealprice', 'attr': 'text'},
                        {'type': 'css', 'selector': '.a-price .a-offscreen', 'attr': 'text'}
                    ],
                    'transformers': [
                        {'name': 'strip'},
                        {'name': 'extract_price'}
                    ],
                    'combiner': 'first'
                },
                'rating': {
                    'selectors': [
                        {'type': 'css', 'selector': '#acrPopover .a-icon-alt', 'attr': 'text'}
                    ],
                    'transformers': [
                        {'name': 'extract_first_number'}
                    ],
                    'combiner': 'first'
                },
                'availability': {
                    'selectors': [
                        {'type': 'css', 'selector': '#availability', 'attr': 'text'}
                    ],
                    'transformers': [
                        {'name': 'strip'}
                    ],
                    'combiner': 'first'
                },
                'images': {
                    'selectors': [
                        {'type': 'css', 'selector': '#imgTagWrapperId img', 'attr': 'src'},
                        {'type': 'css', 'selector': '#imgTagWrapperId img', 'attr': 'data-old-hires'}
                    ],
                    'transformers': [
                        {'name': 'filter_empty'}
                    ],
                    'combiner': 'all'
                }
            }
        })
        self.logger.info(f"Product data: {product_data}")
        
        # 4. Extract table data
        specifications = response.extract_table_advanced({
            'table_selector': {'type': 'css', 'selector': '.prodDetTable'},
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
            'skip_empty': True
        })
        self.logger.info(f"Product specifications: {specifications}")
        
        # 5. Advanced pipeline with conditions
        pipeline_config = {
            'steps': [
                {
                    'type': 'selector',
                    'selectors': [
                        {'type': 'css', 'selector': '#availability', 'attr': 'text'}
                    ]
                },
                {
                    'type': 'transform',
                    'transformers': [
                        {'name': 'strip'},
                        {'name': 'lower'}
                    ]
                },
                {
                    'type': 'condition',
                    'condition': {
                        'type': 'contains',
                        'value': 'in stock'
                    },
                    'then': [
                        {'name': 'replace', 'args': ['in stock', 'Available']}
                    ],
                    'else': [
                        {'name': 'default', 'args': ['Out of stock']}
                    ]
                }
            ]
        }
        availability_status = response.execute_pipeline(pipeline_config)
        self.logger.info(f"Availability status: {availability_status}")
        
        return {
            'product_info': product_info,
            'price': price,
            'product_data': product_data,
            'specifications': specifications,
            'availability_status': availability_status
        }
    
    @config(age=10 * 24 * 60 * 60)
    def news_page(self, response):
        """Process news article page with advanced selectors"""
        # 1. Extract article data
        article_data = response.extract_multiple({
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
                'published_date': {
                    'selectors': [
                        {'type': 'css', 'selector': 'time', 'attr': 'datetime'},
                        {'type': 'css', 'selector': '.date', 'attr': 'text'}
                    ],
                    'transformers': [
                        {'name': 'strip'},
                        {'name': 'format_iso_date'}
                    ],
                    'combiner': 'first'
                },
                'author': {
                    'selectors': [
                        {'type': 'css', 'selector': '.byline__name', 'attr': 'text'},
                        {'type': 'css', 'selector': '.author', 'attr': 'text'}
                    ],
                    'transformers': [
                        {'name': 'strip'}
                    ],
                    'combiner': 'first'
                },
                'content': {
                    'selectors': [
                        {'type': 'css', 'selector': '.article__body-content', 'attr': 'html'},
                        {'type': 'css', 'selector': '.story-body', 'attr': 'html'}
                    ],
                    'transformers': [
                        {'name': 'html_to_text'},
                        {'name': 'normalize_whitespace'}
                    ],
                    'combiner': 'first'
                },
                'tags': {
                    'selectors': [
                        {'type': 'css', 'selector': '.tags-container a', 'attr': 'text'}
                    ],
                    'transformers': [
                        {'name': 'strip'},
                        {'name': 'filter_empty'}
                    ],
                    'combiner': 'all'
                }
            }
        })
        self.logger.info(f"Article data: {article_data}")
        
        # 2. Extract related articles
        related_articles = response.extract_list_advanced({
            'list_selector': {'type': 'css', 'selector': '.related-stories'},
            'item_selector': {'type': 'css', 'selector': '.related-story'},
            'fields': {
                'title': {
                    'selectors': [
                        {'type': 'css', 'selector': 'a', 'attr': 'text'}
                    ],
                    'transformers': [
                        {'name': 'strip'}
                    ]
                },
                'url': {
                    'selectors': [
                        {'type': 'css', 'selector': 'a', 'attr': 'href'}
                    ]
                }
            },
            'skip_empty': True
        })
        self.logger.info(f"Related articles: {related_articles}")
        
        # 3. Advanced pipeline with parallel processing
        pipeline_config = {
            'steps': [
                {
                    'type': 'selector',
                    'selectors': [
                        {'type': 'css', 'selector': '.article__body-content', 'attr': 'html'},
                        {'type': 'css', 'selector': '.story-body', 'attr': 'html'}
                    ]
                },
                {
                    'type': 'transform',
                    'transformers': [
                        {'name': 'html_to_text'},
                        {'name': 'normalize_whitespace'}
                    ]
                },
                {
                    'type': 'parallel',
                    'branches': [
                        [
                            {
                                'type': 'transform',
                                'transformers': [
                                    {'name': 'word_count'}
                                ]
                            }
                        ],
                        [
                            {
                                'type': 'transform',
                                'transformers': [
                                    {'name': 'character_count'}
                                ]
                            }
                        ],
                        [
                            {
                                'type': 'transform',
                                'transformers': [
                                    {'name': 'truncate', 'args': [200]}
                                ]
                            }
                        ]
                    ],
                    'combiner': 'dict',
                    'keys': ['word_count', 'character_count', 'preview']
                }
            ]
        }
        content_analysis = response.execute_pipeline(pipeline_config)
        self.logger.info(f"Content analysis: {content_analysis}")
        
        return {
            'article_data': article_data,
            'related_articles': related_articles,
            'content_analysis': content_analysis
        }
    
    @config(age=10 * 24 * 60 * 60)
    def job_listing_page(self, response):
        """Process job listing page with advanced selectors"""
        # 1. Extract job listings
        job_listings = response.extract_list_advanced({
            'list_selector': {'type': 'css', 'selector': '.jobsearch-ResultsList'},
            'item_selector': {'type': 'css', 'selector': '.job_seen_beacon'},
            'fields': {
                'title': {
                    'selectors': [
                        {'type': 'css', 'selector': '.jobTitle a', 'attr': 'text'},
                        {'type': 'css', 'selector': '.jobtitle', 'attr': 'text'}
                    ],
                    'transformers': [
                        {'name': 'strip'}
                    ]
                },
                'company': {
                    'selectors': [
                        {'type': 'css', 'selector': '.companyName', 'attr': 'text'},
                        {'type': 'css', 'selector': '.company', 'attr': 'text'}
                    ],
                    'transformers': [
                        {'name': 'strip'}
                    ]
                },
                'location': {
                    'selectors': [
                        {'type': 'css', 'selector': '.companyLocation', 'attr': 'text'},
                        {'type': 'css', 'selector': '.location', 'attr': 'text'}
                    ],
                    'transformers': [
                        {'name': 'strip'}
                    ]
                },
                'salary': {
                    'selectors': [
                        {'type': 'css', 'selector': '.salary-snippet', 'attr': 'text'},
                        {'type': 'css', 'selector': '.salaryText', 'attr': 'text'}
                    ],
                    'transformers': [
                        {'name': 'strip'}
                    ]
                },
                'description': {
                    'selectors': [
                        {'type': 'css', 'selector': '.job-snippet', 'attr': 'text'},
                        {'type': 'css', 'selector': '.summary', 'attr': 'text'}
                    ],
                    'transformers': [
                        {'name': 'strip'},
                        {'name': 'normalize_whitespace'}
                    ]
                },
                'date_posted': {
                    'selectors': [
                        {'type': 'css', 'selector': '.date', 'attr': 'text'}
                    ],
                    'transformers': [
                        {'name': 'strip'},
                        {'name': 'parse_relative_date'}
                    ]
                }
            },
            'skip_empty': True
        })
        self.logger.info(f"Job listings: {job_listings}")
        
        # 2. Extract job count
        job_count = response.pipeline([
            {'type': 'css', 'selector': '.jobsearch-JobCountAndSortPane-jobCount', 'attr': 'text'}
        ], [
            {'name': 'extract_first_number'}
        ])
        self.logger.info(f"Job count: {job_count}")
        
        # 3. Process job listings with pipeline
        pipeline_config = {
            'steps': [
                {
                    'type': 'transform',
                    'transformers': [
                        {'name': 'filter_empty'}
                    ]
                },
                {
                    'type': 'loop',
                    'steps': [
                        {
                            'type': 'transform',
                            'transformers': [
                                {
                                    'name': 'rename_keys',
                                    'args': [{'title': 'job_title', 'company': 'employer', 'description': 'summary'}]
                                }
                            ]
                        },
                        {
                            'type': 'condition',
                            'condition': {
                                'type': 'custom',
                                'function': 'word_count'
                            },
                            'then': [
                                {'name': 'pick', 'args': [['job_title', 'employer', 'location', 'salary']]}
                            ]
                        }
                    ]
                }
            ]
        }
        processed_jobs = response.execute_pipeline(pipeline_config, job_listings)
        self.logger.info(f"Processed jobs: {processed_jobs}")
        
        return {
            'job_listings': job_listings,
            'job_count': job_count,
            'processed_jobs': processed_jobs
        }
