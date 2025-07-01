# 데이터베이스 설정 가이드

## 목차

1. [개요](#개요)
2. [로컬 개발 환경 설정](#로컬-개발-환경-설정)
3. [Supabase 프로젝트 설정](#supabase-프로젝트-설정)
4. [마이그레이션 실행](#마이그레이션-실행)
5. [데이터베이스 검증](#데이터베이스-검증)
6. [문제 해결](#문제-해결)

## 개요

Kiko 프로젝트는 Supabase (PostgreSQL 15)를 사용하며, Row-Level Security(RLS)를 통해 보안을 관리합니다.

### 주요 구성 요소

- **데이터베이스**: PostgreSQL 15
- **인증**: Supabase Auth
- **보안**: Row-Level Security (RLS)
- **실시간**: Supabase Realtime
- **스토리지**: Supabase Storage

## 로컬 개발 환경 설정

### 1. Supabase CLI 설치

```bash
# macOS/Linux
brew install supabase/tap/supabase

# Windows (Scoop)
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase

# npm/yarn
npm install -g supabase
```

### 2. 로컬 Supabase 시작

```bash
# 프로젝트 루트에서 실행
supabase init

# 로컬 서비스 시작
supabase start
```

로컬 서비스 URL:

- **Studio**: http://localhost:54323
- **API**: http://localhost:54321
- **DB**: postgresql://postgres:postgres@localhost:54322/postgres

### 3. 환경 변수 설정

```bash
# backend/.env
SUPABASE_URL=http://localhost:54321
SUPABASE_SERVICE_ROLE_KEY=<로컬 서비스 키>
SUPABASE_ANON_KEY=<로컬 익명 키>

# frontend/.env.local
PUBLIC_SUPABASE_URL=http://localhost:54321
PUBLIC_SUPABASE_ANON_KEY=<로컬 익명 키>
```

## Supabase 프로젝트 설정

### 1. 프로젝트 생성

1. [Supabase Dashboard](https://app.supabase.com)에 로그인
2. "New project" 클릭
3. 프로젝트 정보 입력:
   - 프로젝트 이름: `kiko-production`
   - 데이터베이스 비밀번호: 안전한 비밀번호 설정
   - 리전: Tokyo (일본)
   - 요금제: Free tier 또는 Pro

### 2. 프로젝트 키 확인

Settings > API에서:

- `anon` public key: 프론트엔드용
- `service_role` secret key: 백엔드용

### 3. 환경 변수 업데이트

```bash
# 프로덕션 환경 변수
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
```

## 마이그레이션 실행

### 1. 로컬 환경

```bash
# 개발 환경 마이그레이션
cd database
./deploy.sh development

# 또는 직접 실행
psql $DATABASE_URL < migrations/01_create_base_tables.sql
psql $DATABASE_URL < migrations/02_create_indexes.sql
psql $DATABASE_URL < migrations/03_setup_rls.sql
psql $DATABASE_URL < migrations/04_create_triggers.sql
```

### 2. 프로덕션 환경

```bash
# 프로덕션 마이그레이션 (주의!)
./deploy.sh production

# 또는 Supabase Dashboard SQL Editor에서 실행
```

### 3. 샘플 데이터 (선택사항)

```bash
# 개발용 샘플 데이터
psql $DATABASE_URL < seeds/01_sample_data.sql
```

## 데이터베이스 검증

### 1. 스키마 검증

```bash
# Python 스크립트로 검증
python database/test_schema.py

# 수동 검증
psql $DATABASE_URL -c "\dt"  # 테이블 목록
psql $DATABASE_URL -c "\d+ users"  # 테이블 구조
```

### 2. RLS 정책 검증

```sql
-- RLS 정책 확인
SELECT tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE schemaname = 'public';

-- RLS 활성화 확인
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public';
```

### 3. 연결 테스트

```bash
# API 상태 확인
curl http://localhost:8000/api/v1/db/status

# Supabase 연결 테스트
curl -H "apikey: $SUPABASE_ANON_KEY" \
     $SUPABASE_URL/rest/v1/users?select=count
```

## 문제 해결

### 일반적인 문제

#### 1. 마이그레이션 실패

```bash
# 롤백
psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# 재실행
./deploy.sh development
```

#### 2. RLS 정책 충돌

```sql
-- 기존 정책 삭제
DROP POLICY IF EXISTS policy_name ON table_name;

-- 재생성
CREATE POLICY policy_name ON table_name ...
```

#### 3. 연결 실패

```bash
# 환경 변수 확인
echo $SUPABASE_URL
echo $DATABASE_URL

# 포트 확인
lsof -i :54322  # PostgreSQL
lsof -i :54321  # Supabase API
```

### 성능 최적화

#### 1. 인덱스 분석

```sql
-- 누락된 인덱스 찾기
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
AND n_distinct > 100
AND correlation < 0.1
ORDER BY n_distinct DESC;
```

#### 2. 쿼리 성능 분석

```sql
-- 느린 쿼리 확인
SELECT query, calls, mean_time, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### 백업 및 복구

#### 1. 백업

```bash
# 전체 백업
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# 스키마만 백업
pg_dump $DATABASE_URL --schema-only > schema_backup.sql
```

#### 2. 복구

```bash
# 복구
psql $DATABASE_URL < backup_20240701_120000.sql
```

## 다음 단계

1. [API 엔드포인트 개발](../backend/README.md)
2. [프론트엔드 연동](../frontend/README.md)
3. [테스트 작성](./TESTING.md)
4. [배포 준비](../DEPLOYMENT.md)

## 참고 자료

- [Supabase 공식 문서](https://supabase.com/docs)
- [PostgreSQL 15 문서](https://www.postgresql.org/docs/15/)
- [Row-Level Security 가이드](https://supabase.com/docs/guides/auth/row-level-security)
- [프로젝트 스키마 설계](./schema_design.md)
