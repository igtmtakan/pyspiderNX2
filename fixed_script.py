#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2025-03-01 12:47:46
# Project: jsrender

from pyspider.libs.base_handler import *
import requests
from bs4 import BeautifulSoup
import xmlrpc.client
import os
from pathlib import Path
import base64
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
import mimetypes
import urllib.request
from urllib.parse import urlparse
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods import media, posts
from wordpress_xmlrpc.methods.posts import NewPost
from wordpress_xmlrpc.compat import xmlrpc_client




class Handler(BaseHandler):
    crawl_config = {
        "headers": {
            "User-Agent": "GoogleBot",
        },
        "timeout":3000,
        "connect_timeout":1000
    }
    
    

    @config(fetch_type="js")
    def on_start(self):
        self.crawl(
            'https://www.amazon.co.jp/gp/bestsellers/videogames/ref=zg_bs_nav_videogames_0',
            timeout=500,
            connect_timeout=1000,
            callback=self.index_page
        )


    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        for each in response.doc('a.a-link-normal.aok-block').items():
            self.crawl(each.attr.href, callback=self.detail_page)
        
        more_link = response.doc("li.a-last a")
        #self.crawl(response.doc('#right a').attr.href, callback=self.index_page)
        #input[type="text"]
        if more_link:
            next_page_url = more_link.attr.href
            self.crawl(next_page_url, callback=self.index_page)

    def wp_upload_image(wp_url, username, password, img_path, img_name=None):
        # クライアントの作成
        wp = Client(wp_url, username, password)

        # アップロードする画像のパスと名前
        if img_name is None:
            img_name = os.path.basename(img_path)

        # 画像の読み込み
        with open(img_path, 'rb') as img:
            data = {
                'name': img_name,
                'type': 'image/jpeg',  # 画像のMIMEタイプ
                'bits': img.read(),
            }

        # 画像のアップロード
        response = wp.call(media.UploadFile(data))
        return response

            
    @config(fetch_type="js")
    def detail_page(self, response):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        #url = "https://www.sejuku.net/blog/"

        #responsej = requests.get(url)
        #responsej.encoding = responsej.apparent_encoding

        #bs = BeautifulSoup(responsej.text, 'html.parser')

        #print(bs.title.string)
        
        #wp_url = "http://www.torimon.shop/xmlrpc.php?token=1234"  # WordPressサイトのURL
        #wp_username = "admin"  # WordPressのユーザー名
        #wp_password = "password"  # WordPressのパスワード
        #wp = WordPressXMLRPC(wp_url, wp_username, wp_password)

    ##    title = "テスト投稿"
    #    content = """
    #    これはXML-RPCを使用したテスト投稿です。
    #    投稿日時: {}
    #    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        image_src = response.doc("img#landingImage").attr.src;
        
        parsed_url = urlparse(image_src)
        file_name = os.path.basename(parsed_url.path)
        
        #url = image_src
        #dst_path = 'images/'+file_name

        #urllib.request.urlretrieve(url, dst_path)
        
        
        response_img = requests.get(image_src)
        if response_img.status_code == 200:
            with open(script_dir+'/images/'+file_name,'wb') as savefile:
                savefile.write(response_img.content)
                
                
        # WordPressへの接続情報
        wp_url = 'http://www.torimon.shop/xmlrpc.php?token=1234'
        wp_username = 'admin'
        wp_password = 'password'

        # クライアントの作成
        client = Client(wp_url, wp_username, wp_password)

        # アップロードする画像のパス
        image_path = script_dir+'/images/'+file_name

        # 画像のメタデータ
        data = {
            'name': 'image.jpg',
            'type': 'image/jpeg',  # 画像のMIMEタイプ
        }

        # 画像をバイナリ形式で読み込む
        with open(image_path, 'rb') as img:
            data['bits'] = img.read()

        # 画像をアップロード
        wp_response = client.call(media.UploadFile(data))

        # アップロード結果の表示
        print('画像のURL:', wp_response['url'])
        print('メディアID:', wp_response['id'])

        # アップロードした画像のIDを保存
        uploaded_image_id = wp_response['id']

        # 新しい投稿を作成
        post = WordPressPost()
        post.title = response.doc('title').text()
        post.content = '''
<p>これは新しい投稿のコンテンツです。</p>
<p>画像は以下のようになります：</p>
<img src="{}" alt="投稿画像">
'''.format(wp_response['url']) + response.doc('#feature-bullets').text();

        # カテゴリとタグを設定（オプション）
        post.terms_names = {
            'category': ['カテゴリー1', 'カテゴリー2'],
            'post_tag': ['タグ1', 'タグ2']
        }

        # カスタムフィールドを設定
        post.custom_fields = [
            {'key': 'field_key1', 'value': 'フィールド値1'},
            {'key': 'field_key2', 'value': 'フィールド値2'}
        ]

        # 投稿ステータスを設定（publish, draft, pending, private, etc.）
        post.post_status = 'publish'

        # アイキャッチ画像（フィーチャード画像）を設定
        post.thumbnail = uploaded_image_id

        # 投稿を送信
        post_id = client.call(posts.NewPost(post))

        print('投稿完了！投稿ID:', post_id)
                
                




        
        return {
            "url": response.url,
            "detail": response.doc('#feature-bullets').text(),
            "title": response.doc('title').text(),
        }
