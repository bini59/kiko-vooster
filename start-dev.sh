#!/bin/bash

# Kiko 개발 서버 실행 스크립트
# Docker 없이 로컬에서 백엔드와 프론트엔드를 실행합니다.

echo "🚀 Kiko 개발 서버를 시작합니다..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 함수 정의
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1이 설치되어 있지 않습니다.${NC}"
        echo -e "${YELLOW}💡 설치 방법:${NC}"
        case $1 in
            python3)
                echo "   macOS: brew install python3"
                echo "   Ubuntu: sudo apt install python3 python3-pip"
                ;;
            node)
                echo "   macOS: brew install node"
                echo "   Ubuntu: sudo apt install nodejs npm"
                echo "   또는 https://nodejs.org/에서 다운로드"
                ;;
            yarn)
                echo "   npm install -g yarn"
                ;;
        esac
        return 1
    else
        echo -e "${GREEN}✅ $1 설치됨${NC}"
        return 0
    fi
}

# 필수 도구 확인
echo -e "${BLUE}📋 필수 도구 확인 중...${NC}"
check_command python3 || exit 1
check_command node || exit 1
check_command yarn || {
    echo -e "${YELLOW}⚠️  yarn이 없습니다. npm을 사용합니다.${NC}"
    USE_NPM=true
}

# 백엔드 설정
echo -e "\n${BLUE}🔧 백엔드 설정 중...${NC}"
cd backend

# Python 가상환경 생성 (존재하지 않는 경우)
if [ ! -d "venv" ]; then
    echo "가상환경 생성 중..."
    python3 -m venv venv
fi

# 가상환경 활성화
echo "가상환경 활성화 중..."
source venv/bin/activate

# 의존성 설치
echo "Python 의존성 설치 중..."
pip install -r requirements.txt

cd ..

# 프론트엔드 설정
echo -e "\n${BLUE}🔧 프론트엔드 설정 중...${NC}"
cd frontend

# Node.js 의존성 설치
if [ "$USE_NPM" = true ]; then
    echo "npm으로 의존성 설치 중..."
    npm install
else
    echo "yarn으로 의존성 설치 중..."
    yarn install
fi

cd ..

# 서버 실행
echo -e "\n${GREEN}🚀 서버를 시작합니다...${NC}"
echo -e "${YELLOW}📝 사용법:${NC}"
echo "   - 백엔드: http://localhost:8000"
echo "   - 프론트엔드: http://localhost:5173"
echo "   - API 문서: http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}⚠️  종료하려면 Ctrl+C를 두 번 눌러주세요.${NC}"

# 백그라운드에서 백엔드 실행
echo -e "\n${BLUE}🔥 백엔드 서버 시작...${NC}"
cd backend
source venv/bin/activate
export $(cat .env | xargs) 2>/dev/null || true
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# 잠시 대기 (백엔드가 시작될 시간)
sleep 3

# 프론트엔드 실행
echo -e "\n${BLUE}⚡ 프론트엔드 서버 시작...${NC}"
cd frontend
if [ "$USE_NPM" = true ]; then
    npm run dev
else
    yarn dev
fi

# 정리 함수
cleanup() {
    echo -e "\n${YELLOW}🔄 서버를 종료합니다...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    echo -e "${GREEN}✅ 정리 완료${NC}"
    exit 0
}

# 시그널 핸들러 등록
trap cleanup SIGINT SIGTERM

# 프론트엔드가 종료되면 백엔드도 종료
wait
cleanup 