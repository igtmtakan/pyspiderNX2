#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyspider.database.sqlite import projectdb

# データベースに接続
db = projectdb.ProjectDB('./data/project.db')

# プロジェクト「123」のスクリプトを取得
script = db.get('123')['script']

# 構文エラーを修正
script = script.replace('}return {', '}\n        return {')

# 更新したスクリプトを保存
db.update('123', {'script': script})

print('Syntax error fixed successfully')
