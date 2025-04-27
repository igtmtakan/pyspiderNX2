#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyspider.database.sqlite import projectdb

# データベースに接続
db = projectdb.ProjectDB('./data/project.db')

# 改善されたスクリプトを読み込む
with open('improved_yahoo_script.py', 'r') as f:
    script = f.read()

# yahooプロジェクトを更新
db.update('yahoo', {'script': script})

print('Yahoo project script updated successfully')
