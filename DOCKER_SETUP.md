# Docker 설치 및 문제 해결 가이드

## 🐳 Docker Desktop 설치 방법

### macOS

1. **공식 사이트에서 다운로드**

   ```bash
   # 브라우저에서 방문
   https://www.docker.com/products/docker-desktop/
   ```

2. **Homebrew 사용 (권장)**

   ```bash
   # Homebrew 설치 (미설치 시)
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

   # Docker Desktop 설치
   brew install --cask docker
   ```

3. **설치 후 실행**
   - Applications 폴더에서 Docker Desktop 실행
   - 시스템 상단 메뉴바에서 Docker 아이콘 확인
   - 터미널에서 `docker --version` 명령어로 확인

### Windows

1. **WSL2 활성화** (Windows 10/11)

   ```powershell
   # PowerShell 관리자 권한으로 실행
   wsl --install
   ```

2. **Docker Desktop 설치**
   - https://www.docker.com/products/docker-desktop/ 에서 다운로드
   - 설치 프로그램 실행
   - "Use WSL 2 instead of Hyper-V" 옵션 선택

### Linux (Ubuntu)

```bash
# 기존 Docker 제거
sudo apt-get remove docker docker-engine docker.io containerd runc

# 의존성 설치
sudo apt-get update
sudo apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Docker 공식 GPG 키 추가
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Docker 저장소 추가
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker 설치
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER
```

## 🚀 Docker Compose 실행 방법

### 1. 개발 환경 (권장)

```bash
# 개발용 Docker Compose 실행
docker-compose -f docker-compose.dev.yml up --build

# 백그라운드 실행
docker-compose -f docker-compose.dev.yml up -d --build

# 서비스별 로그 확인
docker-compose -f docker-compose.dev.yml logs backend-dev
docker-compose -f docker-compose.dev.yml logs frontend-dev

# 종료
docker-compose -f docker-compose.dev.yml down
```

### 2. 프로덕션 환경

```bash
# 프로덕션용 Docker Compose 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d --build

# 종료
docker-compose down
```

### 3. 서비스 포트

| 서비스        | 개발 환경 | 프로덕션 환경 | 설명         |
| ------------- | --------- | ------------- | ------------ |
| Frontend      | 5173      | 3000          | SvelteKit 앱 |
| Backend       | 8000      | 8000          | FastAPI API  |
| PostgreSQL    | 5432      | -             | 개발 DB      |
| Redis         | 6379      | 6379          | 캐시         |
| Adminer       | 8080      | -             | DB 관리      |
| Redis Insight | 8001      | -             | Redis 관리   |

## 🔧 문제 해결

### Docker Desktop이 시작되지 않는 경우

1. **macOS**

   ```bash
   # Docker Desktop 강제 종료 후 재시작
   killall Docker\ Desktop
   open -a Docker\ Desktop

   # 시스템 재부팅 후 재시도
   sudo reboot
   ```

2. **Windows**

   - WSL2 업데이트: `wsl --update`
   - Hyper-V 설정 확인
   - 바이러스 백신 소프트웨어 예외 추가

3. **Linux**

   ```bash
   # Docker 서비스 시작
   sudo systemctl start docker
   sudo systemctl enable docker

   # 사용자 권한 확인
   groups $USER | grep docker
   ```

### Docker Compose 빌드 오류

1. **캐시 클리어**

   ```bash
   # Docker 캐시 완전 삭제
   docker system prune -a --volumes

   # 특정 이미지 삭제
   docker rmi $(docker images -q)
   ```

2. **개별 서비스 빌드**

   ```bash
   # 백엔드만 빌드
   docker-compose build backend-dev

   # 프론트엔드만 빌드
   docker-compose build frontend-dev
   ```

3. **로그 확인**
   ```bash
   # 실시간 로그 확인
   docker-compose logs -f backend-dev
   docker-compose logs -f frontend-dev
   ```

### 포트 충돌 오류

```bash
# 사용 중인 포트 확인
lsof -i :8000  # 백엔드 포트
lsof -i :5173  # 프론트엔드 포트
lsof -i :5432  # PostgreSQL 포트

# 프로세스 종료
kill -9 <PID>
```

### 권한 오류 (Linux/macOS)

```bash
# Docker 소켓 권한 설정
sudo chown $USER:docker /var/run/docker.sock

# 파일 권한 확인
ls -la docker-compose*.yml
chmod +x start-dev.sh
```

## 🐋 Docker 없이 개발하기

Docker 설치가 어려운 경우, 로컬에서 직접 실행:

```bash
# 개발 스크립트 실행 권한 부여
chmod +x start-dev.sh

# 개발 서버 시작
./start-dev.sh
```

### 필수 요구사항

- **Python 3.11+**
- **Node.js 18+**
- **Yarn** (또는 npm)

### 수동 실행

1. **백엔드**

   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. **프론트엔드**
   ```bash
   cd frontend
   yarn install  # 또는 npm install
   yarn dev      # 또는 npm run dev
   ```

## 📞 추가 지원

문제가 계속 발생하는 경우:

1. **시스템 요구사항 확인**

   - RAM: 최소 4GB (권장 8GB+)
   - 디스크: 최소 10GB 여유 공간
   - OS: macOS 10.15+, Windows 10/11, Ubuntu 18.04+

2. **공식 문서 참조**

   - [Docker Desktop 문서](https://docs.docker.com/desktop/)
   - [Docker Compose 문서](https://docs.docker.com/compose/)

3. **커뮤니티 지원**
   - [Docker 공식 포럼](https://forums.docker.com/)
   - [Stack Overflow](https://stackoverflow.com/questions/tagged/docker)
