# 🚀 데이터베이스 스키마 구현 계획

## 📋 개요

Kiko 일본어 라디오 학습 플랫폼의 데이터베이스 스키마 구현을 위한 단계별 계획서입니다.

## 🎯 구현 목표

- **완전성**: PRD 요구사항을 100% 반영한 데이터 모델 구현
- **성능**: 예상 트래픽(WAU 10K)에 최적화된 인덱스 및 쿼리 설계
- **보안**: Supabase Row-Level Security를 통한 완전한 데이터 격리
- **확장성**: 향후 기능 추가를 고려한 유연한 스키마 설계

## 🏗️ 구현 단계

### Phase 1: 기본 인프라 준비

**예상 소요시간**: 1일

#### 1.1 Supabase 프로젝트 설정

- [ ] Supabase 프로젝트 생성 및 설정
- [ ] PostgreSQL 15 데이터베이스 확인
- [ ] 기본 익스텐션 활성화 (uuid-ossp, pgcrypto)
- [ ] 환경 변수 설정 (백엔드 연동)

#### 1.2 마이그레이션 도구 준비

- [ ] Supabase CLI 설치 및 설정
- [ ] 마이그레이션 파일 구조 확인
- [ ] 백업 및 롤백 계획 수립

### Phase 2: 스키마 생성 및 기본 설정

**예상 소요시간**: 1일

#### 2.1 기본 테이블 생성

```bash
# 마이그레이션 실행
supabase db push database/migrations/01_create_base_tables.sql
```

**생성될 테이블**:

- `users` (사용자 기본 정보)
- `scripts` (라디오/팟캐스트 메타데이터)
- `sentences` (스크립트 문장 분할)
- `words` (일본어 단어 사전)
- `user_words` (개인 단어장)
- `user_scripts_progress` (학습 진행률)
- `bookmarks` (북마크 시스템)

#### 2.2 인덱스 최적화

```bash
supabase db push database/migrations/02_create_indexes.sql
```

**주요 인덱스**:

- B-tree 인덱스: 일반적인 WHERE, ORDER BY 조건
- GIN 인덱스: 배열, JSONB, 전문 검색
- 복합 인덱스: 자주 사용되는 필터 조합

### Phase 3: 보안 정책 적용

**예상 소요시간**: 0.5일

#### 3.1 Row-Level Security 설정

```bash
supabase db push database/migrations/03_setup_rls.sql
```

**RLS 정책 개요**:

- **사용자 데이터**: 본인만 접근 가능
- **공개 콘텐츠**: 모든 사용자 읽기 가능
- **관리자 권한**: 콘텐츠 생성/수정/삭제

#### 3.2 인증 연동 테스트

- [ ] Supabase Auth JWT 토큰 검증
- [ ] 정책 적용 확인 (사용자별 데이터 격리)
- [ ] 관리자 권한 테스트

### Phase 4: 자동화 및 검증

**예상 소요시간**: 0.5일

#### 4.1 트리거 및 함수 적용

```bash
supabase db push database/migrations/04_create_triggers.sql
```

**구현될 기능**:

- `updated_at` 자동 갱신
- 문장 시간 범위 검증
- 복습 스케줄 자동 계산
- 북마크 유효성 검증

#### 4.2 데이터 정합성 검증

- [ ] 외래키 제약조건 테스트
- [ ] CHECK 제약조건 검증
- [ ] 트리거 동작 확인

## 🧪 테스트 및 검증 계획

### 1. 스키마 검증

```sql
-- 테이블 생성 확인
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- 인덱스 생성 확인
SELECT indexname, tablename FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- RLS 정책 확인
SELECT schemaname, tablename, policyname, cmd, roles
FROM pg_policies
ORDER BY tablename, policyname;
```

### 2. 성능 테스트

```sql
-- 주요 쿼리 성능 측정
EXPLAIN ANALYZE SELECT * FROM scripts
WHERE category = 'news' AND difficulty_level = 'beginner'
ORDER BY created_at DESC LIMIT 20;

EXPLAIN ANALYZE SELECT * FROM sentences
WHERE script_id = $1 ORDER BY order_index;

EXPLAIN ANALYZE SELECT * FROM user_words
WHERE user_id = $1 AND next_review <= NOW()
ORDER BY mastery_level LIMIT 10;
```

### 3. 보안 테스트

```sql
-- RLS 정책 테스트 (사용자별 데이터 격리)
-- 테스트 사용자 A로 로그인
SELECT * FROM user_words; -- 본인 데이터만 조회되어야 함

-- 테스트 사용자 B로 로그인
SELECT * FROM user_words; -- 다른 사용자 데이터는 조회되지 않아야 함
```

## 📊 백엔드 연동 가이드

### 1. Pydantic 모델 매핑 확인

| 백엔드 모델        | DB 테이블               | 매핑 상태    |
| ------------------ | ----------------------- | ------------ |
| `User`             | `users`                 | ✅ 완전 매핑 |
| `Script`           | `scripts`               | ✅ 완전 매핑 |
| `Sentence`         | `sentences`             | ✅ 완전 매핑 |
| `Word`             | `words`                 | ✅ 완전 매핑 |
| `UserWord`         | `user_words`            | ✅ 완전 매핑 |
| `PlaybackProgress` | `user_scripts_progress` | ✅ 완전 매핑 |

### 2. API 엔드포인트 연동 체크리스트

#### Scripts API

- [ ] `GET /scripts/` - 스크립트 목록 조회
- [ ] `GET /scripts/{id}` - 특정 스크립트 조회
- [ ] `GET /scripts/{id}/sentences` - 문장 목록 조회
- [ ] `POST /scripts/{id}/progress` - 진행률 업데이트
- [ ] `GET /scripts/{id}/progress` - 진행률 조회

#### Words API

- [ ] `GET /words/search` - 단어 검색
- [ ] `GET /words/vocabulary` - 단어장 조회
- [ ] `POST /words/vocabulary` - 단어 추가
- [ ] `PUT /words/vocabulary/{id}` - 단어 수정
- [ ] `GET /words/review` - 복습 단어 조회
- [ ] `POST /words/review/{id}/result` - 복습 결과 제출

#### Users API

- [ ] `GET /users/me` - 사용자 정보 조회
- [ ] `PUT /users/me` - 사용자 정보 수정
- [ ] `GET /users/stats` - 학습 통계 조회
- [ ] `GET /users/progress` - 학습 진행상황 조회

### 3. 데이터베이스 연결 설정

```python
# backend/app/core/database.py
from supabase import create_client
import os

# Supabase 클라이언트 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# 예시: 스크립트 조회
def get_scripts(category=None, difficulty=None, limit=20, offset=0):
    query = supabase.table("scripts").select("*")

    if category:
        query = query.eq("category", category)
    if difficulty:
        query = query.eq("difficulty_level", difficulty)

    return query.order("created_at", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
```

## 🔄 마이그레이션 실행 순서

### 개발 환경

```bash
# 1. 로컬 Supabase 시작
supabase start

# 2. 마이그레이션 실행 (순서대로)
psql -h localhost -p 54321 -U postgres -d postgres -f database/migrations/01_create_base_tables.sql
psql -h localhost -p 54321 -U postgres -d postgres -f database/migrations/02_create_indexes.sql
psql -h localhost -p 54321 -U postgres -d postgres -f database/migrations/03_setup_rls.sql
psql -h localhost -p 54321 -U postgres -d postgres -f database/migrations/04_create_triggers.sql

# 3. 백엔드 연동 테스트
cd backend && python -m pytest tests/test_database.py
```

### 프로덕션 환경

```bash
# 1. 마이그레이션 배포
supabase db push --linked

# 2. 데이터 백업 확인
supabase db dump --linked > backup_before_migration.sql

# 3. 단계별 적용 및 검증
# 각 마이그레이션 파일을 개별적으로 적용하며 검증
```

## ⚠️ 위험 요소 및 대응책

### 1. 데이터 손실 위험

**위험**: 마이그레이션 중 기존 데이터 손실
**대응**:

- 프로덕션 배포 전 스테이징 환경에서 전체 테스트
- 마이그레이션 전 완전한 데이터 백업
- 롤백 스크립트 준비

### 2. 성능 이슈

**위험**: 인덱스 부족으로 인한 쿼리 성능 저하
**대응**:

- EXPLAIN ANALYZE로 주요 쿼리 성능 사전 검증
- 점진적 인덱스 추가 (트래픽 적은 시간대)
- 모니터링 도구로 실시간 성능 추적

### 3. RLS 정책 오류

**위험**: 잘못된 보안 정책으로 데이터 누출/접근 차단
**대응**:

- 다양한 사용자 시나리오로 정책 테스트
- 관리자/일반사용자/비로그인 사용자별 접근 검증
- 단계별 정책 적용 및 검증

## 📈 성공 기준

### 기능적 요구사항

- [ ] 모든 PRD 요구사항이 데이터 모델에 반영됨
- [ ] 백엔드 API와 100% 호환성 확보
- [ ] 사용자별 완전한 데이터 격리 달성

### 비기능적 요구사항

- [ ] 주요 쿼리 응답시간 < 100ms (p95)
- [ ] 동시 접속 1000명 지원 (초기 목표)
- [ ] 데이터 정합성 100% 보장

### 운영 요구사항

- [ ] 완전한 백업/복구 프로세스 구축
- [ ] 모니터링 및 알람 시스템 연동
- [ ] 문서화 및 팀 온보딩 자료 완성

---

**다음 단계**: 이 계획에 따라 실제 마이그레이션을 실행하고 백엔드 연동 테스트를 진행합니다.
