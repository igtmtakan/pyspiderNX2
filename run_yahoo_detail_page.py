#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
from pyspider.database.sqlite import projectdb

# データベースに接続
db = projectdb.ProjectDB('./data/project.db')

# yahooプロジェクトのスクリプトを取得
script = db.get('yahoo')['script']

# タスクを定義（detail_pageメソッドを呼び出す）
task = {
    "taskid": "detail_page_test",
    "project": "yahoo",
    "url": "https://finance.yahoo.co.jp/news",
    "process": {
        "callback": "detail_page"
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

# レスポンスをファイルに保存
with open('yahoo_detail_page_response.json', 'w', encoding='utf-8') as f:
    f.write(response.text)

print("Response saved to yahoo_detail_page_response.json")

# 結果を表示
data = json.loads(response.text)
print("Result:", data.get("result"))
