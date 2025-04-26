import time
from pyspider.libs.utils import utf8
from pyspider.database.sqlite.projectdb import ProjectDB

projectdb = ProjectDB('data/project.db')

# 新しい名前でプロジェクトを作成
project = {
    'name': 'test_project_new',  # 新しい名前
    'group': '',
    'status': 'RUNNING',
    'script': '''
import time

def on_start(self):
    self.crawl('http://example.com/', callback=self.index_page)

def index_page(self, response):
    return {
        "title": response.doc('title').text(),
        "url": response.url,
        "time": time.time()
    }
''',
    'rate': 1,
    'burst': 10,
    'updatetime': time.time()
}

# 新しいプロジェクトを保存
projectdb.insert(project['name'], project)
print("New project created successfully!")

# 保存されたプロジェクトを確認
saved_project = projectdb.get(project['name'])
print("New project:", saved_project)
