#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
from pyspider.database.sqlite import projectdb

# データベースに接続
db = projectdb.ProjectDB('./data/project.db')

# yahooプロジェクトのスクリプトを取得
script = db.get('yahoo')['script']

# タスクを定義（on_startメソッドを呼び出す）
task = {
    "taskid": "data:,on_start",
    "project": "yahoo",
    "url": "data:,on_start",
    "process": {
        "callback": "on_start"
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
with open('improved_yahoo_response.json', 'w', encoding='utf-8') as f:
    f.write(response.text)

print("Response saved to improved_yahoo_response.json")

# フォローの数を表示
data = json.loads(response.text)
print(f"Number of follows: {len(data.get('follows', []))}")
if data.get('follows'):
    print("First follow:", data['follows'][0]['url'])
