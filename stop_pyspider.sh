#!/bin/bash

# OpenSSL設定を環境変数に設定
export OPENSSL_CONF=/dev/null

# 色の定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}PySpider停止スクリプト${NC}"
echo "=================================="

# プロセスを終了
echo -e "${YELLOW}PySpiderを停止しています...${NC}"
pkill -9 -f "python.*run.py" 2>/dev/null
echo -e "${GREEN}PySpiderを停止しました${NC}"

echo -e "${YELLOW}Puppeteer Fetcherを停止しています...${NC}"
pkill -9 -f "node.*puppeteer_fetcher.js" 2>/dev/null
echo -e "${GREEN}Puppeteer Fetcherを停止しました${NC}"

echo -e "${YELLOW}PhantomJSを停止しています...${NC}"
pkill -9 -f "phantomjs" 2>/dev/null
echo -e "${GREEN}PhantomJSを停止しました${NC}"

echo "=================================="
echo -e "${GREEN}すべてのプロセスを停止しました${NC}"
