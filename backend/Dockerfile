# Multi-stage build for FastAPI backend
FROM python:3.11-slim as builder

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# 비 root 사용자 생성
RUN groupadd -r kiko && useradd -r -g kiko kiko

# 필요한 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 패키지를 builder에서 복사
COPY --from=builder /root/.local /home/kiko/.local
ENV PATH=/home/kiko/.local/bin:$PATH

# 애플리케이션 코드 복사
COPY --chown=kiko:kiko . .

# 포트 노출
EXPOSE 8000

# 사용자 전환
USER kiko

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 애플리케이션 실행
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 