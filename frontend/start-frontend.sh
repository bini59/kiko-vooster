#!/bin/bash

# Kiko 프론트엔드 서버 실행 스크립트

echo "⚡ Kiko 프론트엔드 서버를 시작합니다..."

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Node.js 확인
if ! command -v node &> /dev/null; then
    echo "❌ Node.js가 설치되어 있지 않습니다."
    echo "설치 방법: brew install node (macOS) 또는 https://nodejs.org"
    exit 1
fi

# 패키지 매니저 확인
if command -v yarn &> /dev/null; then
    PACKAGE_MANAGER="yarn"
    INSTALL_CMD="yarn install"
    DEV_CMD="yarn dev"
elif command -v npm &> /dev/null; then
    PACKAGE_MANAGER="npm"
    INSTALL_CMD="npm install"
    DEV_CMD="npm run dev"
else
    echo "❌ npm 또는 yarn이 설치되어 있지 않습니다."
    echo "설치 방법: npm install -g yarn"
    exit 1
fi

echo -e "${BLUE}📦 $PACKAGE_MANAGER 사용${NC}"

# 의존성 설치
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}📥 의존성 설치 중...${NC}"
    $INSTALL_CMD
fi

# 환경변수 확인
if [ ! -f ".env.local" ]; then
    echo -e "${YELLOW}⚠️  .env.local 파일이 없습니다. .env.example을 복사하세요.${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env.local
        echo -e "${GREEN}✅ .env.local 파일을 생성했습니다.${NC}"
    fi
fi

# 서버 시작
echo -e "${GREEN}🚀 프론트엔드 서버 시작 (http://localhost:5173)${NC}"
echo -e "${YELLOW}🔗 백엔드 연결: http://localhost:8000${NC}"
echo -e "${YELLOW}⚠️  종료하려면 Ctrl+C를 눌러주세요.${NC}"

$DEV_CMD 