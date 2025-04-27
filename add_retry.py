#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyspider.database.sqlite import projectdb

# データベースに接続
db = projectdb.ProjectDB('./data/project.db')

# amazon_improvedプロジェクトのスクリプトを取得
script = db.get('amazon_improved')['script']

# リトライ機能を追加
if '"retries":' not in script:
    script = script.replace('"puppeteer": {', '"retries": 3,\n        "retry_delay": 10,\n        "puppeteer": {')

# 更新したスクリプトを保存
db.update('amazon_improved', {'script': script})

print('Retry functionality added successfully')
