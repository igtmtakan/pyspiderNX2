#!/bin/bash

# 色の定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}PySpider 安定化機能のインストール${NC}"
echo "=================================="

# 必要なPythonパッケージをインストール
echo -e "${YELLOW}必要なPythonパッケージをインストールしています...${NC}"
pip install psutil redis

# systemdサービスのインストール
echo -e "${YELLOW}systemdサービスをインストールしています...${NC}"
bash install_service.sh

# logrotateの設定
echo -e "${YELLOW}logrotateの設定をインストールしています...${NC}"
bash install_logrotate.sh

# cronジョブの設定
echo -e "${YELLOW}cronジョブをインストールしています...${NC}"
bash install_cron_jobs.sh

# データベースのバックアップディレクトリを作成
echo -e "${YELLOW}データベースのバックアップディレクトリを作成しています...${NC}"
mkdir -p backups

# ログディレクトリを作成
echo -e "${YELLOW}ログディレクトリを作成しています...${NC}"
mkdir -p logs

# 権限を設定
echo -e "${YELLOW}権限を設定しています...${NC}"
chmod -R 755 *.sh
chmod -R 755 pyspider/sample_projects/*.py

echo -e "${GREEN}PySpider 安定化機能のインストールが完了しました${NC}"
echo "=================================="
echo -e "${YELLOW}以下のコマンドでPySpiderを起動できます:${NC}"
echo "sudo systemctl start pyspider"
echo "=================================="
echo -e "${YELLOW}以下のURLでメトリクスにアクセスできます:${NC}"
echo "http://localhost:5000/metrics"
echo "http://localhost:5000/metrics/health"
echo "=================================="
