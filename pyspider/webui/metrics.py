#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: PySpider Team
# Created on 2025-04-26

import json
import time
import psutil
import logging
from flask import jsonify
from .app import app

logger = logging.getLogger(__name__)

def get_scheduler_stats():
    """スケジューラの統計情報を取得する"""
    try:
        if not hasattr(app, 'scheduler'):
            return {}
        
        scheduler = app.scheduler
        stats = {
            'queue_size': 0,
            'processing_tasks': 0,
            'total_tasks_24h': 0,
            'failed_tasks_24h': 0,
            'success_tasks_24h': 0,
            'pending_tasks': 0
        }
        
        # キューサイズ
        if hasattr(scheduler, 'queue') and hasattr(scheduler.queue, 'qsize'):
            stats['queue_size'] = scheduler.queue.qsize()
        
        # 処理中のタスク
        if hasattr(scheduler, 'processing'):
            stats['processing_tasks'] = len(scheduler.processing)
        
        # カウンター
        if hasattr(scheduler, 'counter'):
            try:
                stats['total_tasks_24h'] = scheduler.counter('1d', 'sum')
                stats['failed_tasks_24h'] = scheduler.counter('1d', 'failed')
                stats['success_tasks_24h'] = scheduler.counter('1d', 'success')
                stats['pending_tasks'] = scheduler.counter('all', 'pending')
            except Exception as e:
                logger.error(f"Error getting counter stats: {str(e)}")
        
        return stats
    except Exception as e:
        logger.error(f"Error getting scheduler stats: {str(e)}")
        return {}

def get_system_stats():
    """システムの統計情報を取得する"""
    try:
        stats = {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'uptime': time.time() - psutil.boot_time()
        }
        
        # プロセス情報
        process = psutil.Process()
        stats['process_cpu_percent'] = process.cpu_percent(interval=0.1)
        stats['process_memory_percent'] = process.memory_percent()
        stats['process_memory_mb'] = process.memory_info().rss / (1024 * 1024)
        stats['process_threads'] = process.num_threads()
        stats['process_open_files'] = len(process.open_files())
        stats['process_connections'] = len(process.connections())
        
        return stats
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        return {}

@app.route('/metrics')
def metrics():
    """メトリクスエンドポイント"""
    try:
        # 統計情報を収集
        metrics = {
            'timestamp': time.time(),
            'scheduler': get_scheduler_stats(),
            'system': get_system_stats()
        }
        
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error in metrics endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': time.time()
        }), 500

@app.route('/metrics/health')
def health():
    """ヘルスチェックエンドポイント"""
    try:
        # 基本的なヘルスチェック
        system_stats = get_system_stats()
        scheduler_stats = get_scheduler_stats()
        
        # ヘルスステータスを判断
        health_status = 'healthy'
        issues = []
        
        # システムリソースのチェック
        if system_stats.get('cpu_percent', 0) > 90:
            health_status = 'warning'
            issues.append('High CPU usage')
        
        if system_stats.get('memory_percent', 0) > 90:
            health_status = 'warning'
            issues.append('High memory usage')
        
        if system_stats.get('disk_percent', 0) > 90:
            health_status = 'warning'
            issues.append('High disk usage')
        
        # スケジューラのチェック
        if scheduler_stats.get('queue_size', 0) > 10000:
            health_status = 'warning'
            issues.append('Large queue size')
        
        if scheduler_stats.get('processing_tasks', 0) > 1000:
            health_status = 'warning'
            issues.append('Many processing tasks')
        
        # レスポンスを返す
        return jsonify({
            'status': health_status,
            'issues': issues,
            'timestamp': time.time()
        })
    except Exception as e:
        logger.error(f"Error in health endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        }), 500
