# 🛠️ 로컬 개발 서버 실행 가이드

Docker 없이 로컬에서 Kiko 개발 서버를 실행하는 방법입니다.

## 🚀 1단계: 원클릭 실행 (권장)

```bash
# 모든 권한 설정 및 서버 시작
chmod +x start-dev.sh && ./start-dev.sh
```

이 스크립트는:

- 필수 도구 확인 (Python3, Node.js)
- 백엔드 가상환경 설정
- 의존성 자동 설치
- 백엔드와 프론트엔드 동시 실행

## 🔧 2단계: 개별 서비스 실행

### 백엔드만 실행

```bash
cd backend
chmod +x start-backend.sh
./start-backend.sh
```

### 프론트엔드만 실행

```bash
cd frontend
chmod +x start-frontend.sh
./start-frontend.sh
```

## ⚙️ 3단계: 수동 실행 (고급 사용자)

### 백엔드 (FastAPI)

```bash
cd backend

# 1. 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경변수 설정 확인
ls -la .env

# 4. 서버 시작
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 프론트엔드 (SvelteKit)

```bash
cd frontend

# 1. 의존성 설치
yarn install  # 또는 npm install

# 2. 환경변수 설정 확인
ls -la .env.local

# 3. 개발 서버 시작
yarn dev  # 또는 npm run dev
```

## 📋 사전 요구사항

### 필수 소프트웨어

- **Python 3.11+**

  ```bash
  # macOS
  brew install python3

  # Ubuntu/Debian
  sudo apt install python3 python3-pip python3-venv
  ```

- **Node.js 18+**

  ```bash
  # macOS
  brew install node

  # Ubuntu/Debian
  curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
  sudo apt-get install -y nodejs
  ```

- **Yarn (선택사항)**
  ```bash
  npm install -g yarn
  ```

### 환경변수 설정

1. **백엔드**: `backend/.env` 파일 확인
2. **프론트엔드**: `frontend/.env.local` 파일 확인

환경변수가 없는 경우 example 파일들을 복사:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

## 🌐 접속 주소

| 서비스     | URL                        | 포트 |
| ---------- | -------------------------- | ---- |
| 프론트엔드 | http://localhost:5173      | 5173 |
| 백엔드 API | http://localhost:8000      | 8000 |
| API 문서   | http://localhost:8000/docs | 8000 |

## 🔍 문제 해결

### 포트 충돌

```bash
# 사용 중인 포트 확인
lsof -i :8000
lsof -i :5173

# 프로세스 종료
kill -9 <PID>
```

### Python 가상환경 오류

```bash
# 가상환경 삭제 후 재생성
rm -rf backend/venv
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Node.js 의존성 오류

```bash
# 캐시 클리어 후 재설치
cd frontend
rm -rf node_modules yarn.lock package-lock.json
yarn install  # 또는 npm install
```

## 💡 팁

1. **개발 중단/재시작**: `Ctrl+C`로 서버 종료 후 스크립트 재실행
2. **로그 확인**: 각 터미널에서 에러 메시지 확인
3. **환경변수 변경**: `.env` 파일 수정 후 서버 재시작
4. **포트 변경**: 필요시 스크립트 내 포트 번호 수정

## 🚀 다음 단계

로컬 개발 환경이 성공적으로 실행되면:

1. API 문서 (http://localhost:8000/docs) 확인
2. 프론트엔드 (http://localhost:5173) 접속 테스트
3. 데이터베이스 연결 상태 확인
4. 첫 번째 기능 개발 시작!
