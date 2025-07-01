# 오디오 API 테스트 가이드

## 1. 테스트 환경 설정

### 1.1 필수 요구사항

- Python 3.11+
- Redis 서버 (캐시 테스트용)
- Supabase 프로젝트 (테스트 환경)
- FFmpeg (오디오 처리 테스트용)

### 1.2 의존성 설치

```bash
cd backend
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-mock httpx
```

### 1.3 환경 변수 설정

```bash
# .env.test 파일 생성
cp .env.example .env.test

# 테스트용 환경 변수 설정
export ENVIRONMENT=test
export DATABASE_URL=postgresql://...
export REDIS_URL=redis://localhost:6379/1
```

## 2. 테스트 실행

### 2.1 전체 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 상세 출력과 함께 실행
pytest -v

# 특정 마커의 테스트만 실행
pytest -m unit          # 단위 테스트만
pytest -m integration   # 통합 테스트만
pytest -m "not slow"    # 느린 테스트 제외
```

### 2.2 특정 테스트 실행

```bash
# 특정 파일의 테스트 실행
pytest tests/test_audio_api.py

# 특정 클래스의 테스트 실행
pytest tests/test_audio_api.py::TestAudioAPI

# 특정 테스트 메서드 실행
pytest tests/test_audio_api.py::TestAudioAPI::test_get_stream_success
```

### 2.3 커버리지 측정

```bash
# 커버리지와 함께 테스트 실행
pytest --cov=app --cov-report=html

# 커버리지 리포트 확인
open htmlcov/index.html
```

## 3. 테스트 시나리오

### 3.1 단위 테스트

| 테스트             | 설명                  | 파일                |
| ------------------ | --------------------- | ------------------- |
| Pydantic 모델 검증 | 요청/응답 모델 유효성 | `test_audio_api.py` |
| 캐시 매니저        | 캐시 저장/조회/삭제   | `test_audio_api.py` |
| 스토리지 매니저    | 파일 업로드/다운로드  | `test_audio_api.py` |
| 오디오 서비스 로직 | 비즈니스 로직         | `test_audio_api.py` |

### 3.2 통합 테스트

| 테스트           | 설명                               | 파일                        |
| ---------------- | ---------------------------------- | --------------------------- |
| 전체 재생 플로우 | 스트림 조회 → 재생 → 진행률 → 종료 | `test_audio_integration.py` |
| 에러 처리        | 404, 403, 500 에러 응답            | `test_audio_integration.py` |
| 성능 요구사항    | p95 < 300ms 검증                   | `test_audio_integration.py` |
| 동시 세션 처리   | 멀티 세션 동시 처리                | `test_audio_integration.py` |
| 캐시 효과        | 캐시 히트율 측정                   | `test_audio_integration.py` |

### 3.3 성능 테스트

```python
# 성능 측정 예시
async def test_api_performance(performance_counter):
    with performance_counter.measure("stream_api"):
        response = await client.get("/api/v1/audio/stream/...")

    stats = performance_counter.get_stats()
    assert stats["p95"] < 0.3  # 300ms
```

## 4. 테스트 데이터 준비

### 4.1 샘플 스크립트 생성

```sql
-- 테스트용 스크립트 데이터
INSERT INTO scripts (id, title, audio_url, duration, user_id)
VALUES
  ('123e4567-e89b-12d3-a456-426614174000', '테스트 라디오', 'test.mp3', 3600, ...);
```

### 4.2 샘플 오디오 파일

```bash
# 테스트용 오디오 파일 생성
ffmpeg -f lavfi -i "sine=frequency=440:duration=60" test.mp3
```

## 5. CI/CD 통합

### 5.1 GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run tests
        env:
          REDIS_URL: redis://localhost:6379/0
        run: |
          pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 6. 테스트 모범 사례

### 6.1 AAA 패턴

```python
async def test_example():
    # Arrange - 준비
    test_data = create_test_data()

    # Act - 실행
    result = await service.process(test_data)

    # Assert - 검증
    assert result.status == "success"
```

### 6.2 격리된 테스트

- 각 테스트는 독립적으로 실행 가능해야 함
- 테스트 간 상태 공유 금지
- 테스트 후 데이터 정리

### 6.3 명확한 테스트 이름

```python
# Good
async def test_get_stream_returns_404_when_script_not_found():
    ...

# Bad
async def test_stream():
    ...
```

## 7. 문제 해결

### 7.1 일반적인 문제

**Redis 연결 실패**

```bash
# Redis 서버 시작
redis-server

# 또는 Docker 사용
docker run -d -p 6379:6379 redis:7
```

**데이터베이스 연결 실패**

```bash
# 테스트 DB 생성
createdb kiko_test

# 마이그레이션 실행
alembic upgrade head
```

**느린 테스트**

```bash
# 느린 테스트 찾기
pytest --durations=10

# 병렬 실행
pytest -n auto
```

### 7.2 디버깅

```python
# 테스트 중 디버깅
import pdb; pdb.set_trace()

# 또는 pytest 내장 디버거
pytest --pdb

# 로그 출력
pytest -s
```

## 8. 체크리스트

### 8.1 테스트 완료 기준

- [ ] 모든 API 엔드포인트 테스트 작성
- [ ] 정상 및 예외 플로우 커버
- [ ] 성능 요구사항 검증 (p95 < 300ms)
- [ ] 캐시 효과 측정
- [ ] 동시성 테스트 통과
- [ ] 코드 커버리지 80% 이상
- [ ] CI/CD 파이프라인 통합
- [ ] 테스트 문서화 완료

### 8.2 리뷰 체크포인트

- [ ] 테스트가 명확하고 이해하기 쉬운가?
- [ ] 엣지 케이스를 모두 다루는가?
- [ ] 테스트가 빠르게 실행되는가?
- [ ] 테스트가 신뢰할 수 있는가?

## 9. 참고 자료

- [pytest 공식 문서](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [FastAPI 테스팅](https://fastapi.tiangolo.com/tutorial/testing/)
- [httpx 문서](https://www.python-httpx.org/)
