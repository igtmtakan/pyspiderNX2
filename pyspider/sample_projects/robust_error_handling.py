#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: PySpider Team
# Created on 2025-04-26 12:00:00

"""
Sample project demonstrating robust error handling techniques
"""

import time
import traceback
import logging
from pyspider.libs.base_handler import *

class Handler(BaseHandler):
    crawl_config = {
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        },
        'timeout': 30,  # 30秒のタイムアウト
        'connect_timeout': 10,  # 10秒の接続タイムアウト
        'retries': 3,  # 3回のリトライ
    }
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        super(Handler, self).__init__()
    
    def handle_error(self, error, task):
        """エラーを処理するヘルパーメソッド"""
        error_type = type(error).__name__
        error_traceback = traceback.format_exc()
        
        self.logger.error(f"Error processing {task.get('url')}: {error_type} - {str(error)}")
        self.logger.debug(f"Traceback: {error_traceback}")
        
        # エラーの種類に基づいて異なる処理を行う
        if "Timeout" in error_type or "ConnectionError" in error_type:
            # タイムアウトやネットワークエラーの場合は、後でリトライするようにスケジュール
            self.logger.info(f"Rescheduling {task.get('url')} due to {error_type}")
            self.crawl(
                task.get('url'),
                callback=task.get('callback'),
                retries=task.get('retries', 0) + 1,
                exetime=time.time() + 60 * (task.get('retries', 0) + 1),  # 指数バックオフ
                save=task.get('save', {})
            )
        
        # エラー情報を含む結果を返す
        return {
            "error": True,
            "error_type": error_type,
            "error_message": str(error),
            "url": task.get('url'),
            "task_id": task.get('taskid')
        }
    
    @every(minutes=24 * 60)
    def on_start(self):
        """スクレイピングの開始点"""
        try:
            # 通常のページ
            self.crawl('https://example.com/', callback=self.index_page)
            
            # 存在しないページ（404エラーのテスト）
            self.crawl('https://example.com/not-found', callback=self.index_page)
            
            # タイムアウトが発生する可能性のあるページ
            self.crawl('https://httpbin.org/delay/10', callback=self.timeout_page, timeout=5)
            
            # 複雑なページ
            self.crawl('https://news.ycombinator.com/', callback=self.complex_page)
        except Exception as e:
            self.logger.error(f"Error in on_start: {str(e)}")
            self.logger.debug(traceback.format_exc())
    
    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        """基本的なページの処理"""
        try:
            # ページのタイトルと内容を抽出
            title = response.doc('title').text()
            paragraphs = [p.text() for p in response.doc('p').items()]
            
            # 結果を返す
            return {
                'url': response.url,
                'status': response.status_code,
                'title': title,
                'paragraphs': paragraphs,
                'success': True
            }
        except Exception as e:
            # エラーハンドリング
            return self.handle_error(e, response.save)
    
    @config(age=10 * 24 * 60 * 60)
    def timeout_page(self, response):
        """タイムアウトが発生する可能性のあるページの処理"""
        try:
            # レスポンスが正常に返ってきた場合の処理
            return {
                'url': response.url,
                'status': response.status_code,
                'delay_info': response.json,
                'success': True
            }
        except Exception as e:
            # エラーハンドリング
            return self.handle_error(e, response.save)
    
    @config(age=10 * 24 * 60 * 60)
    def complex_page(self, response):
        """複雑なページの処理"""
        try:
            # 記事のリストを抽出
            articles = []
            
            # 各記事の情報を抽出
            for item in response.doc('.athing').items():
                try:
                    article_id = item.attr('id')
                    title_element = item.css('.titleline > a')
                    title = title_element.text()
                    url = title_element.attr('href')
                    
                    # 次の要素から点数と投稿者を取得
                    subtext = item.next('.subtext')
                    score_text = subtext.css('.score').text() or '0 points'
                    score = int(score_text.split()[0])
                    author = subtext.css('.hnuser').text()
                    
                    articles.append({
                        'id': article_id,
                        'title': title,
                        'url': url,
                        'score': score,
                        'author': author
                    })
                except Exception as e:
                    # 個々の記事の処理中のエラーをログに記録するが、処理は続行
                    self.logger.warning(f"Error processing article: {str(e)}")
                    continue
            
            # 結果を返す
            return {
                'url': response.url,
                'status': response.status_code,
                'articles_count': len(articles),
                'articles': articles,
                'success': True
            }
        except Exception as e:
            # エラーハンドリング
            return self.handle_error(e, response.save)
    
    def on_result(self, result):
        """結果の処理"""
        try:
            # エラーが発生した場合はログに記録
            if result and result.get('error'):
                self.logger.error(f"Task failed: {result.get('url')} - {result.get('error_type')}: {result.get('error_message')}")
            
            # 成功した場合は情報をログに記録
            elif result and result.get('success'):
                self.logger.info(f"Task succeeded: {result.get('url')}")
            
            # 結果を親クラスのon_resultに渡す
            super(Handler, self).on_result(result)
        except Exception as e:
            self.logger.error(f"Error in on_result: {str(e)}")
