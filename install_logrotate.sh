#!/bin/bash

# 色の定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}PySpider logrotate設定のインストール${NC}"
echo "=================================="

# logrotate設定ファイルをコピー
echo -e "${YELLOW}logrotate設定ファイルをコピーしています...${NC}"
sudo cp pyspider-logrotate /etc/logrotate.d/pyspider
if [ $? -ne 0 ]; then
    echo -e "${RED}logrotate設定ファイルのコピーに失敗しました。sudo権限を確認してください。${NC}"
    exit 1
fi

# 権限を設定
echo -e "${YELLOW}権限を設定しています...${NC}"
sudo chmod 644 /etc/logrotate.d/pyspider
if [ $? -ne 0 ]; then
    echo -e "${RED}権限の設定に失敗しました。${NC}"
    exit 1
fi

echo -e "${GREEN}PySpider logrotate設定のインストールが完了しました${NC}"
echo "=================================="
echo -e "${YELLOW}以下のコマンドでlogrotateの設定をテストできます:${NC}"
echo "sudo logrotate -d /etc/logrotate.d/pyspider # デバッグモードでテスト"
echo "sudo logrotate -f /etc/logrotate.d/pyspider # 強制的に実行"
echo "=================================="
