#!/bin/bash

# 色の定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}PySpider 安定化機能のアンインストール${NC}"
echo "=================================="

# PySpiderプロセスを停止
echo -e "${YELLOW}PySpiderプロセスを停止しています...${NC}"
pkill -9 -f "python.*run.py" 2>/dev/null
pkill -9 -f "puppeteer" 2>/dev/null
pkill -9 -f "phantomjs" 2>/dev/null
pkill -9 -f "chrome" 2>/dev/null
echo -e "${GREEN}PySpiderプロセスを停止しました${NC}"

# systemdサービスの削除
echo -e "${YELLOW}systemdサービスを削除しています...${NC}"
if [ -f "/etc/systemd/system/pyspider.service" ]; then
    sudo systemctl stop pyspider 2>/dev/null
    sudo systemctl disable pyspider 2>/dev/null
    sudo rm /etc/systemd/system/pyspider.service
    sudo systemctl daemon-reload
    echo -e "${GREEN}systemdサービスを削除しました${NC}"
else
    echo -e "${YELLOW}systemdサービスは存在しません${NC}"
fi

# logrotateの設定を削除
echo -e "${YELLOW}logrotate設定を削除しています...${NC}"
if [ -f "/etc/logrotate.d/pyspider" ]; then
    sudo rm /etc/logrotate.d/pyspider
    echo -e "${GREEN}logrotate設定を削除しました${NC}"
else
    echo -e "${YELLOW}logrotate設定は存在しません${NC}"
fi

# cronジョブの削除
echo -e "${YELLOW}cronジョブを削除しています...${NC}"
CURRENT_CRONTAB=$(crontab -l 2>/dev/null || echo "")
if echo "$CURRENT_CRONTAB" | grep -q "pyspiderNx"; then
    echo "$CURRENT_CRONTAB" | grep -v "pyspiderNx" > /tmp/crontab.tmp
    crontab /tmp/crontab.tmp
    rm /tmp/crontab.tmp
    echo -e "${GREEN}cronジョブを削除しました${NC}"
else
    echo -e "${YELLOW}cronジョブは存在しません${NC}"
fi

# 設定ファイルの復元
echo -e "${YELLOW}設定ファイルを復元しています...${NC}"

# config.jsonの復元
cat > /home/igtmtakan/workplace/python/pyspiderNx/config.json << 'EOF'
{
    "phantomjs": {
        "args": ["--ignore-ssl-errors=true"]
    },
    "message_queue": "redis://localhost:6379/0",
    "webui": {
        "port": 5000
    }
}
EOF
echo -e "${GREEN}config.jsonを復元しました${NC}"

# puppeteer_fetcher.jsのポート設定を復元
sed -i 's/const port = process.env.PUPPETEER_FETCHER_PORT || 22224;/const port = process.env.PUPPETEER_FETCHER_PORT || 22222;/' /home/igtmtakan/workplace/python/pyspiderNx/pyspider/fetcher/puppeteer_fetcher.js
sed -i "s/waitUntil: 'domcontentloaded',  \/\/ 'networkidle2'から変更して高速化/waitUntil: 'networkidle2',/" /home/igtmtakan/workplace/python/pyspiderNx/pyspider/fetcher/puppeteer_fetcher.js
sed -i "s/timeout: task.request_timeout || 30000  \/\/ デフォルトタイムアウトを30秒に短縮/timeout: timeout/" /home/igtmtakan/workplace/python/pyspiderNx/pyspider/fetcher/puppeteer_fetcher.js
echo -e "${GREEN}puppeteer_fetcher.jsを復元しました${NC}"

# 追加したモジュールの削除
echo -e "${YELLOW}追加したモジュールを削除しています...${NC}"
if [ -f "/home/igtmtakan/workplace/python/pyspiderNx/pyspider/webui/metrics.py" ]; then
    rm /home/igtmtakan/workplace/python/pyspiderNx/pyspider/webui/metrics.py
    echo -e "${GREEN}metrics.pyを削除しました${NC}"
fi

if [ -f "/home/igtmtakan/workplace/python/pyspiderNx/pyspider/webui/security.py" ]; then
    rm /home/igtmtakan/workplace/python/pyspiderNx/pyspider/webui/security.py
    echo -e "${GREEN}security.pyを削除しました${NC}"
fi

# webui/__init__.pyの復元
cat > /home/igtmtakan/workplace/python/pyspiderNx/pyspider/webui/__init__.py << 'EOF'
#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-22 23:20:40

from . import app, index, debug, task, result, login, products, selector_tester, api
EOF
echo -e "${GREEN}webui/__init__.pyを復元しました${NC}"

# 追加したスクリプトの削除
echo -e "${YELLOW}追加したスクリプトを削除しています...${NC}"
rm -f /home/igtmtakan/workplace/python/pyspiderNx/install_service.sh
rm -f /home/igtmtakan/workplace/python/pyspiderNx/install_logrotate.sh
rm -f /home/igtmtakan/workplace/python/pyspiderNx/install_cron_jobs.sh
rm -f /home/igtmtakan/workplace/python/pyspiderNx/backup_and_optimize_db.sh
rm -f /home/igtmtakan/workplace/python/pyspiderNx/monitor_queues.py
rm -f /home/igtmtakan/workplace/python/pyspiderNx/pyspider.service
rm -f /home/igtmtakan/workplace/python/pyspiderNx/pyspider-logrotate
rm -f /home/igtmtakan/workplace/python/pyspiderNx/install_all.sh
echo -e "${GREEN}追加したスクリプトを削除しました${NC}"

# サンプルプロジェクトの削除
echo -e "${YELLOW}追加したサンプルプロジェクトを削除しています...${NC}"
if [ -f "/home/igtmtakan/workplace/python/pyspiderNx/pyspider/sample_projects/robust_error_handling.py" ]; then
    rm /home/igtmtakan/workplace/python/pyspiderNx/pyspider/sample_projects/robust_error_handling.py
    echo -e "${GREEN}robust_error_handling.pyを削除しました${NC}"
fi

echo -e "${GREEN}PySpider 安定化機能のアンインストールが完了しました${NC}"
echo "=================================="
echo -e "${YELLOW}以下のコマンドでPySpiderを起動できます:${NC}"
echo "cd /home/igtmtakan/workplace/python/pyspiderNx && bash start_pyspider.sh"
echo "=================================="
