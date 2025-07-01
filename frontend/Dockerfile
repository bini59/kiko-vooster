# Multi-stage build for SvelteKit frontend
FROM node:18-alpine as builder

# 작업 디렉토리 설정
WORKDIR /app

# 패키지 매니저 설정 (yarn 1.x 고정)
RUN corepack enable && corepack prepare yarn@1.22.22 --activate

# 의존성 파일 복사
COPY package.json yarn.lock* ./

# 의존성 설치 (yarn 1.x 문법)
RUN yarn install --frozen-lockfile --network-timeout 300000

# 소스 코드 복사
COPY . .

# 빌드
RUN yarn build

# Production stage - nginx를 사용하여 정적 파일 서빙
FROM nginx:alpine

# nginx 설정
COPY --from=builder /app/build /usr/share/nginx/html

# 커스텀 nginx 설정 (SPA 라우팅 지원)
RUN echo 'server { \
    listen 3000; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    location /api { \
        proxy_pass http://backend:8000; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
    } \
}' > /etc/nginx/conf.d/default.conf

# 포트 노출
EXPOSE 3000

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# nginx 실행
CMD ["nginx", "-g", "daemon off;"] 