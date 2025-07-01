# 🔧 환경 변수 설정 가이드

이 문서는 Kiko 프로젝트의 환경 변수 설정 방법을 안내합니다.

## 📋 필수 환경 변수 목록

### 1. Supabase 설정
Supabase 대시보드에서 확인할 수 있는 설정값들입니다.

```bash
# Supabase 프로젝트 URL
SUPABASE_URL=https://your-project-id.supabase.co

# Supabase 익명 키 (공개용)
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Supabase 서비스 롤 키 (서버용, 비밀)
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2. JWT 설정
JWT 토큰 생성을 위한 시크릿 키입니다.

```bash
# JWT 시크릿 키 (랜덤 문자열, 32자 이상 권장)
JWT_SECRET_KEY=your-super-secret-jwt-key-here-should-be-long
```

### 3. OAuth 설정
소셜 로그인을 위한 OAuth 클라이언트 정보입니다.

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Apple OAuth (선택사항)
APPLE_CLIENT_ID=your.apple.client.id
APPLE_CLIENT_SECRET=your-apple-client-secret
```

### 4. 개발 환경 설정
개발 및 운영 환경 구분용 설정입니다.

```bash
# 환경 구분
NODE_ENV=development  # development | production | test
PYTHON_ENV=development

# API 엔드포인트
API_URL=http://localhost:8000        # 로컬 개발용
# API_URL=https://api.kiko.dev       # 프로덕션용

# 로그 레벨
LOG_LEVEL=debug  # debug | info | warn | error
```

## 🚀 환경별 설정 방법

### 개발 환경 (Local Development)

#### Frontend 환경 변수
`frontend/.env.local` 파일을 생성합니다:

```bash
# Supabase (공개용)
PUBLIC_SUPABASE_URL=https://your-project.supabase.co
PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key

# API 설정
PUBLIC_API_URL=http://localhost:8000

# OAuth (공개용)
PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com

# 개발 설정
NODE_ENV=development
VITE_LOG_LEVEL=debug
```

#### Backend 환경 변수
`backend/.env` 파일을 생성합니다:

```bash
# Supabase (서버용)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# JWT 설정
JWT_SECRET_KEY=your-super-secret-jwt-key-here-should-be-long
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# OAuth (비밀 키)
GOOGLE_CLIENT_SECRET=your-google-client-secret
APPLE_CLIENT_SECRET=your-apple-client-secret

# 데이터베이스
DATABASE_URL=postgresql://postgres:password@localhost:54321/postgres

# Redis (선택사항)
REDIS_URL=redis://localhost:6379

# 개발 설정
PYTHON_ENV=development
LOG_LEVEL=debug
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 프로덕션 환경

#### Vercel (Frontend)
Vercel 대시보드의 Environment Variables에서 설정:

```bash
PUBLIC_SUPABASE_URL=https://your-project.supabase.co
PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
PUBLIC_API_URL=https://api.your-domain.com
PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
NODE_ENV=production
```

#### Fly.io (Backend)
`fly.toml` 파일 또는 Fly.io 시크릿으로 관리:

```bash
# Fly.io 시크릿 설정 명령어
fly secrets set SUPABASE_URL=https://your-project.supabase.co
fly secrets set SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
fly secrets set JWT_SECRET_KEY=your-super-secret-jwt-key
fly secrets set GOOGLE_CLIENT_SECRET=your-google-client-secret
```

## 🔐 보안 가이드라인

### 1. 민감한 정보 관리
- ✅ **포함해도 되는 것** (PUBLIC_ 접두사)
  - API URL
  - Supabase URL
  - Supabase Anon Key
  - OAuth Client ID

- ❌ **절대 노출하면 안 되는 것**
  - Supabase Service Role Key
  - JWT Secret Key
  - OAuth Client Secret
  - 데이터베이스 비밀번호

### 2. 환경 변수 파일 관리
```bash
# 올바른 파일 권한 설정
chmod 600 .env
chmod 600 frontend/.env.local
chmod 600 backend/.env
```

### 3. Git 관리
```bash
# .gitignore에 포함된 항목들 (이미 설정됨)
.env
.env.local
.env.*.local
backend/.env
frontend/.env.local
```

## 🛠️ 설정 검증 방법

### Frontend 설정 확인
```bash
cd frontend
pnpm dev
# 브라우저 콘솔에서 확인
console.log(import.meta.env.PUBLIC_SUPABASE_URL)
```

### Backend 설정 확인
```python
# backend/app/core/config.py에서 확인
from app.core.config import settings
print(f"Supabase URL: {settings.SUPABASE_URL}")
print(f"JWT Secret configured: {'***' if settings.JWT_SECRET_KEY else 'NOT SET'}")
```

## 🚨 문제 해결

### 자주 발생하는 오류

#### 1. Supabase 연결 실패
```bash
# 원인: 잘못된 URL 또는 키
# 해결: Supabase 대시보드에서 정확한 값 복사
```

#### 2. CORS 오류
```bash
# 원인: Backend CORS 설정 누락
# 해결: backend/.env에 CORS_ORIGINS 추가
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

#### 3. JWT 토큰 오류
```bash
# 원인: JWT_SECRET_KEY 미설정 또는 너무 짧음
# 해결: 32자 이상의 랜덤 문자열 사용
JWT_SECRET_KEY=$(openssl rand -base64 32)
```

## 📚 추가 리소스

- [Supabase 환경 변수 가이드](https://supabase.com/docs/guides/getting-started/local-development)
- [SvelteKit 환경 변수](https://kit.svelte.dev/docs/modules#$env-static-public)
- [FastAPI 설정 관리](https://fastapi.tiangolo.com/advanced/settings/)
- [Vercel 환경 변수](https://vercel.com/docs/concepts/projects/environment-variables)
- [Fly.io 시크릿 관리](https://fly.io/docs/reference/secrets/)

---

⚠️ **주의사항**: 환경 변수 설정 후 서버를 재시작해야 변경사항이 적용됩니다. 