#!/bin/bash

# Kiko 백엔드 서버 실행 스크립트

echo "🔥 Kiko 백엔드 서버를 시작합니다..."

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Python 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3이 설치되어 있지 않습니다."
    echo "설치 방법: brew install python3 (macOS) 또는 https://python.org"
    exit 1
fi

# 가상환경 생성 및 활성화
if [ ! -d "venv" ]; then
    echo -e "${BLUE}📦 Python 가상환경 생성 중...${NC}"
    python3 -m venv venv
fi

echo -e "${BLUE}🔧 가상환경 활성화 중...${NC}"
source venv/bin/activate

# 의존성 설치
echo -e "${BLUE}📥 의존성 설치 중...${NC}"
pip install -r requirements.txt

# 환경변수 로드
if [ -f ".env" ]; then
    echo -e "${BLUE}⚙️  환경변수 로드 중...${NC}"
    export $(cat .env | grep -v '^#' | xargs) 2>/dev/null || true
fi

# 서버 시작
echo -e "${GREEN}🚀 백엔드 서버 시작 (http://localhost:8000)${NC}"
echo -e "${YELLOW}📖 API 문서: http://localhost:8000/docs${NC}"
echo -e "${YELLOW}⚠️  종료하려면 Ctrl+C를 눌러주세요.${NC}"

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 