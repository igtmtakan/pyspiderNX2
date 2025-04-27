#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
from pyspider.database.sqlite import projectdb

# データベースに接続
db = projectdb.ProjectDB('./data/project.db')

# yahooプロジェクトのスクリプトを取得
script = db.get('yahoo')['script']

# タスクを定義（index_pageメソッドを呼び出す）
task = {
    "taskid": "132fdf92bfff698466ac449622cb0035",
    "project": "yahoo",
    "url": "https://finance.yahoo.co.jp/news",
    "process": {
        "callback": "index_page"
    }
}

# POSTリクエストを送信
response = requests.post(
    "http://localhost:5000/debug-v2/yahoo/run",
    data={
        "task": json.dumps(task),
        "script": script
    }
)

# レスポンスを表示
print(response.status_code)
print(response.text)
