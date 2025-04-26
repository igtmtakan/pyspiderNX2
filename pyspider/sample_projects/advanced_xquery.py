#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-28 15:00:00

"""
Sample project demonstrating advanced XQuery features
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
        # XML example
        self.crawl('https://www.w3schools.com/xml/books.xml', callback=self.xml_page)
        
        # RSS feed example
        self.crawl('https://news.yahoo.com/rss/', callback=self.rss_page)
        
        # SOAP API example (simulated)
        self.crawl('https://www.w3schools.com/xml/note.xml', callback=self.soap_page)
    
    @config(age=10 * 24 * 60 * 60)
    def xml_page(self, response):
        """Process XML data with XQuery"""
        # 1. Basic XPath
        books = response.xpath('//book')
        self.logger.info(f"Books count (XPath): {len(books)}")
        
        # 2. Basic XQuery
        titles = response.xquery('//book/title/text()')
        self.logger.info(f"Book titles (XQuery): {titles}")
        
        # 3. XQuery with element construction
        book_list = response.xquery('''
            for $book in //book
            return <book>
                <title>{$book/title/text()}</title>
                <author>{$book/author/text()}</author>
                <price>{$book/price/text()}</price>
            </book>
        ''')
        self.logger.info(f"Book list (XQuery): {book_list}")
        
        # 4. XQuery 3.1 with FLWOR expression
        # Note: This requires Saxon-HE to be available
        try:
            expensive_books = response.execute_flwor('''
                for $book in //book
                let $price := number($book/price)
                where $price > 30
                order by $price descending
                return map {
                    "title": $book/title/string(),
                    "author": $book/author/string(),
                    "price": $price
                }
            ''')
            self.logger.info(f"Expensive books (FLWOR): {expensive_books}")
        except Exception as e:
            self.logger.error(f"Error executing FLWOR expression: {e}")
            expensive_books = "Error: Saxon-HE not available"
        
        # 5. XQuery with grouping
        try:
            books_by_author = response.xquery31('''
                let $books := //book
                for $author in distinct-values($books/author)
                return map {
                    "author": $author,
                    "books": array {
                        for $book in $books[author = $author]
                        return map {
                            "title": $book/title/string(),
                            "price": number($book/price)
                        }
                    },
                    "total_books": count($books[author = $author]),
                    "avg_price": avg($books[author = $author]/price/number())
                }
            ''')
            self.logger.info(f"Books by author (XQuery 3.1): {books_by_author}")
        except Exception as e:
            self.logger.error(f"Error executing XQuery 3.1: {e}")
            books_by_author = "Error: Saxon-HE not available"
        
        # 6. Extract specific values
        book_prices = response.xquery_selector.extract_values('//book/price')
        self.logger.info(f"Book prices: {book_prices}")
        
        # 7. Extract attributes
        book_categories = response.xquery_selector.extract_attributes('//book', 'category')
        self.logger.info(f"Book categories: {book_categories}")
        
        return {
            'books_count': len(books),
            'titles': titles,
            'book_list': book_list,
            'expensive_books': expensive_books,
            'books_by_author': books_by_author,
            'book_prices': book_prices,
            'book_categories': book_categories
        }
    
    @config(age=10 * 24 * 60 * 60)
    def rss_page(self, response):
        """Process RSS feed with XQuery"""
        # 1. Register namespaces
        response.xquery_selector.register_namespace('rss', 'http://purl.org/rss/1.0/')
        response.xquery_selector.register_namespace('content', 'http://purl.org/rss/1.0/modules/content/')
        response.xquery_selector.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')
        
        # 2. Basic XQuery with namespaces
        items = response.xquery('//item')
        self.logger.info(f"RSS items count: {len(items) if items else 0}")
        
        # 3. Extract titles
        titles = response.xquery('//item/title/text()')
        self.logger.info(f"RSS titles: {titles[:3] if titles else []}")
        
        # 4. XQuery with FLWOR expression
        try:
            recent_items = response.execute_flwor('''
                for $item in //item
                let $date := $item/pubDate/string()
                order by $date descending
                return map {
                    "title": $item/title/string(),
                    "link": $item/link/string(),
                    "date": $date,
                    "description": $item/description/string()
                }
            ''')
            self.logger.info(f"Recent items (FLWOR): {recent_items}")
        except Exception as e:
            self.logger.error(f"Error executing FLWOR expression: {e}")
            recent_items = "Error: Saxon-HE not available"
        
        # 5. Extract specific values
        item_links = response.xquery_selector.extract_values('//item/link')
        self.logger.info(f"Item links: {item_links[:3] if item_links else []}")
        
        return {
            'items_count': len(items) if items else 0,
            'titles': titles[:5] if titles else [],
            'recent_items': recent_items,
            'item_links': item_links[:5] if item_links else []
        }
    
    @config(age=10 * 24 * 60 * 60)
    def soap_page(self, response):
        """Process SOAP API response with XQuery (simulated)"""
        # 1. Basic XQuery
        note_to = response.xquery('//to/text()')
        note_from = response.xquery('//from/text()')
        note_heading = response.xquery('//heading/text()')
        note_body = response.xquery('//body/text()')
        
        self.logger.info(f"Note: From {note_from} to {note_to}")
        
        # 2. XQuery with element construction
        formatted_note = response.xquery('''
            let $note := //note
            return <formatted_note>
                <sender>{$note/from/text()}</sender>
                <recipient>{$note/to/text()}</recipient>
                <subject>{$note/heading/text()}</subject>
                <message>{$note/body/text()}</message>
            </formatted_note>
        ''')
        self.logger.info(f"Formatted note: {formatted_note}")
        
        # 3. Extract XML
        note_xml = response.xquery_selector.extract_xml('//note')
        self.logger.info(f"Note XML: {note_xml}")
        
        return {
            'note_to': note_to,
            'note_from': note_from,
            'note_heading': note_heading,
            'note_body': note_body,
            'formatted_note': formatted_note,
            'note_xml': note_xml
        }
