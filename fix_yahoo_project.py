#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyspider.database.sqlite import projectdb

# データベースに接続
db = projectdb.ProjectDB('./data/project.db')

# yahooプロジェクトのスクリプトを取得
script = db.get('yahoo')['script']

# crawl_configにSSL検証を無効にする設定を追加
script = script.replace("    crawl_config = {\n    }", """    crawl_config = {
        "verify": False,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        }
    }""")

# on_startメソッドを修正
script = script.replace("""    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl('https://finance.yahoo.co.jp/news', callback=self.index_page)""", """    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl('https://finance.yahoo.co.jp/news', callback=self.index_page)
        return {"status": "ok"}""")

# 更新したスクリプトを保存
db.update('yahoo', {'script': script})

print('Yahoo project script updated successfully')
