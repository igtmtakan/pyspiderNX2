#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2025-04-27 11:05:52
# Project: yahoo

from pyspider.libs.base_handler import *
import random
import time
import urllib.parse


class Handler(BaseHandler):
    crawl_config = {
        "verify": False,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        },
        "timeout": 60,
        "connect_timeout": 30,
        "retries": 3,
        "retry_delay": 5
    }

    # ユーザーエージェントのリスト
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
    ]

    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl('https://finance.yahoo.co.jp/news', 
                  callback=self.index_page,
                  headers={"User-Agent": random.choice(self.user_agents)})

    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        # ニュース記事のリンクを抽出
        news_links = []
        for each in response.doc('a[href^="https://finance.yahoo.co.jp/news/"]').items():
            if '/news/detail/' in each.attr.href:
                news_links.append(each.attr.href)
        
        # 重複を削除
        news_links = list(set(news_links))
        
        self.logger.info(f"Found {len(news_links)} news links")
        
        # ニュース記事をクロール
        for link in news_links:
            # ランダムな待機時間を追加
            time.sleep(random.uniform(1, 3))
            self.crawl(link, 
                      callback=self.detail_page,
                      headers={"User-Agent": random.choice(self.user_agents)})
        
        # その他のリンクもクロール
        for each in response.doc('a[href^="http"]').items():
            # Yahoo!ファイナンスのドメイン内のリンクのみをクロール
            if 'finance.yahoo.co.jp' in each.attr.href and each.attr.href not in news_links:
                # ランダムな待機時間を追加
                time.sleep(random.uniform(0.5, 1.5))
                self.crawl(each.attr.href, 
                          callback=self.index_page,
                          headers={"User-Agent": random.choice(self.user_agents)})

    @config(priority=2)
    def detail_page(self, response):
        try:
            # タイトルを取得
            title = response.doc('title').text()
            
            # 記事の本文を取得
            content = response.doc('.article_body').text()
            
            # 公開日時を取得
            publish_date = response.doc('.dtPublished').text()
            
            # カテゴリを取得
            category = response.doc('.category').text()
            
            self.logger.info(f"Scraped article: {title}")
            
            return {
                "url": response.url,
                "title": title,
                "content": content,
                "publish_date": publish_date,
                "category": category
            }
        except Exception as e:
            self.logger.error(f"Error scraping {response.url}: {str(e)}")
            return {
                "url": response.url,
                "title": response.doc('title').text(),
                "error": str(e)
            }
