#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2025-03-01 12:47:46
# Project: jsrender

from pyspider.libs.base_handler import *
import requests
from bs4 import BeautifulSoup
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


class Handler(BaseHandler):
    crawl_config = {
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        },
        "timeout": 3000,
        "connect_timeout": 1000
    }
    
    @config(fetch_type="puppeteer")
    def on_start(self):
        self.crawl(
            'https://www.amazon.co.jp/gp/bestsellers/videogames/ref=zg_bs_nav_videogames_0',
            timeout=500,
            connect_timeout=1000,
            callback=self.index_page
        )
        self.logger.info("Started crawling Amazon bestsellers")

    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        self.logger.info(f"Processing index page: {response.url}")
        
        # 各商品リンクをクロール
        for each in response.doc('a.a-link-normal.aok-block').items():
            self.crawl(each.attr.href, fetch_type="puppeteer", callback=self.detail_page)
            self.logger.debug(f"Added product URL to queue: {each.attr.href}")
        
        # 次のページをクロール
        more_link = response.doc("li.a-last a")
        if more_link:
            next_page_url = more_link.attr.href
            self.crawl(next_page_url, fetch_type="puppeteer", callback=self.index_page)
            self.logger.info(f"Added next page to queue: {next_page_url}")

    def wp_upload_image(self, wp_url, username, password, img_path, img_name=None):
        """WordPressに画像をアップロードする"""
        try:
            # クライアントの作成
            wp = Client(wp_url, username, password)

            # アップロードする画像のパスと名前
            if img_name is None:
                img_name = os.path.basename(img_path)

            # 画像の読み込み
            with open(img_path, 'rb') as img:
                data = {
                    'name': img_name,
                    'type': mimetypes.guess_type(img_path)[0] or 'image/jpeg',
                    'bits': img.read(),
                }

            # 画像のアップロード
            response = wp.call(media.UploadFile(data))
            return response
        except Exception as e:
            self.logger.error(f"Error uploading image: {e}")
            return None
            
    @config(fetch_type="puppeteer")
    def detail_page(self, response):
        self.logger.info(f"Processing detail page: {response.url}")
        
        try:
            # スクリプトのディレクトリを取得
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 画像ディレクトリを作成（存在しない場合）
            images_dir = os.path.join(script_dir, 'images')
            os.makedirs(images_dir, exist_ok=True)
            
            # 商品画像のURLを取得
            image_src = response.doc("img#landingImage").attr.src
            if not image_src:
                self.logger.warning(f"No image found on page: {response.url}")
                return {
                    "url": response.url,
                    "detail": response.doc('#feature-bullets').text(),
                    "title": response.doc('title').text(),
                    "error": "No image found"
                }
            
            # 画像ファイル名を取得
            parsed_url = urlparse(image_src)
            file_name = os.path.basename(parsed_url.path)
            
            # 画像をダウンロード
            response_img = requests.get(image_src)
            image_path = os.path.join(images_dir, file_name)
            
            if response_img.status_code == 200:
                with open(image_path, 'wb') as savefile:
                    savefile.write(response_img.content)
                self.logger.info(f"Image saved to {image_path}")
            else:
                self.logger.error(f"Failed to download image: {image_src}, status code: {response_img.status_code}")
                return {
                    "url": response.url,
                    "detail": response.doc('#feature-bullets').text(),
                    "title": response.doc('title').text(),
                    "error": f"Image download failed with status code {response_img.status_code}"
                }
                
            # WordPressへの接続情報
            wp_url = 'http://www.torimon.shop/xmlrpc.php?token=1234'
            wp_username = 'admin'
            wp_password = 'password'

            try:
                # クライアントの作成
                client = Client(wp_url, wp_username, wp_password)

                # 画像のメタデータ
                data = {
                    'name': file_name,
                    'type': mimetypes.guess_type(image_path)[0] or 'image/jpeg',
                }

                # 画像をバイナリ形式で読み込む
                with open(image_path, 'rb') as img:
                    data['bits'] = img.read()

                # 画像をアップロード
                wp_response = client.call(media.UploadFile(data))
                self.logger.info(f"Image uploaded to WordPress: {wp_response['url']}")

                # アップロードした画像のIDを保存
                uploaded_image_id = wp_response['id']

                # 商品詳細を取得
                product_title = response.doc('title').text()
                product_details = response.doc('#feature-bullets').text()

                # 新しい投稿を作成
                post = WordPressPost()
                post.title = product_title
                post.content = f'''
<p>これは新しい投稿のコンテンツです。</p>
<p>画像は以下のようになります：</p>
<img src="{wp_response['url']}" alt="投稿画像">
{product_details}
'''

                # カテゴリとタグを設定
                post.terms_names = {
                    'category': ['ゲーム', 'Amazon'],
                    'post_tag': ['ゲーム', 'ベストセラー']
                }

                # カスタムフィールドを設定
                post.custom_fields = [
                    {'key': 'amazon_url', 'value': response.url},
                    {'key': 'crawled_date', 'value': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                ]

                # 投稿ステータスを設定
                post.post_status = 'publish'

                # アイキャッチ画像を設定
                post.thumbnail = uploaded_image_id

                # 投稿を送信
                post_id = client.call(posts.NewPost(post))
                self.logger.info(f"Post published with ID: {post_id}")

                return {
                    "url": response.url,
                    "detail": product_details,
                    "title": product_title,
                    "image_url": wp_response['url'],
                    "post_id": post_id
                }
                
            except Exception as e:
                self.logger.error(f"WordPress error: {e}")
                return {
                    "url": response.url,
                    "detail": response.doc('#feature-bullets').text(),
                    "title": response.doc('title').text(),
                    "error": f"WordPress error: {str(e)}"
                }
                
        except Exception as e:
            self.logger.error(f"Error processing detail page: {e}")
            return {
                "url": response.url,
                "error": f"Processing error: {str(e)}"
            }
