#!/bin/bash

# 色の定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}PySpider cronジョブのインストール${NC}"
echo "=================================="

# 現在のcrontabを取得
CURRENT_CRONTAB=$(crontab -l 2>/dev/null || echo "")

# データベースバックアップのcronジョブを追加
echo -e "${YELLOW}データベースバックアップのcronジョブを追加しています...${NC}"
DB_BACKUP_JOB="0 2 * * * /home/igtmtakan/workplace/python/pyspiderNx/backup_and_optimize_db.sh >> /home/igtmtakan/workplace/python/pyspiderNx/logs/db_backup.log 2>&1"

# 既に存在するか確認
if echo "$CURRENT_CRONTAB" | grep -q "backup_and_optimize_db.sh"; then
    echo -e "${YELLOW}データベースバックアップのcronジョブは既に存在します。${NC}"
else
    # cronジョブを追加
    echo "$CURRENT_CRONTAB" > /tmp/crontab.tmp
    echo "$DB_BACKUP_JOB" >> /tmp/crontab.tmp
    crontab /tmp/crontab.tmp
    rm /tmp/crontab.tmp
    echo -e "${GREEN}データベースバックアップのcronジョブを追加しました。${NC}"
fi

# PySpider再起動のcronジョブを追加
echo -e "${YELLOW}PySpider再起動のcronジョブを追加しています...${NC}"
RESTART_JOB="0 3 * * * sudo systemctl restart pyspider >> /home/igtmtakan/workplace/python/pyspiderNx/logs/restart.log 2>&1"

# 既に存在するか確認
if echo "$CURRENT_CRONTAB" | grep -q "systemctl restart pyspider"; then
    echo -e "${YELLOW}PySpider再起動のcronジョブは既に存在します。${NC}"
else
    # cronジョブを追加
    CURRENT_CRONTAB=$(crontab -l 2>/dev/null || echo "")
    echo "$CURRENT_CRONTAB" > /tmp/crontab.tmp
    echo "$RESTART_JOB" >> /tmp/crontab.tmp
    crontab /tmp/crontab.tmp
    rm /tmp/crontab.tmp
    echo -e "${GREEN}PySpider再起動のcronジョブを追加しました。${NC}"
fi

# キュー監視のcronジョブを追加
echo -e "${YELLOW}キュー監視のcronジョブを追加しています...${NC}"
MONITOR_JOB="*/10 * * * * /home/igtmtakan/workplace/python/pyspiderNx/monitor_queues.py >> /home/igtmtakan/workplace/python/pyspiderNx/logs/queue_monitor.log 2>&1"

# 既に存在するか確認
if echo "$CURRENT_CRONTAB" | grep -q "monitor_queues.py"; then
    echo -e "${YELLOW}キュー監視のcronジョブは既に存在します。${NC}"
else
    # cronジョブを追加
    CURRENT_CRONTAB=$(crontab -l 2>/dev/null || echo "")
    echo "$CURRENT_CRONTAB" > /tmp/crontab.tmp
    echo "$MONITOR_JOB" >> /tmp/crontab.tmp
    crontab /tmp/crontab.tmp
    rm /tmp/crontab.tmp
    echo -e "${GREEN}キュー監視のcronジョブを追加しました。${NC}"
fi

echo -e "${GREEN}PySpider cronジョブのインストールが完了しました${NC}"
echo "=================================="
echo -e "${YELLOW}以下のコマンドでcronジョブを確認できます:${NC}"
echo "crontab -l"
echo "=================================="
