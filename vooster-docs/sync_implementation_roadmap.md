# 싱크 매핑 엔진 구현 로드맵

## 1. 전체 일정 개요

### 1.1 총 소요 시간: 13일

- **Phase 1**: 기반 구조 (7일)
- **Phase 2**: WebSocket 실시간 동기화 (5일)
- **Phase 3**: AI 자동 정렬 (3일)
- **총 기간**: 2.5주 (병렬 작업 고려)

### 1.2 주요 마일스톤

```
Day 1-7:   기반 구조 완료 → API 테스트 가능
Day 8-12:  실시간 동기화 → 멀티 클라이언트 테스트
Day 13-15: AI 정렬 구현 → 전체 시스템 통합 테스트
```

---

## 2. Phase 1: 기반 구조 (Day 1-7)

### 2.1 Day 1-2: 데이터베이스 스키마 및 마이그레이션

#### 작업 상세

- [ ] **마이그레이션 파일 생성** (06_create_sync_tables.sql)
- [ ] **새 테이블 3개** 구현: `sentence_mappings`, `mapping_edits`, `sync_sessions`
- [ ] **성능 인덱스** 추가: 6개 인덱스
- [ ] **RLS 정책** 설정: 편집 권한 제어
- [ ] **트리거 함수** 구현: 자동 타임스탬프 업데이트

#### 완료 기준

```sql
-- 테스트 쿼리가 모두 성공해야 함
SELECT * FROM sentence_mappings WHERE sentence_id = 'test-uuid';
INSERT INTO mapping_edits (...) VALUES (...);
SELECT performance FROM pg_stat_user_indexes WHERE indexname LIKE 'idx_sync_%';
```

#### 위험 요소

- **기존 sentences 테이블과의 호환성**: 마이그레이션 시 데이터 손실 위험
- **대응**: 백업 + 롤백 스크립트 준비, 테스트 환경에서 사전 검증

### 2.2 Day 3-4: 핵심 모델 및 서비스 구현

#### 작업 상세

- [ ] **Pydantic 모델** (app/models/sync.py):
  ```python
  - SentenceMapping, MappingEdit, SyncSession
  - TimecodeUpdate, MappingResult, AlignmentResult
  - SyncMessage (WebSocket 메시지)
  ```
- [ ] **SyncMappingEngine** 핵심 클래스:
  ```python
  - get_current_sentence()     # 위치별 문장 조회
  - update_timecode_mapping()  # 수동 편집
  - get_mapping_history()      # 편집 내역
  - validate_timecode_range()  # 겹침 검증
  ```
- [ ] **데이터 접근 계층** (app/repositories/sync_repository.py):
  ```python
  - get_sentence_mappings()
  - create_mapping_edit()
  - get_active_sync_sessions()
  ```

#### 완료 기준

```python
# 단위 테스트 통과
async def test_get_current_sentence():
    sentence = await sync_engine.get_current_sentence(script_id, 45.2)
    assert sentence.id is not None
    assert 45.0 <= sentence.start_time <= 45.2 <= sentence.end_time

async def test_update_timecode():
    result = await sync_engine.update_timecode_mapping(
        sentence_id, new_start=30.0, new_end=35.0
    )
    assert result.success == True
    assert result.confidence_score > 0.5
```

#### 위험 요소

- **타임코드 겹침 로직**: 복잡한 검증 로직으로 버그 가능성
- **대응**: 상세한 테스트 케이스 작성, 경계값 테스트

### 2.3 Day 5-6: REST API 엔드포인트 구현

#### 작업 상세

- [ ] **API 라우터** (app/api/v1/endpoints/sync.py):
  ```python
  GET    /sync/mappings/{script_id}       # 매핑 조회
  PUT    /sync/mappings/{sentence_id}     # 수동 편집
  GET    /sync/history/{script_id}        # 편집 내역
  POST   /sync/validate/{script_id}       # 매핑 검증
  ```
- [ ] **캐시 통합**: 기존 CacheManager 확장
  ```python
  - get_sentence_mapping()  # TTL: 24시간
  - set_mapping_cache()
  - invalidate_script_cache()  # 편집 시 캐시 무효화
  ```
- [ ] **에러 처리**: 일관된 HTTPException 패턴
- [ ] **API 문서화**: OpenAPI 스키마 자동 생성

#### 완료 기준

```bash
# API 테스트 통과
curl GET /api/v1/sync/mappings/script-123 → 200 OK
curl PUT /api/v1/sync/mappings/sentence-456 → 200 OK
curl GET /api/v1/sync/history/script-123 → 200 OK

# 응답 시간 기준
- p95 < 300ms (캐시 히트)
- p95 < 800ms (캐시 미스)
```

#### 위험 요소

- **캐시 무효화**: 편집 시 관련 캐시 일괄 삭제 누락
- **대응**: 캐시 태그 시스템 도입, 무효화 테스트 추가

### 2.4 Day 7: 통합 테스트 및 문서화

#### 작업 상세

- [ ] **통합 테스트**: API + DB + 캐시 전체 흐름
- [ ] **성능 테스트**: 1K 동시 요청 처리
- [ ] **API 문서 업데이트**: README.md, API_DOCUMENTATION.md
- [ ] **코드 리뷰**: 팀 내 품질 검토

#### 완료 기준

- 모든 테스트 통과 (단위 + 통합)
- API 문서화 100% 완료
- 코드 커버리지 ≥80%

---

## 3. Phase 2: WebSocket 실시간 동기화 (Day 8-12)

### 3.1 Day 8-9: WebSocket 기반 구조

#### 작업 상세

- [ ] **WebSocket 라우팅** (app/websocket/router.py):
  ```python
  /ws/sync/{script_id}  # 스크립트별 룸 연결
  ```
- [ ] **연결 관리** (app/websocket/connection_manager.py):
  ```python
  - connect_to_room()      # 스크립트 룸 참가
  - disconnect_from_room() # 연결 해제
  - get_room_users()       # 룸 참가자 조회
  - broadcast_to_room()    # 룸 내 브로드캐스트
  ```
- [ ] **JWT 인증**: WebSocket 연결 시 토큰 검증
- [ ] **Redis Pub/Sub 연동**: 다중 서버 간 메시지 전파

#### 완료 기준

```python
# WebSocket 연결 테스트
async def test_websocket_connection():
    async with websockets.connect("ws://localhost:8000/ws/sync/script-123") as ws:
        await ws.send(json.dumps({"type": "join_room"}))
        response = await ws.recv()
        assert json.loads(response)["type"] == "room_joined"

# 멀티 클라이언트 테스트
async def test_multi_client_broadcast():
    # 2개 클라이언트 연결 → 1개에서 메시지 전송 → 다른 클라이언트 수신 확인
```

#### 위험 요소

- **연결 안정성**: 네트워크 끊김, 재연결 처리
- **대응**: Heartbeat 구현, 자동 재연결 로직

### 3.2 Day 10-11: 실시간 동기화 로직

#### 작업 상세

- [ ] **메시지 타입 정의**:
  ```python
  - sentence_highlight: 문장 하이라이트 동기화
  - position_sync: 재생 위치 동기화
  - mapping_update: 타임코드 편집 전파
  - user_joined/left: 사용자 입/퇴장
  ```
- [ ] **브로드캐스터** (app/services/sync/realtime_broadcaster.py):
  ```python
  - broadcast_sentence_highlight()
  - broadcast_position_sync()
  - broadcast_mapping_change()
  ```
- [ ] **세션 관리**: sync_sessions 테이블 CRUD
- [ ] **메시지 큐잉**: Redis Stream 활용

#### 완료 기준

```python
# 실시간 동기화 테스트
async def test_sentence_highlight_sync():
    # Client A: 문장 클릭
    # Client B: 동일 문장 하이라이트 확인
    # 지연시간 < 1초

async def test_position_broadcast():
    # Client A: 재생 위치 변경
    # Client B: 동일 위치로 자동 이동
```

#### 위험 요소

- **메시지 순서**: 비동기 처리로 인한 메시지 순서 꼬임
- **대응**: 타임스탬프 기반 순서 보장, 중복 제거

### 3.3 Day 12: 안정성 및 에러 처리

#### 작업 상세

- [ ] **연결 복구**: 네트워크 끊김 시 자동 재연결
- [ ] **메시지 유실 방지**: Redis Streams 활용한 메시지 저장
- [ ] **부하 테스트**: 100 동시 연결 처리
- [ ] **모니터링**: 연결 수, 메시지 처리량 메트릭

#### 완료 기준

- 연결 안정성 테스트 통과
- 부하 테스트 성공 (100 동시 연결)
- 에러 복구 시나리오 검증

---

## 4. Phase 3: AI 자동 정렬 (Day 13-15)

### 4.1 Day 13: 음성 구간 검출

#### 작업 상세

- [ ] **VAD (Voice Activity Detection)** 구현:
  ```python
  - detect_speech_segments()   # 음성 구간 탐지
  - calculate_silence_gaps()   # 무음 구간 계산
  - segment_audio_by_time()    # 시간 기반 분할
  ```
- [ ] **의존성 추가**: librosa, webrtcvad
- [ ] **오디오 전처리**: 노이즈 제거, 정규화

#### 완료 기준

```python
# VAD 테스트
audio_segments = detect_speech_segments("test_audio.wav")
assert len(audio_segments) > 0
assert all(seg.end_time > seg.start_time for seg in audio_segments)
```

### 4.2 Day 14: 자동 정렬 알고리즘

#### 작업 상세

- [ ] **길이 기반 매핑**:
  ```python
  - estimate_sentence_duration()  # 문장 길이 → 예상 소요 시간
  - align_by_proportional()       # 비례 배분 정렬
  - adjust_by_speech_rate()       # 화자 속도 보정
  ```
- [ ] **신뢰도 점수**:
  ```python
  - calculate_alignment_confidence()  # 정렬 신뢰도 0-1
  - identify_low_confidence_regions() # 수동 편집 필요 구간
  ```
- [ ] **백그라운드 처리**: 비동기 태스크 큐

#### 완료 기준

- 자동 정렬 정확도 ≥70% (±500ms 허용)
- 신뢰도 점수 정확도 검증
- 10분 오디오 처리 시간 ≤30초

### 4.3 Day 15: 통합 및 최적화

#### 작업 상세

- [ ] **API 통합**: `/sync/auto-align/{script_id}` 엔드포인트
- [ ] **프로그레스 피드백**: 처리 진행률 실시간 업데이트
- [ ] **에러 복구**: 처리 실패 시 롤백 + 재시도
- [ ] **최종 테스트**: 전체 워크플로우 검증

#### 완료 기준

- 전체 시스템 통합 테스트 통과
- 실제 라디오 오디오 테스트 성공
- 성능 기준 달성 (p95 < 300ms)

---

## 5. 위험 관리 계획

### 5.1 기술 위험 대응

| 위험                      | 확률   | 영향도 | 대응 계획                           | 대안                    |
| ------------------------- | ------ | ------ | ----------------------------------- | ----------------------- |
| **WebSocket 연결 불안정** | Medium | High   | - Heartbeat 구현<br>- 자동 재연결   | Server-Sent Events 폴백 |
| **AI 정렬 정확도 부족**   | High   | Medium | - 수동 편집 기능<br>- 사용자 피드백 | 규칙 기반 정렬 알고리즘 |
| **동시 편집 충돌**        | Low    | Medium | - 낙관적 잠금<br>- 실시간 알림      | 마지막 수정자 우선      |
| **성능 병목**             | Medium | High   | - 캐시 최적화<br>- 인덱스 튜닝      | 읽기 전용 복제본        |

### 5.2 일정 위험 대응

| 위험          | 대응 방안                                          |
| ------------- | -------------------------------------------------- |
| **개발 지연** | - 핵심 기능 우선 구현<br>- AI 정렬은 후순위로 조정 |
| **통합 오류** | - 매일 통합 테스트<br>- 조기 문제 발견             |
| **성능 미달** | - 단계별 성능 측정<br>- 병목 지점 사전 식별        |

---

## 6. 품질 보증 체크리스트

### 6.1 각 Phase 완료 시 검증 항목

#### Phase 1 체크리스트

- [ ] 모든 단위 테스트 통과 (커버리지 ≥80%)
- [ ] API 응답 시간 p95 ≤300ms
- [ ] 데이터베이스 마이그레이션 무결성 확인
- [ ] 캐시 히트율 ≥70%
- [ ] 코드 리뷰 완료

#### Phase 2 체크리스트

- [ ] 멀티 클라이언트 동기화 테스트 통과
- [ ] WebSocket 연결 안정성 검증
- [ ] 메시지 전달 지연 ≤1초
- [ ] 100 동시 연결 부하 테스트 통과
- [ ] 에러 복구 시나리오 검증

#### Phase 3 체크리스트

- [ ] AI 정렬 정확도 ≥70%
- [ ] 백그라운드 처리 성능 검증
- [ ] 전체 시스템 통합 테스트 통과
- [ ] 실제 오디오 데이터 검증
- [ ] 모니터링 대시보드 구성

### 6.2 최종 검수 기준

```python
# 성능 기준
- API 응답 시간 p95 ≤ 300ms
- WebSocket 메시지 지연 ≤ 1초
- 동시 접속 100명 처리 가능
- 캐시 히트율 ≥ 70%

# 기능 기준
- 타임코드 매핑 CRUD 100% 동작
- 실시간 동기화 100% 동작
- AI 자동 정렬 70% 정확도
- 편집 내역 추적 100% 동작

# 품질 기준
- 코드 커버리지 ≥ 80%
- 코드 리뷰 100% 완료
- 문서화 100% 완료
- 보안 검토 완료
```

---

## 7. 성공 지표 및 모니터링

### 7.1 핵심 KPI

```python
# 기술적 성능
- sync_mapping_api_latency_p95 ≤ 300ms
- websocket_connection_success_rate ≥ 99%
- ai_alignment_accuracy_rate ≥ 70%
- cache_hit_rate ≥ 70%

# 사용자 경험
- sentence_click_response_time ≤ 1s
- real_time_sync_delay ≤ 1s
- mapping_edit_success_rate ≥ 95%
- user_session_duration (목표: 증가)
```

### 7.2 모니터링 대시보드

```python
# Grafana 대시보드 구성
1. 시스템 성능: API 지연시간, 에러율, 처리량
2. WebSocket 상태: 연결 수, 메시지 전송량, 재연결 빈도
3. 사용자 활동: 편집 횟수, 동기화 세션, 활성 사용자
4. AI 정렬: 처리 시간, 정확도, 실패율
```

이 로드맵은 기존 코드베이스와의 호환성을 보장하며, 단계적 구현을 통해 안정적인 출시를 지원합니다.
