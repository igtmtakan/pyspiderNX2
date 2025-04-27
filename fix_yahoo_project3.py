#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyspider.database.sqlite import projectdb

# データベースに接続
db = projectdb.ProjectDB('./data/project.db')

# yahooプロジェクトのスクリプトを取得
script = db.get('yahoo')['script']

# detail_pageメソッドを修正
script = script.replace("""    @config(priority=2)
    def detail_page(self, response):
        return {
            "url": response.url,
            "title": response.doc('title').text(),
        }""", """    @config(priority=2)
    def detail_page(self, response):
        return {
            "url": response.url,
            "title": response.doc('title').text(),
        }""")

# 完全に新しいスクリプトを作成
new_script = """#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2025-04-27 11:05:52
# Project: yahoo

from pyspider.libs.base_handler import *
import urllib.parse


class Handler(BaseHandler):
    crawl_config = {
        "verify": False,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        }
    }

    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl('https://finance.yahoo.co.jp/news', callback=self.index_page)
        return {"status": "ok"}

    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        for each in response.doc('a[href^="http"]').items():
            self.crawl(each.attr.href, callback=self.detail_page)
        return {"status": "ok"}

    @config(priority=2)
    def detail_page(self, response):
        return {
            "url": response.url,
            "title": response.doc('title').text(),
        }
"""

# 更新したスクリプトを保存
db.update('yahoo', {'script': new_script})

print('Yahoo project script completely updated')
