#!/usr/bin/env python
# -*- coding: utf-8 -*-

import redis
import time
import json
import os
import logging
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# ログの設定
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'queue_monitor.log')

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Redisに接続
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()  # 接続テスト
    logging.info("Redisに接続しました")
except redis.ConnectionError as e:
    logging.error(f"Redisへの接続に失敗しました: {str(e)}")
    exit(1)

# 閾値の設定
QUEUE_THRESHOLD = 10000  # キューのサイズがこの値を超えると警告
PROCESSING_TIME_THRESHOLD = 3600  # タスクの処理時間がこの値（秒）を超えると警告
ALERT_INTERVAL = 3600  # アラートの送信間隔（秒）

# 最後のアラート送信時刻を記録する辞書
last_alerts = {}

def send_alert(subject, message):
    """
    アラートを送信する関数
    実際のメール送信は環境に合わせて設定する必要があります
    """
    logging.warning(f"アラート: {subject} - {message}")
    
    # メール送信の設定（実際の環境に合わせて設定）
    # msg = MIMEText(message)
    # msg['Subject'] = subject
    # msg['From'] = 'pyspider@example.com'
    # msg['To'] = 'admin@example.com'
    
    # # メール送信
    # try:
    #     s = smtplib.SMTP('localhost')
    #     s.send_message(msg)
    #     s.quit()
    #     logging.info(f"アラートメールを送信しました: {subject}")
    # except Exception as e:
    #     logging.error(f"メール送信に失敗しました: {str(e)}")

def can_send_alert(alert_key):
    """
    アラートを送信できるかどうかを判断する関数
    同じアラートが短時間に連続して送信されるのを防ぐ
    """
    current_time = time.time()
    if alert_key not in last_alerts or current_time - last_alerts[alert_key] > ALERT_INTERVAL:
        last_alerts[alert_key] = current_time
        return True
    return False

def monitor_queues():
    """
    Redisキューを監視する関数
    """
    logging.info("キューの監視を開始します")
    
    try:
        # キューのサイズを取得
        queue_keys = r.keys('pyspider:scheduler:*:queue')
        for queue_key in queue_keys:
            queue_name = queue_key.decode('utf-8')
            queue_size = r.llen(queue_name)
            logging.info(f"キュー {queue_name}: サイズ {queue_size}")
            
            if queue_size > QUEUE_THRESHOLD and can_send_alert(f"queue_size:{queue_name}"):
                send_alert(
                    'PySpider Queue Alert',
                    f'Queue {queue_name} size ({queue_size}) exceeds threshold ({QUEUE_THRESHOLD})'
                )
        
        # 処理中のタスクを確認
        processing_keys = r.keys('pyspider:scheduler:*:processing')
        for processing_key in processing_keys:
            processing_name = processing_key.decode('utf-8')
            processing_tasks = r.hgetall(processing_name)
            current_time = time.time()
            
            for task_id, start_time in processing_tasks.items():
                task_id = task_id.decode('utf-8')
                try:
                    start_time = float(start_time)
                    processing_time = current_time - start_time
                    
                    if processing_time > PROCESSING_TIME_THRESHOLD and can_send_alert(f"processing_time:{task_id}"):
                        send_alert(
                            'PySpider Task Alert',
                            f'Task {task_id} has been processing for {processing_time:.2f} seconds'
                        )
                except (ValueError, TypeError) as e:
                    logging.error(f"タスク {task_id} の処理時間の解析に失敗しました: {str(e)}")
        
        # カウンターの状態を確認
        counter_keys = r.keys('pyspider:scheduler:*:counter:*')
        counters = {}
        
        for counter_key in counter_keys:
            counter_name = counter_key.decode('utf-8')
            counter_value = r.get(counter_key)
            if counter_value:
                try:
                    counter_value = int(counter_value)
                    counters[counter_name] = counter_value
                except (ValueError, TypeError) as e:
                    logging.error(f"カウンター {counter_name} の値の解析に失敗しました: {str(e)}")
        
        # カウンターの状態をログに記録
        if counters:
            logging.info(f"カウンターの状態: {json.dumps(counters, indent=2)}")
        
    except Exception as e:
        logging.error(f"キューの監視中にエラーが発生しました: {str(e)}")

if __name__ == '__main__':
    logging.info(f"PySpider Queue Monitor を開始しました - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    monitor_queues()
    logging.info(f"PySpider Queue Monitor を終了しました - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
