# 🚀 Kiko 배포 가이드

이 문서는 Kiko 프로젝트의 배포 및 운영 방법을 안내합니다.

## 📋 배포 환경별 가이드

### 🔧 개발 환경 (Development)

#### 로컬 개발 환경 설정

```bash
# 1. 저장소 클론
git clone https://github.com/your-org/kiko-vooster.git
cd kiko-vooster

# 2. 환경 변수 설정
cp .env.example .env.development
# .env.development 파일을 편집하여 필요한 값들을 설정

# 3. Docker Compose로 전체 스택 실행
docker-compose -f docker-compose.dev.yml up -d

# 또는 개별 실행
# Frontend (터미널 1)
cd frontend && yarn install && yarn dev

# Backend (터미널 2)  
cd backend && source venv/bin/activate && python -m app.main
```

#### 접속 주소
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **Adminer (DB 관리)**: http://localhost:8080
- **Redis Insight**: http://localhost:8001

### 🌐 스테이징 환경 (Staging)

#### Vercel + Fly.io 배포

**Frontend (Vercel)**
```bash
# 1. Vercel CLI 설치 및 로그인
npm i -g vercel
vercel login

# 2. 프로젝트 배포
cd frontend
vercel --prod

# 3. 환경 변수 설정 (Vercel 대시보드에서)
# - PUBLIC_API_URL: https://your-api.fly.dev
# - NODE_ENV: production
```

**Backend (Fly.io)**
```bash
# 1. Fly CLI 설치 및 로그인
curl -L https://fly.io/install.sh | sh
flyctl auth login

# 2. 앱 생성 및 배포
cd backend
flyctl launch --name kiko-api-staging
flyctl deploy

# 3. 환경 변수 설정
flyctl secrets set SUPABASE_URL="your-supabase-url"
flyctl secrets set SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
flyctl secrets set JWT_SECRET_KEY="your-jwt-secret"
```

### 🏭 프로덕션 환경 (Production)

#### Docker Compose 배포

```bash
# 1. 프로덕션 서버에 코드 배포
git clone https://github.com/your-org/kiko-vooster.git
cd kiko-vooster

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 프로덕션 값들을 설정

# 3. SSL 인증서 설정 (Let's Encrypt)
./infrastructure/scripts/setup-ssl.sh your-domain.com

# 4. 프로덕션 배포
docker-compose --profile production up -d

# 5. 로그 확인
docker-compose logs -f
```

## 🔐 환경 변수 설정

### 필수 환경 변수

```bash
# Supabase 설정
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# JWT 설정
JWT_SECRET_KEY=your-super-secret-jwt-key-32-chars-minimum

# OAuth 설정 (선택사항)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# 환경 설정
ENVIRONMENT=production
DEBUG=false
```

### 환경 변수 보안 관리

- **개발 환경**: `.env.development` (Git 추적 안함)
- **스테이징**: Vercel/Fly.io 환경 변수 설정
- **프로덕션**: Docker secrets 또는 서버 환경 변수

## 📊 모니터링 및 로깅

### 헬스 체크 엔드포인트

```bash
# Backend 헬스 체크
curl http://your-api-url/health

# 응답 예시
{
  "status": "healthy",
  "environment": "production",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 로그 확인

```bash
# Docker Compose 로그
docker-compose logs -f [service-name]

# Fly.io 로그
flyctl logs -a kiko-api-staging

# Vercel 로그 (대시보드에서 확인)
```

## 🔄 CI/CD 파이프라인

### GitHub Actions 설정

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Fly.io
        uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --remote-only
```

## 🗄️ 데이터베이스 관리

### Supabase 마이그레이션

```bash
# 1. Supabase CLI 설치
npm install supabase --save-dev

# 2. 로그인 및 프로젝트 연결
npx supabase login
npx supabase link --project-ref your-project-ref

# 3. 마이그레이션 생성
npx supabase migration new create_users_table

# 4. 마이그레이션 적용
npx supabase db push
```

### 백업 및 복구

```bash
# 데이터 백업 (Supabase 대시보드에서)
# 1. Database → Backups → Create backup

# 수동 백업
pg_dump "postgresql://user:pass@host:port/dbname" > backup.sql

# 복구
psql "postgresql://user:pass@host:port/dbname" < backup.sql
```

## 🚨 트러블슈팅

### 자주 발생하는 문제들

#### 1. CORS 오류
```bash
# Backend 설정 확인
CORS_ORIGINS=https://your-frontend-url.com,https://localhost:3000
```

#### 2. JWT 토큰 만료
```bash
# 토큰 만료 시간 조정
JWT_EXPIRE_MINUTES=60  # 기본 30분
```

#### 3. Supabase 연결 실패
```bash
# URL 및 키 확인
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_ROLE_KEY
```

#### 4. Docker 메모리 부족
```bash
# 메모리 사용량 확인
docker stats

# 불필요한 컨테이너 정리
docker system prune -a
```

### 성능 최적화

#### Frontend 최적화
```bash
# 빌드 최적화
yarn build --optimize

# Lighthouse 성능 검사
npx lighthouse https://your-site.com
```

#### Backend 최적화
```bash
# Uvicorn workers 조정
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000

# 메모리 사용량 모니터링
ps aux | grep uvicorn
```

## 📞 지원 및 문의

- **GitHub Issues**: https://github.com/your-org/kiko-vooster/issues
- **Slack**: #kiko-dev-support
- **문서**: https://docs.kiko-app.com

---

**⚠️ 중요**: 프로덕션 배포 전에 반드시 스테이징 환경에서 충분한 테스트를 수행하세요. 