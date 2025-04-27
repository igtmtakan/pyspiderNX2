#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2024-04-27 12:30:00
# Project: amazon_scraper_fixed

import os
import requests
from urllib.parse import urlparse
from pyspider.libs.base_handler import *


class Handler(BaseHandler):
    crawl_config = {
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        },
        "timeout": 3000,
        "connect_timeout": 1000
    }

    @config(fetch_type="js", js_script_path="amazon_map_polyfill.js", js_run_at="document-end", js_timeout=60)
    def on_start(self):
        self.crawl(
            'https://www.amazon.co.jp/gp/bestsellers/videogames/ref=zg_bs_nav_videogames_0',
            timeout=500,
            connect_timeout=1000,
            js_script_path="amazon_map_polyfill.js",
            js_run_at="document-end",
            js_timeout=60,
            fetch_type="js",
            callback=self.index_page
        )
        self.logger.info("Started crawling Amazon bestsellers with Map polyfill")

    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        self.logger.info(f"Processing index page: {response.url}")

        try:
            # 各商品リンクをクロール
            product_links = []
            for each in response.doc('a.a-link-normal.aok-block').items():
                product_links.append(each.attr.href)

            # 商品リンクが見つからない場合は別のセレクタを試す
            if not product_links:
                for each in response.doc('a.a-link-normal[href*="/dp/"]').items():
                    product_links.append(each.attr.href)

            # 商品リンクが見つからない場合は別のセレクタを試す
            if not product_links:
                for each in response.doc('a[href*="/dp/"]').items():
                    product_links.append(each.attr.href)

            self.logger.info(f"Found {len(product_links)} product links")

            # 重複を削除
            product_links = list(set(product_links))

            for url in product_links:
                self.crawl(url,
                          fetch_type="js",
                          js_script_path="amazon_map_polyfill.js",
                          js_run_at="document-end",
                          js_timeout=60,
                          callback=self.detail_page)
                self.logger.debug(f"Added product URL to queue: {url}")

            # 次のページをクロール
            more_link = response.doc("li.a-last a")
            if more_link:
                next_page_url = more_link.attr.href
                self.crawl(next_page_url,
                          fetch_type="js",
                          js_script_path="amazon_map_polyfill.js",
                          js_run_at="document-end",
                          js_timeout=60,
                          callback=self.index_page)
                self.logger.info(f"Added next page to queue: {next_page_url}")
        except Exception as e:
            self.logger.error(f"Error processing index page {response.url}: {str(e)}")

    @config(priority=2)
    def detail_page(self, response):
        self.logger.info(f"Processing detail page: {response.url}")

        try:
            # 商品情報を取得
            title = response.doc('title').text()

            # 価格を取得（複数のセレクタを試す）
            price = response.doc('#corePriceDisplay_desktop_feature_div .a-offscreen').text()
            if not price:
                price = response.doc('.a-price .a-offscreen').text()
            if not price:
                price = response.doc('#price_inside_buybox').text()
            if not price:
                price = response.doc('#priceblock_ourprice').text()
            if not price:
                price = "価格情報なし"

            # 説明を取得（複数のセレクタを試す）
            description = response.doc('#feature-bullets').text()
            if not description:
                description = response.doc('#productDescription').text()
            if not description:
                description = response.doc('#aplus').text()
            if not description:
                description = "説明なし"

            # 商品画像のURLを取得（複数のセレクタを試す）
            image_src = None
            image_elements = [
                response.doc("img#landingImage"),
                response.doc("img#imgBlkFront"),
                response.doc("#main-image-container img"),
                response.doc(".a-dynamic-image"),
                response.doc("#imageBlock img")
            ]

            for img in image_elements:
                if img and img.attr.src:
                    image_src = img.attr.src
                    break

            if not image_src:
                self.logger.warning(f"No image found on page: {response.url}")
                image_src = "No image found"

            # ASIN（Amazon商品ID）を取得
            asin = ""
            url_parts = response.url.split("/dp/")
            if len(url_parts) > 1:
                asin_part = url_parts[1].split("/")[0].split("?")[0]
                if asin_part:
                    asin = asin_part

            # レビュー情報を取得
            rating = response.doc('#acrPopover').attr.title
            if not rating:
                rating = "レビューなし"

            review_count = response.doc('#acrCustomerReviewText').text()
            if not review_count:
                review_count = "0件"

            # 在庫状況を取得
            availability = response.doc('#availability').text().strip()
            if not availability:
                availability = "在庫状況不明"

            return {
                "url": response.url,
                "title": title,
                "price": price,
                "description": description,
                "image_url": image_src,
                "asin": asin,
                "rating": rating,
                "review_count": review_count,
                "availability": availability
            }

        except Exception as e:
            self.logger.error(f"Error processing detail page {response.url}: {str(e)}")
            return {
                "url": response.url,
                "title": response.doc('title').text() if response.doc('title') else "Title not found",
                "error": str(e)
            }
