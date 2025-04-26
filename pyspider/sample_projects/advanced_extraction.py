#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-25 18:00:00

"""
Sample project demonstrating advanced data extraction features
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
        self.crawl('https://example.com/', callback=self.index_page)
    
    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        # 1. Advanced Selector Examples
        
        # 1.1 XPath Examples
        title_xpath = response.xpath('//h1/text()')
        self.logger.info(f"Title (XPath): {title_xpath}")
        
        links_xpath = response.xpaths('//a/@href')
        self.logger.info(f"Links (XPath): {links_xpath}")
        
        # 1.2 CSS Examples
        title_css = response.css('h1')
        self.logger.info(f"Title (CSS): {title_css}")
        
        links_css = response.csss('a', 'href')
        self.logger.info(f"Links (CSS): {links_css}")
        
        # 1.3 RegEx Examples
        title_regex = response.regex(r'<h1>(.*?)</h1>')
        self.logger.info(f"Title (RegEx): {title_regex}")
        
        # 1.4 Combined Selectors
        combined_result = response.advanced.select([
            {'type': 'css', 'selector': 'h1', 'attr': 'text'},
            {'type': 'xpath', 'selector': '//h1/text()'},
            {'type': 'regex', 'pattern': '<h1>(.*?)</h1>'}
        ])
        self.logger.info(f"Title (Combined): {combined_result}")
        
        # 1.5 Table Extraction
        table_data = response.extract_table('table')
        self.logger.info(f"Table Data: {table_data}")
        
        # 1.6 List Extraction
        list_data = response.extract_list('ul', 'li')
        self.logger.info(f"List Data: {list_data}")
        
        # 2. Structured Data Examples
        
        # 2.1 JSON-LD Extraction
        json_ld = response.structured_data.extract_json_ld()
        self.logger.info(f"JSON-LD: {json_ld}")
        
        # 2.2 Microdata Extraction
        microdata = response.structured_data.extract_microdata()
        self.logger.info(f"Microdata: {microdata}")
        
        # 2.3 RDFa Extraction
        rdfa = response.structured_data.extract_rdfa()
        self.logger.info(f"RDFa: {rdfa}")
        
        # 2.4 Open Graph Extraction
        opengraph = response.structured_data.extract_opengraph()
        self.logger.info(f"Open Graph: {opengraph}")
        
        # 2.5 Twitter Cards Extraction
        twitter_cards = response.structured_data.extract_twitter_cards()
        self.logger.info(f"Twitter Cards: {twitter_cards}")
        
        # 2.6 All Structured Data
        all_structured_data = response.structured_data.extract_all()
        self.logger.info(f"All Structured Data: {all_structured_data}")
        
        # 3. Multimedia Examples
        
        # 3.1 Image Extraction
        images = response.multimedia.extract_images()
        self.logger.info(f"Images: {images}")
        
        # 3.2 Video Extraction
        videos = response.multimedia.extract_videos()
        self.logger.info(f"Videos: {videos}")
        
        # 3.3 Audio Extraction
        audio = response.multimedia.extract_audio()
        self.logger.info(f"Audio: {audio}")
        
        # 3.4 Download Images
        # Note: This will download images to the specified directory
        # downloaded_images = response.multimedia.download_images()
        # self.logger.info(f"Downloaded Images: {downloaded_images}")
        
        # Return the extracted data
        return {
            'title': title_xpath or title_css or title_regex,
            'links': links_xpath or links_css,
            'structured_data': all_structured_data,
            'images': images,
            'videos': videos,
            'audio': audio
        }
