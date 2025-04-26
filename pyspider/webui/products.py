#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Trae AI
# Created on 2025-04-18

import os
import json
from flask import jsonify, render_template
from .app import app

@app.route('/products/view', methods=['GET'])
def view_products():
    """
    製品データを表示するHTMLページ
    """
    return render_template('products.html')


@app.route('/products-v2/view', methods=['GET'])
def view_products_v2():
    """
    製品データを表示するHTMLページ（v2バージョン）
    """
    return render_template('products-v2.html')

@app.route('/products', methods=['GET'])
def get_products():
    """
    製品データをJSONフォーマットで返すAPIエンドポイント
    """
    try:
        # プロジェクトルートからJSONファイルのパスを取得
        json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                'amazon_products_20250415.json')

        # JSONファイルが存在するか確認
        if not os.path.exists(json_path):
            return jsonify({
                'status': 'error',
                'message': 'Products data file not found'
            }), 404

        # JSONファイルを読み込む
        with open(json_path, 'r', encoding='utf-8') as f:
            # 単一のJSONオブジェクトの場合
            product_data = json.load(f)

        # 配列に変換して返す
        if isinstance(product_data, dict):
            # タイトルが空の場合はデフォルト値を設定
            if 'title' in product_data and not product_data['title']:
                product_data['title'] = '商品名なし'
            products = [product_data]
        else:
            # 配列の場合、各要素のタイトルをチェック
            products = []
            for item in product_data:
                if isinstance(item, dict) and 'title' in item and not item['title']:
                    item['title'] = '商品名なし'
                products.append(item)

        return jsonify({
            'status': 'success',
            'data': products
        })

    except Exception as e:
        app.logger.error(f'Error loading products data: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': f'Error loading products data: {str(e)}'
        }), 500
