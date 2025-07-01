# 라디오 오디오 재생 API 구현 계획

## 1. 분석 결과

### 1.1 현재 코드베이스 상태

- **프레임워크**: FastAPI + Uvicorn
- **데이터베이스**: Supabase (PostgreSQL 15) 연동 완료
- **인증**: JWT 기반 설정 준비
- **라우터 구조**: 도메인별 모듈화 완료
- **설정 관리**: Pydantic 기반 환경 변수 관리

### 1.2 필요한 추가 구성

- 오디오 스트리밍 모듈
- Redis 캐싱 레이어
- FFmpeg 통합
- CDN 연동
- WebSocket 실시간 통신

## 2. 기술 아키텍처

### 2.1 컴포넌트 구조

```
backend/app/
├── api/v1/endpoints/
│   └── audio.py          # 오디오 API 엔드포인트
├── services/
│   ├── audio_service.py  # 오디오 처리 로직
│   ├── cache_service.py  # Redis 캐싱
│   └── cdn_service.py    # CDN 연동
├── models/
│   └── audio.py          # Pydantic 모델
├── core/
│   ├── redis.py          # Redis 클라이언트
│   └── storage.py        # Supabase Storage
└── utils/
    └── ffmpeg.py         # FFmpeg 래퍼
```

### 2.2 의존성

```toml
# 추가 필요한 패키지
aioredis = "^2.0.1"       # Redis 비동기 클라이언트
python-multipart = "^0.0.6" # 파일 업로드
httpx = "^0.24.1"         # 비동기 HTTP 클라이언트
ffmpeg-python = "^0.2.0"  # FFmpeg 래퍼
websockets = "^11.0"      # WebSocket
```

## 3. 공통 모듈 설계

### 3.1 오디오 서비스 인터페이스

```python
class AudioService:
    async def get_stream_url(script_id: UUID, quality: str) -> StreamInfo
    async def prepare_audio(script_id: UUID, priority: str) -> PrepareStatus
    async def process_hls(file_path: str) -> List[str]
    async def generate_manifest(segments: List[str]) -> str
```

### 3.2 캐시 서비스 인터페이스

```python
class CacheService:
    async def get(key: str) -> Optional[Any]
    async def set(key: str, value: Any, ttl: int)
    async def delete(key: str)
    async def exists(key: str) -> bool
```

### 3.3 CDN 서비스 인터페이스

```python
class CDNService:
    async def upload_segment(segment_path: str) -> str
    async def generate_signed_url(resource: str) -> str
    async def purge_cache(pattern: str)
```

## 4. 구현 우선순위

### Phase 1: 기본 기능 (3일)

1. **오디오 엔드포인트 구현**

   - GET /audio/stream/{script_id}
   - POST /audio/play
   - PUT /audio/progress

2. **Supabase Storage 연동**

   - 오디오 파일 업로드/다운로드
   - 메타데이터 관리

3. **기본 재생 기능**
   - 스트림 URL 생성
   - 재생 세션 관리
   - 진행률 저장

### Phase 2: 캐싱 및 최적화 (3일)

1. **Redis 캐싱 구현**

   - 스트림 URL 캐싱
   - 세션 데이터 캐싱
   - 메타데이터 캐싱

2. **FFmpeg 통합**

   - HLS 변환
   - 세그먼트 생성
   - 비트레이트 조정

3. **프리로딩 로직**
   - 첫 세그먼트 자동 로드
   - 예측 기반 프리페치

### Phase 3: 고급 기능 (2일)

1. **CDN 연동**

   - Cloudflare Workers 설정
   - Signed URL 생성
   - 캐시 무효화

2. **실시간 기능**

   - WebSocket 연결
   - 실시간 진행률 동기화
   - 다중 기기 지원

3. **북마크 및 반복**
   - 구간 북마크
   - A-B 반복 재생
   - 재생 속도 조절

## 5. 위험 요소 및 대응 방안

### 5.1 기술적 위험

| 위험 요소         | 영향도 | 대응 방안                        |
| ----------------- | ------ | -------------------------------- |
| FFmpeg 성능 병목  | 높음   | 비동기 처리, 워커 풀 사용        |
| 대용량 파일 처리  | 중간   | 청크 단위 처리, 스트리밍 업로드  |
| CDN 연동 복잡성   | 중간   | Cloudflare SDK 활용, 단계적 적용 |
| Redis 메모리 부족 | 낮음   | TTL 최적화, 선택적 캐싱          |

### 5.2 보안 위험

- **인증 우회**: JWT 검증 강화, 미들웨어 적용
- **DDoS 공격**: Rate limiting, IP 차단
- **파일 접근**: Signed URL, 권한 체크

## 6. 테스트 전략

### 6.1 단위 테스트

- 각 서비스 메서드 테스트
- 모킹을 통한 외부 의존성 격리
- 에러 케이스 처리 검증

### 6.2 통합 테스트

- API 엔드포인트 전체 플로우
- 실제 파일 처리 테스트
- 캐싱 동작 검증

### 6.3 성능 테스트

- 동시 접속 부하 테스트
- 대용량 파일 처리
- 응답 시간 측정

## 7. 모니터링 계획

### 7.1 메트릭 수집

```python
# Prometheus 메트릭
audio_stream_requests = Counter('audio_stream_requests_total')
audio_stream_duration = Histogram('audio_stream_duration_seconds')
cache_hit_rate = Gauge('cache_hit_rate')
```

### 7.2 로깅 전략

- 구조화된 JSON 로그
- 요청별 트레이싱 ID
- 에러 자동 알림

## 8. 예외 처리 시나리오

### 8.1 파일 관련

- **파일 없음**: 404 응답, 대체 파일 제공
- **손상된 파일**: 재처리 시도, 관리자 알림
- **형식 미지원**: 400 응답, 지원 형식 안내

### 8.2 시스템 관련

- **Redis 다운**: 직접 DB 조회, 성능 저하 알림
- **CDN 장애**: 원본 서버 폴백
- **FFmpeg 실패**: 재시도 후 원본 제공

## 9. 문서화 계획

### 9.1 API 문서

- OpenAPI 스펙 자동 생성
- 예제 요청/응답 포함
- 에러 코드 상세 설명

### 9.2 개발자 가이드

- 아키텍처 다이어그램
- 설정 가이드
- 트러블슈팅 가이드

## 10. 검증 체크리스트

### 기능 검증

- [ ] 모든 API 엔드포인트 동작 확인
- [ ] 인증/권한 체크 정상 동작
- [ ] 캐싱 효과 측정
- [ ] CDN 연동 확인

### 성능 검증

- [ ] p95 응답시간 < 300ms
- [ ] 동시 접속 1000+ 지원
- [ ] 버퍼링 < 1초
- [ ] 메모리 사용량 안정적

### 보안 검증

- [ ] 인증 우회 불가
- [ ] SQL 인젝션 방어
- [ ] 파일 접근 제어
- [ ] Rate limiting 동작
