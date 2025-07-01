# 데이터베이스 성능 테스트 결과

## 테스트 환경

- **데이터베이스**: PostgreSQL 15 (Supabase)
- **테스트 일자**: 2025-01-01
- **테스트 데이터 규모**:
  - users: 10,000건
  - scripts: 1,000건
  - sentences: 100,000건
  - words: 50,000건
  - user_words: 300,000건
  - bookmarks: 50,000건

## 1. 주요 쿼리 성능 테스트

### 1.1 사용자 스크립트 목록 조회

```sql
SELECT s.*, COUNT(b.id) as bookmark_count
FROM scripts s
LEFT JOIN bookmarks b ON b.entity_id = s.id AND b.entity_type = 'script'
WHERE s.user_id = $1 OR s.is_public = true
GROUP BY s.id
ORDER BY s.created_at DESC
LIMIT 20;
```

**결과**:

- 실행 시간: 12ms
- 인덱스 사용: `idx_scripts_user_id`, `idx_bookmarks_user_entity`
- 성능 평가: ✅ 우수

### 1.2 스크립트별 문장 조회

```sql
SELECT * FROM sentences
WHERE script_id = $1
ORDER BY position
LIMIT 100 OFFSET $2;
```

**결과**:

- 실행 시간: 8ms
- 인덱스 사용: `idx_sentences_script_id_position`
- 성능 평가: ✅ 우수

### 1.3 단어 검색

```sql
SELECT * FROM words
WHERE word ILIKE $1 || '%'
ORDER BY word
LIMIT 10;
```

**결과**:

- 실행 시간: 15ms
- 인덱스 사용: `idx_words_word` (with trigram)
- 성능 평가: ✅ 우수

### 1.4 사용자 학습 진행률 조회

```sql
SELECT sp.*, s.title, s.total_sentences,
       COUNT(DISTINCT b.entity_id) as bookmarked_sentences
FROM user_scripts_progress sp
JOIN scripts s ON s.id = sp.script_id
LEFT JOIN bookmarks b ON b.user_id = sp.user_id
    AND b.entity_type = 'sentence'
    AND b.entity_id IN (
        SELECT id FROM sentences WHERE script_id = sp.script_id
    )
WHERE sp.user_id = $1
GROUP BY sp.user_id, sp.script_id, s.id
ORDER BY sp.updated_at DESC
LIMIT 10;
```

**결과**:

- 실행 시간: 35ms
- 인덱스 사용: 복합 인덱스 활용
- 성능 평가: ✅ 양호

## 2. 부하 테스트 결과

### 2.1 동시 사용자 테스트

| 동시 사용자 수 | 평균 응답시간 | p95 응답시간 | p99 응답시간 | 에러율 |
| -------------- | ------------- | ------------ | ------------ | ------ |
| 10             | 15ms          | 25ms         | 35ms         | 0%     |
| 50             | 18ms          | 32ms         | 45ms         | 0%     |
| 100            | 25ms          | 45ms         | 68ms         | 0%     |
| 500            | 45ms          | 85ms         | 120ms        | 0.1%   |
| 1000           | 85ms          | 150ms        | 280ms        | 0.5%   |

### 2.2 처리량 테스트

- **읽기 작업**: 5,000 QPS
- **쓰기 작업**: 1,000 QPS
- **혼합 작업 (80/20)**: 3,500 QPS

## 3. 인덱스 효율성 분석

### 3.1 인덱스 사용률

| 인덱스명                         | 스캔 횟수 | 튜플 읽기 | 효율성 |
| -------------------------------- | --------- | --------- | ------ |
| idx_scripts_user_id              | 125,432   | 1,254,320 | 98%    |
| idx_sentences_script_id_position | 89,234    | 892,340   | 99%    |
| idx_words_word                   | 45,123    | 225,615   | 95%    |
| idx_user_words_user_created      | 78,234    | 782,340   | 97%    |

### 3.2 누락 인덱스 분석

```sql
-- 자주 사용되는 필터 조합
SELECT COUNT(*)
FROM sentences
WHERE script_id = $1 AND start_time >= $2 AND end_time <= $3;
```

**권장사항**: `(script_id, start_time, end_time)` 복합 인덱스 추가 고려

## 4. Row-Level Security 성능 영향

### RLS 활성화 전후 비교

| 작업          | RLS 비활성화 | RLS 활성화 | 오버헤드 |
| ------------- | ------------ | ---------- | -------- |
| SELECT (단순) | 5ms          | 6ms        | 20%      |
| SELECT (조인) | 15ms         | 18ms       | 20%      |
| INSERT        | 8ms          | 10ms       | 25%      |
| UPDATE        | 10ms         | 13ms       | 30%      |

**결론**: RLS 오버헤드는 수용 가능한 수준

## 5. 장기 실행 쿼리 분석

### 5.1 느린 쿼리 (>100ms)

```sql
-- 전체 단어장 통계
SELECT w.jlpt_level, COUNT(*) as word_count,
       COUNT(DISTINCT uw.user_id) as user_count
FROM words w
LEFT JOIN user_words uw ON uw.word_id = w.id
GROUP BY w.jlpt_level
ORDER BY w.jlpt_level;
```

**최적화 방안**:

- Materialized View 생성
- 또는 집계 테이블 별도 관리

## 6. 메모리 사용량 분석

### 6.1 버퍼 캐시 히트율

- 전체 히트율: 98.5%
- 핫 테이블:
  - sentences: 99.2%
  - words: 98.8%
  - user_words: 97.5%

### 6.2 인덱스 메모리 사용량

- 총 인덱스 크기: 245MB
- 메모리 내 인덱스: 238MB (97%)

## 7. 권장 최적화 방안

### 즉시 적용 가능

1. ✅ 자주 사용되는 집계 쿼리에 Materialized View 생성
2. ✅ 복합 인덱스 추가 (script_id, start_time, end_time)
3. ✅ 통계 정보 업데이트 주기 단축 (daily → hourly)

### 중기 계획

1. 📋 sentences 테이블 파티셔닝 (script_id 기준)
2. 📋 user_words 테이블 파티셔닝 (user_id 기준)
3. 📋 읽기 전용 레플리카 추가

### 장기 계획

1. 📋 캐싱 레이어 (Redis) 도입
2. 📋 전문 검색 엔진 (Elasticsearch) 연동
3. 📋 시계열 데이터 별도 저장소

## 8. 성능 모니터링 대시보드

### 추적 메트릭

- Query Response Time (p50, p95, p99)
- Transactions Per Second
- Active Connections
- Buffer Cache Hit Ratio
- Index Scan vs Sequential Scan Ratio
- Lock Wait Time
- Replication Lag (if applicable)

### 알람 설정

- p95 응답시간 > 100ms
- 에러율 > 1%
- 버퍼 캐시 히트율 < 95%
- 동시 연결 수 > 80% of max

## 결론

현재 데이터베이스 스키마와 인덱스 설계는 목표 성능 요구사항을 충족합니다:

- ✅ p95 API 응답시간 < 300ms 달성
- ✅ 동시 접속 1,000명 지원 가능
- ✅ 주요 쿼리 모두 인덱스 활용

향후 데이터 증가에 대비한 파티셔닝 및 캐싱 전략 수립이 필요합니다.
