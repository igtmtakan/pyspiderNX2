#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyspider.database.sqlite import projectdb

# データベースに接続
db = projectdb.ProjectDB('./data/project.db')

# yahooプロジェクトのスクリプトを取得
script = db.get('yahoo')['script']

# index_pageメソッドを修正
script = script.replace("""    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        for each in response.doc('a[href^="http"]').items():
            self.crawl(each.attr.href, callback=self.detail_page)""", """    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        for each in response.doc('a[href^="http"]').items():
            self.crawl(each.attr.href, callback=self.detail_page)
        return {"status": "ok"}""")

# 更新したスクリプトを保存
db.update('yahoo', {'script': script})

print('Yahoo project script updated successfully')
