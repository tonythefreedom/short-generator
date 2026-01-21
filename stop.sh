#!/bin/bash
# WAN 2.2 Short Video Generator - 서버 종료 스크립트

cd "$(dirname "$0")"

PID_FILE=".server.pids"

GREEN='\033[0;32m'
NC='\033[0m'

echo "서버 종료 중..."

if [ -f "$PID_FILE" ]; then
    while read pid; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            echo "프로세스 $pid 종료됨"
        fi
    done < "$PID_FILE"
    rm -f "$PID_FILE"
fi

# 남은 프로세스 정리
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "python main.py --listen" 2>/dev/null || true

echo -e "${GREEN}모든 서버가 종료되었습니다.${NC}"
