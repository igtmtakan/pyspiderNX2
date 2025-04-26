#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: PySpider Team
# Created on 2025-04-26

import logging
import functools
import ipaddress
from flask import request, abort, current_app
from .app import app

logger = logging.getLogger(__name__)

# 許可するIPアドレスのリスト
ALLOWED_IPS = [
    '127.0.0.1',       # localhost
    '::1',             # localhost IPv6
    '192.168.0.0/16',  # プライベートネットワーク
    '10.0.0.0/8',      # プライベートネットワーク
    '172.16.0.0/12',   # プライベートネットワーク
]

# レート制限の設定
RATE_LIMIT = {
    'default': '200 per day, 50 per hour',
    'api': '1000 per day, 100 per hour',
    'login': '20 per hour, 5 per minute'
}

def is_ip_allowed(ip):
    """IPアドレスが許可リストに含まれているかチェックする"""
    try:
        client_ip = ipaddress.ip_address(ip)
        for allowed_ip in ALLOWED_IPS:
            if '/' in allowed_ip:
                # CIDRブロックの場合
                if client_ip in ipaddress.ip_network(allowed_ip):
                    return True
            else:
                # 単一IPアドレスの場合
                if client_ip == ipaddress.ip_address(allowed_ip):
                    return True
        return False
    except ValueError:
        logger.error(f"Invalid IP address: {ip}")
        return False

def restrict_access(func):
    """特定のIPアドレスからのアクセスのみを許可するデコレータ"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        client_ip = request.remote_addr
        if not is_ip_allowed(client_ip):
            logger.warning(f"Unauthorized access attempt from {client_ip}")
            abort(403)  # Forbidden
        return func(*args, **kwargs)
    return wrapper

def init_security():
    """セキュリティ設定を初期化する"""
    try:
        # 管理者向けエンドポイントにアクセス制限を適用
        admin_endpoints = [
            '/debug/<project>',
            '/task/<project>',
            '/results',
            '/tasks',
            '/metrics',
            '/metrics/health'
        ]
        
        # 各エンドポイントにデコレータを適用
        for endpoint in admin_endpoints:
            view_func = app.view_functions.get(endpoint)
            if view_func:
                app.view_functions[endpoint] = restrict_access(view_func)
        
        logger.info("Security settings initialized")
    except Exception as e:
        logger.error(f"Error initializing security settings: {str(e)}")

# セキュリティ設定を初期化
init_security()
