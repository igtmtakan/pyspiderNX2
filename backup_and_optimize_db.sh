#!/bin/bash

# 色の定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}PySpider データベースのバックアップと最適化${NC}"
echo "=================================="

# バックアップディレクトリ
BACKUP_DIR="/home/igtmtakan/workplace/python/pyspiderNx/backups"
mkdir -p $BACKUP_DIR

# 日付スタンプ
DATE=$(date +%Y%m%d)

# PySpiderが実行中かチェック
if systemctl is-active --quiet pyspider; then
    echo -e "${YELLOW}PySpiderを停止しています...${NC}"
    sudo systemctl stop pyspider
    PYSPIDER_WAS_RUNNING=true
else
    PYSPIDER_WAS_RUNNING=false
fi

# データベースのバックアップ
echo -e "${YELLOW}データベースをバックアップしています...${NC}"
mkdir -p $BACKUP_DIR/$DATE
cp /home/igtmtakan/workplace/python/pyspiderNx/data/*.db $BACKUP_DIR/$DATE/
if [ $? -ne 0 ]; then
    echo -e "${RED}データベースのバックアップに失敗しました。${NC}"
    # PySpiderを再起動
    if [ "$PYSPIDER_WAS_RUNNING" = true ]; then
        echo -e "${YELLOW}PySpiderを再起動しています...${NC}"
        sudo systemctl start pyspider
    fi
    exit 1
fi

# SQLiteデータベースの最適化
echo -e "${YELLOW}データベースを最適化しています...${NC}"
for db in /home/igtmtakan/workplace/python/pyspiderNx/data/*.db; do
  echo "Optimizing $db..."
  sqlite3 $db "VACUUM;"
  if [ $? -ne 0 ]; then
      echo -e "${RED}データベース $db の最適化に失敗しました。${NC}"
  fi
done

# 古いバックアップを削除（30日以上前のもの）
echo -e "${YELLOW}古いバックアップを削除しています...${NC}"
find $BACKUP_DIR -type d -name "20*" -mtime +30 -exec rm -rf {} \;

# PySpiderを再起動
if [ "$PYSPIDER_WAS_RUNNING" = true ]; then
    echo -e "${YELLOW}PySpiderを再起動しています...${NC}"
    sudo systemctl start pyspider
fi

echo -e "${GREEN}データベースのバックアップと最適化が完了しました${NC}"
echo "=================================="
echo -e "${YELLOW}バックアップは以下のディレクトリに保存されました:${NC}"
echo "$BACKUP_DIR/$DATE"
echo "=================================="
