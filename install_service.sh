#!/bin/bash

# 色の定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}PySpider systemdサービスのインストール${NC}"
echo "=================================="

# サービスファイルをコピー
echo -e "${YELLOW}サービスファイルをコピーしています...${NC}"
sudo cp pyspider.service /etc/systemd/system/
if [ $? -ne 0 ]; then
    echo -e "${RED}サービスファイルのコピーに失敗しました。sudo権限を確認してください。${NC}"
    exit 1
fi

# systemdをリロード
echo -e "${YELLOW}systemdをリロードしています...${NC}"
sudo systemctl daemon-reload
if [ $? -ne 0 ]; then
    echo -e "${RED}systemdのリロードに失敗しました。${NC}"
    exit 1
fi

# サービスを有効化
echo -e "${YELLOW}サービスを有効化しています...${NC}"
sudo systemctl enable pyspider.service
if [ $? -ne 0 ]; then
    echo -e "${RED}サービスの有効化に失敗しました。${NC}"
    exit 1
fi

echo -e "${GREEN}PySpider systemdサービスのインストールが完了しました${NC}"
echo "=================================="
echo -e "${YELLOW}以下のコマンドでサービスを管理できます:${NC}"
echo "sudo systemctl start pyspider   # サービスを開始"
echo "sudo systemctl stop pyspider    # サービスを停止"
echo "sudo systemctl restart pyspider # サービスを再起動"
echo "sudo systemctl status pyspider  # サービスの状態を確認"
echo "=================================="
