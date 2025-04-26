from pyspider.libs.base_handler import *

class Handler(BaseHandler):
    crawl_config = {
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124",
        },
        "verify": False,  # SSL証明書の検証を無効化
        "allow_redirects": True,
        "fetch": {
            "js_disable_ssl_verify": True  # JavaScript実行時のSSL検証を無効化
        }
    }

    @config(fetch_type="playwright")
    def on_start(self):
        self.crawl('https://example.com', 
                  callback=self.index_page,
                  fetch={
                      'verify': False,  # 個別のリクエストでもSSL検証を無効化
                  })

    def index_page(self, response):
        # Process the response
        print(response.doc('title').text())
