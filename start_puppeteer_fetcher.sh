#!/bin/bash
# Start Puppeteer Fetcher

# Set environment variables
export PUPPETEER_FETCHER_PORT=22223
export NODE_ENV=production
# Skip Chromium download if already installed
export PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
# Disable sandbox for Docker environments
export PUPPETEER_NO_SANDBOX=true

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if puppeteer_fetcher.js exists
if [ ! -f "pyspider/fetcher/puppeteer_fetcher.js" ]; then
    echo "puppeteer_fetcher.js not found."
    exit 1
fi

# Check if required Node.js packages are installed
cd pyspider
if [ ! -d "node_modules/puppeteer" ] || [ ! -d "node_modules/express" ] || [ ! -d "node_modules/body-parser" ]; then
    echo "Installing required Node.js packages..."
    npm install
fi

# Kill any existing Puppeteer Fetcher processes
echo "Checking for existing Puppeteer Fetcher processes..."
PUPPETEER_PID=$(lsof -i:$PUPPETEER_FETCHER_PORT -t 2>/dev/null)
if [ ! -z "$PUPPETEER_PID" ]; then
    echo "Killing existing Puppeteer Fetcher process (PID: $PUPPETEER_PID)..."
    kill -9 $PUPPETEER_PID 2>/dev/null
fi

# Start Puppeteer Fetcher
echo "Starting Puppeteer Fetcher on port $PUPPETEER_FETCHER_PORT..."
node fetcher/puppeteer_fetcher.js &
