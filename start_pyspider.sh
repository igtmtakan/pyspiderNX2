#!/bin/bash

# OpenSSL設定を環境変数に設定
export OPENSSL_CONF=/dev/null

# 色の定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}PySpider起動スクリプト${NC}"
echo "=================================="

# 既存のプロセスを終了
echo -e "${YELLOW}既存のプロセスを終了しています...${NC}"
pkill -9 -f "python.*run.py" 2>/dev/null
pkill -9 -f "node.*puppeteer_fetcher.js" 2>/dev/null
pkill -9 -f "phantomjs" 2>/dev/null
echo -e "${GREEN}既存のプロセスを終了しました${NC}"

# Puppeteer Fetcherを起動
echo -e "${YELLOW}Puppeteer Fetcherを起動しています...${NC}"
./start_puppeteer_fetcher.sh &
PUPPETEER_PID=$!

# Puppeteer Fetcherの起動を待つ
sleep 5
echo -e "${GREEN}Puppeteer Fetcherを起動しました${NC}"

# PySpiderを起動
echo -e "${YELLOW}PySpiderを起動しています...${NC}"
python -u ./run.py -c config.json &
PYSPIDER_PID=$!

# 起動完了メッセージ
echo -e "${GREEN}PySpiderを起動しました${NC}"
echo "=================================="
echo -e "${GREEN}WebUI: http://localhost:5000${NC}"
echo -e "${YELLOW}終了するには Ctrl+C を押してください${NC}"

# シグナルハンドラの設定
trap 'echo -e "${RED}終了しています...${NC}"; kill $PUPPETEER_PID $PYSPIDER_PID 2>/dev/null; exit 0' INT TERM

# プロセスが終了するまで待機
wait $PYSPIDER_PID
