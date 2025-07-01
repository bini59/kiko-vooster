# 🎌 Kiko - 일본어 라디오 학습 플랫폼

일본어 라디오 방송을 들으며 스크립트를 한 줄씩 따라 읽고, 단어장을 통해 어휘를 학습할 수 있는 웹 서비스입니다.

## 📋 프로젝트 개요

사용자는 좋아하는 일본어 라디오 콘텐츠로 학습 지속성을 높이고, 문장·단어 단위 상호작용으로 몰입형 학습 경험을 얻을 수 있습니다.

### 🎯 주요 기능
- 🎵 라디오 스트림/녹음 실시간 재생
- 📝 스크립트 싱크 (한 줄씩 하이라이트)
- 📚 개인 단어장 및 복습 모드
- 👤 소셜 로그인 및 학습 통계
- 🌙 다크모드 및 접근성 기능

## 🛠️ 기술 스택

### Frontend
- **Framework**: SvelteKit 1.x
- **Language**: TypeScript
- **Styling**: TailwindCSS + DaisyUI
- **Build**: Vite 4, pnpm
- **Testing**: Playwright (e2e)

### Backend
- **Language**: Python 3.11
- **Framework**: FastAPI 0.110 + Uvicorn
- **API**: RESTful + WebSocket
- **Validation**: Pydantic v2

### Database & Services
- **Database**: Supabase PostgreSQL 15
- **Auth**: Supabase Auth + Row-Level Security
- **Storage**: Supabase Storage
- **Real-time**: Supabase Realtime

### Infrastructure
- **Frontend Hosting**: Vercel
- **Backend Hosting**: Fly.io
- **CDN**: Cloudflare (HLS 오디오)
- **CI/CD**: GitHub Actions

## 🚀 개발 환경 설정

### 1. 필수 요구사항
- **Node.js**: 18.x 이상
- **Python**: 3.11 이상
- **pnpm**: 8.x 이상
- **Git**: 최신 버전

### 2. 저장소 클론 및 설정

```bash
# 저장소 클론
git clone [repository-url]
cd kiko-vooster

# 브랜치 설정 (main으로 변경)
git branch -m main
```

### 3. 환경 변수 설정

#### Frontend 환경 변수
```bash
# frontend/.env.local 파일 생성
cp frontend/.env.example frontend/.env.local
```

#### Backend 환경 변수
```bash
# backend/.env 파일 생성
cp backend/.env.example backend/.env
```

#### 필수 환경 변수
- `SUPABASE_URL`: Supabase 프로젝트 URL
- `SUPABASE_ANON_KEY`: Supabase 익명 키
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase 서비스 롤 키
- `JWT_SECRET_KEY`: JWT 토큰 시크릿
- `GOOGLE_CLIENT_ID`: Google OAuth 클라이언트 ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth 클라이언트 시크릿

### 4. 의존성 설치

#### Frontend
```bash
cd frontend
pnpm install
```

#### Backend
```bash
cd backend
pip install -r requirements.txt
# 또는 poetry 사용 시
poetry install
```

## 🏃‍♂️ 실행 방법

### 개발 서버 실행

#### Frontend 개발 서버
```bash
cd frontend
pnpm dev
# 접속: http://localhost:5173
```

#### Backend 개발 서버
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# 접속: http://localhost:8000
# API 문서: http://localhost:8000/docs
```

### 데이터베이스 설정

#### Supabase 마이그레이션
```bash
# Supabase CLI 설치
npm install -g supabase

# 로컬 Supabase 시작
supabase start

# 마이그레이션 실행
supabase db push
```

## 📁 프로젝트 구조

```
kiko-vooster/
├── frontend/                 # SvelteKit 프론트엔드
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/   # UI 컴포넌트
│   │   │   │   ├── components/   # UI 컴포넌트
│   │   │   │   ├── stores/       # Svelte 스토어
│   │   │   │   ├── hooks/        # 커스텀 훅
│   │   │   │   └── utils/        # 유틸리티 함수
│   │   │   ├── routes/           # SvelteKit 라우트
│   │   │   └── styles/           # 스타일 파일
│   │   ├── static/               # 정적 자원
│   │   └── package.json
│   ├── backend/                  # FastAPI 백엔드
│   │   ├── app/
│   │   │   ├── api/v1/          # API 엔드포인트
│   │   │   ├── services/        # 비즈니스 로직
│   │   │   ├── models/          # 데이터 모델
│   │   │   ├── websocket/       # WebSocket 핸들러
│   │   │   ├── core/            # 핵심 설정
│   │   │   └── utils/           # 유틸리티
│   │   ├── Dockerfile           # Docker 설정
│   │   └── pyproject.toml       # Python 의존성
│   ├── database/                # 데이터베이스 관련
│   │   ├── migrations/          # DB 마이그레이션
│   │   ├── seeds/               # 시드 데이터
│   │   └── schema.sql           # DB 스키마
│   └── infrastructure/          # 인프라 설정
│       ├── fly/                 # Fly.io 설정
│       ├── vercel/              # Vercel 설정
│       ├── scripts/             # 배포 스크립트
│       └── monitoring/          # 모니터링 설정
```

## 🌿 브랜치 정책

### 브랜치 전략
- `main`: 프로덕션 브랜치 (배포용)
- `develop`: 개발 브랜치 (통합 테스트)
- `feature/*`: 기능 개발 브랜치
- `hotfix/*`: 긴급 수정 브랜치

### 브랜치 네이밍 규칙
```
feature/auth-login          # 기능 개발
hotfix/player-sync-bug      # 버그 수정
chore/update-dependencies   # 기타 작업
```

### PR 규칙
1. 모든 변경사항은 PR을 통해 진행
2. 최소 1명의 코드 리뷰 필수
3. CI/CD 통과 후 병합
4. 스쿼시 병합 사용

## 🧪 테스트

### Frontend 테스트
```bash
cd frontend
pnpm test              # 단위 테스트
pnpm test:e2e          # E2E 테스트
pnpm test:coverage     # 커버리지 리포트
```

### Backend 테스트
```bash
cd backend
pytest                 # 단위 테스트
pytest --cov          # 커버리지 포함
```

## 🚀 배포

### Frontend 배포 (Vercel)
```bash
cd frontend
pnpm build
pnpm preview
```

### Backend 배포 (Fly.io)
```bash
cd backend
fly deploy
```

## 🤝 기여 가이드라인

### 코드 스타일
- **TypeScript**: 엄격한 타입 사용
- **Python**: PEP 8 준수, type hints 필수
- **Prettier**: 자동 포맷팅 (`.prettierrc` 참조)
- **ESLint**: 코드 품질 검사

### 커밋 메시지 규칙
```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 업데이트
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 코드 추가
chore: 기타 변경사항
```

### 개발 워크플로우
1. `feature/*` 브랜치에서 개발
2. 테스트 코드 작성 및 통과
3. PR 생성 및 코드 리뷰
4. CI/CD 통과 후 `develop` 브랜치로 병합
5. `develop` → `main` 병합 (릴리즈)

## 📞 문의 및 지원

- **이슈 트래킹**: GitHub Issues
- **문서**: [프로젝트 위키](링크)
- **개발 가이드**: `vooster__guideline.mdc` 참조

## 📄 라이선스

이 프로젝트는 MIT 라이선스하에 배포됩니다.

---

⚠️ **주의사항**: 이 프로젝트는 현재 개발 중입니다. 프로덕션 환경에서 사용하기 전에 충분한 테스트를 거쳐주세요. 