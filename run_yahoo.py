#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
from pyspider.database.sqlite import projectdb

# データベースに接続
db = projectdb.ProjectDB('./data/project.db')

# yahooプロジェクトのスクリプトを取得
script = db.get('yahoo')['script']

# タスクを定義
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
    "http://localhost:5000/debug/yahoo/run",
    data={
        "task": json.dumps(task),
        "script": script
    }
)

# レスポンスを表示
print(response.status_code)
print(response.text)
