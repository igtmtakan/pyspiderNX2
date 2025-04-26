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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        },
        "timeout": 3000,
        "connect_timeout": 1000,
        "js_script_timeout": 60,
        "js_run_at": "document-end",
        "js_script": """
        // Amazon Fix for PySpider
        // This script defines missing functions in Amazon pages to prevent errors

        // Define markFeatureRenderForImageBlock function if not exists
        if (typeof window.markFeatureRenderForImageBlock === 'undefined') {
            window.markFeatureRenderForImageBlock = function() {
                console.log('Mock markFeatureRenderForImageBlock called');
                return true;
            };
        }

        // Define other potentially missing Amazon functions
        if (typeof window.P === 'undefined') {
            window.P = {
                register: function() { return {}; },
                execute: function() { return {}; },
                when: function() { return { execute: function() {} }; }
            };
        }

        // Define jQuery if not exists (some Amazon pages expect it)
        if (typeof window.jQuery === 'undefined') {
            window.jQuery = function() { 
                return {
                    on: function() { return this; },
                    ready: function(fn) { setTimeout(fn, 0); return this; }
                };
            };
            window.$ = window.jQuery;
        }

        console.log('Amazon fix script loaded successfully');
        """
    }
    
    

    @config(fetch_type="js")
    def on_start(self):  self.crawl('https://www.amazon.co.jp/gp/bestsellers/videogames/ref=zg_bs_nav_videogames_0',timeout=500,connect_timeout=1000,callback=self.index_page)              

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
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Try to get the image source, but handle potential errors
            try:
                image_src = response.doc("img#landingImage").attr.src
                if not image_src:
                    self.logger.warning("Image source not found, using placeholder")
                    image_src = "https://via.placeholder.com/300"
            except Exception as e:
                self.logger.error(f"Error getting image source: {e}")
                image_src = "https://via.placeholder.com/300"
            
            parsed_url = urlparse(image_src)
            file_name = os.path.basename(parsed_url.path)
            
            # Create images directory if it doesn't exist
            os.makedirs(os.path.join(script_dir, 'images'), exist_ok=True)
            
            response_img = requests.get(image_src)
            if response_img.status_code == 200:
                with open(os.path.join(script_dir, 'images', file_name), 'wb') as savefile:
                    savefile.write(response_img.content)
                    
            # WordPressへの接続情報
            wp_url = 'http://www.torimon.shop/xmlrpc.php?token=1234'
            wp_username = 'admin'
            wp_password = 'password'

            # クライアントの作成
            client = Client(wp_url, wp_username, wp_password)

            # アップロードする画像のパス
            image_path = os.path.join(script_dir, 'images', file_name)

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
            self.logger.info(f'画像のURL: {wp_response["url"]}')
            self.logger.info(f'メディアID: {wp_response["id"]}')

            # アップロードした画像のIDを保存
            uploaded_image_id = wp_response['id']

            # 新しい投稿を作成
            post = WordPressPost()
            post.title = response.doc('title').text()
            post.content = f'''
    <p>これは新しい投稿のコンテンツです。</p>
    <p>画像は以下のようになります：</p>
    <img src="{wp_response['url']}" alt="投稿画像">
    ''' + response.doc('#feature-bullets').text()

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

            self.logger.info(f'投稿完了！投稿ID: {post_id}')
                    
            return {
                "url": response.url,
                "detail": response.doc('#feature-bullets').text(),
                "title": response.doc('title').text(),
            }
        except Exception as e:
            self.logger.error(f"Error in detail_page: {e}")
            return {
                "url": response.url,
                "error": str(e)
            }
