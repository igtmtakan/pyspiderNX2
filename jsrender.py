#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2025-03-01 12:47:46
# Project: jsrender

from pyspider.libs.base_handler import *
import requests
import os
import urllib3
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from urllib3.contrib.pyopenssl import inject_into_urllib3

# OpenSSLをURLLib3に注入
inject_into_urllib3()

# カスタムアダプタークラスの定義
class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(
            ciphers='DEFAULT:@SECLEVEL=1',  # 暗号化レベルを調整
            cert_reqs=0,  # 証明書検証を無効化（必要な場合のみ）
            options=0x4  # SSL_OP_LEGACY_SERVER_CONNECT
        )
        kwargs['ssl_context'] = context
        return super(TLSAdapter, self).init_poolmanager(*args, **kwargs)

class Handler(BaseHandler):
    crawl_config = {
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        },
        'verify': False,  # SSL検証を無効化
        'allow_redirects': True
    }

    def __init__(self):
        self.session = requests.Session()
        # カスタムアダプターを設定
        adapter = TLSAdapter()
        self.session.mount('https://', adapter)
        # SSL警告を無効化
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def on_start(self):
        self.crawl('対象URL', 
                  callback=self.index_page,
                  fetch_type='requests',  # requestsを使用
                  validate_cert=False)    # 証明書検証を無効化

    def index_page(self, response):
        # ページの処理ロジック
        pass
