#!/bin/bash

# OpenSSL設定を環境変数に設定
export OPENSSL_CONF=/dev/null

# 色の定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}PySpider ローカルモード起動スクリプト${NC}"
echo "=================================="

# 既存のプロセスを終了
echo -e "${YELLOW}既存のプロセスを終了しています...${NC}"
pkill -9 -f "python.*run.py" 2>/dev/null
pkill -9 -f "python.*pyspider.run" 2>/dev/null
pkill -9 -f "node.*puppeteer_fetcher.js" 2>/dev/null

# ポート22222を使用しているプロセスを検索して終了
echo -e "${YELLOW}ポート22222を使用しているプロセスを確認中...${NC}"
PORT_PIDS=$(lsof -i :22222 -t 2>/dev/null)

if [ -n "$PORT_PIDS" ]; then
    echo -e "${YELLOW}ポート22222を使用しているプロセスを終了します: $PORT_PIDS${NC}"
    for PID in $PORT_PIDS; do
        echo -e "${YELLOW}プロセスID $PID を終了中...${NC}"
        kill -9 $PID 2>/dev/null
    done
    echo -e "${GREEN}ポート22222を使用していたプロセスを終了しました${NC}"
else
    echo -e "${GREEN}ポート22222を使用しているプロセスはありません${NC}"
fi

# XML-RPCポート（23333と24444）も確認
echo -e "${YELLOW}XML-RPCポート（23333と24444）を使用しているプロセスを確認中...${NC}"
XML_RPC_PIDS=$(lsof -i :23333,24444 -t 2>/dev/null)

if [ -n "$XML_RPC_PIDS" ]; then
    echo -e "${YELLOW}XML-RPCポートを使用しているプロセスを終了します: $XML_RPC_PIDS${NC}"
    for PID in $XML_RPC_PIDS; do
        echo -e "${YELLOW}プロセスID $PID を終了中...${NC}"
        kill -9 $PID 2>/dev/null
    done
    echo -e "${GREEN}XML-RPCポートを使用していたプロセスを終了しました${NC}"
else
    echo -e "${GREEN}XML-RPCポートを使用しているプロセスはありません${NC}"
fi

# WebUIポート（5000）も確認
echo -e "${YELLOW}WebUIポート（5000）を使用しているプロセスを確認中...${NC}"
WEBUI_PIDS=$(lsof -i :5000 -t 2>/dev/null)

if [ -n "$WEBUI_PIDS" ]; then
    echo -e "${YELLOW}WebUIポートを使用しているプロセスを終了します: $WEBUI_PIDS${NC}"
    for PID in $WEBUI_PIDS; do
        echo -e "${YELLOW}プロセスID $PID を終了中...${NC}"
        kill -9 $PID 2>/dev/null
    done
    echo -e "${GREEN}WebUIポートを使用していたプロセスを終了しました${NC}"
else
    echo -e "${GREEN}WebUIポートを使用しているプロセスはありません${NC}"
fi

# 少し待機してポートが解放されるのを確認
echo -e "${YELLOW}ポートが解放されるのを待機中...${NC}"
sleep 2

echo -e "${GREEN}既存のプロセスを終了しました${NC}"

# Puppeteer Fetcherを起動
echo -e "${YELLOW}Puppeteer Fetcherを起動しています...${NC}"
./start_puppeteer_fetcher.sh &
PUPPETEER_PID=$!

# Puppeteer Fetcherの起動を待つ
sleep 5
echo -e "${GREEN}Puppeteer Fetcherを起動しました${NC}"

# PySpiderをローカルモードで起動
echo -e "${YELLOW}PySpiderをローカルモードで起動しています...${NC}"
# Python 3.13対応のコマンド
python -m pyspider.run -c config.json one &
PYSPIDER_PID=$!

# 起動完了メッセージ
echo -e "${GREEN}PySpiderをローカルモードで起動しました${NC}"
echo "=================================="
echo -e "${GREEN}WebUI: http://localhost:5000${NC}"
echo -e "${YELLOW}終了するには Ctrl+C を押してください${NC}"

# シグナルハンドラの設定
trap 'echo -e "${RED}終了しています...${NC}"; kill $PUPPETEER_PID $PYSPIDER_PID 2>/dev/null; exit 0' INT TERM

# プロセスが終了するまで待機
wait $PYSPIDER_PID
