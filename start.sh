#!/bin/bash
# WAN 2.2 Short Video Generator - 통합 실행 스크립트

set -e

cd "$(dirname "$0")"

# PID 파일 경로
PID_FILE=".server.pids"

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

cleanup() {
    echo ""
    echo -e "${YELLOW}서버 종료 중...${NC}"

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
    exit 0
}

# Ctrl+C 시그널 처리
trap cleanup SIGINT SIGTERM

echo "============================================"
echo -e "${GREEN}WAN 2.2 Short Video Generator${NC}"
echo "============================================"
echo ""

# 기존 프로세스 정리
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "python main.py --listen" 2>/dev/null || true
sleep 1

# PID 파일 초기화
> "$PID_FILE"

# 1. ComfyUI 시작
echo -e "${YELLOW}[1/2] ComfyUI 시작 중...${NC}"
cd comfyui
source venv/bin/activate
python main.py --listen --port 8188 > /tmp/comfyui.log 2>&1 &
COMFYUI_PID=$!
echo $COMFYUI_PID >> "../$PID_FILE"
cd ..

# ComfyUI가 준비될 때까지 대기
echo -n "ComfyUI 준비 대기 중"
for i in {1..30}; do
    if curl -s http://localhost:8188/system_stats > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}ComfyUI 준비 완료! (http://localhost:8188)${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

if ! curl -s http://localhost:8188/system_stats > /dev/null 2>&1; then
    echo ""
    echo -e "${RED}ComfyUI 시작 실패. 로그 확인: /tmp/comfyui.log${NC}"
    cleanup
fi

# 2. Backend 시작
echo ""
echo -e "${YELLOW}[2/2] FastAPI Backend 시작 중...${NC}"
cd backend
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID >> "../$PID_FILE"
cd ..

# Backend가 준비될 때까지 대기
echo -n "Backend 준비 대기 중"
for i in {1..15}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}Backend 준비 완료! (http://localhost:8000)${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

if ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo ""
    echo -e "${RED}Backend 시작 실패. 로그 확인: /tmp/backend.log${NC}"
    cleanup
fi

echo ""
echo "============================================"
echo -e "${GREEN}모든 서버가 시작되었습니다!${NC}"
echo "============================================"
echo ""
echo "  웹 UI:    http://localhost:8000"
echo "  ComfyUI:  http://localhost:8188"
echo ""
echo -e "${YELLOW}종료하려면 Ctrl+C 를 누르세요${NC}"
echo ""

# 서버 상태 모니터링
while true; do
    sleep 5

    # 프로세스 상태 확인
    if ! kill -0 $COMFYUI_PID 2>/dev/null; then
        echo -e "${RED}ComfyUI가 예기치 않게 종료되었습니다.${NC}"
        cleanup
    fi

    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}Backend가 예기치 않게 종료되었습니다.${NC}"
        cleanup
    fi
done
