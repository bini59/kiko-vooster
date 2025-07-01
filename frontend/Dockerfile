# Multi-stage build for SvelteKit frontend
FROM node:18-alpine as builder

# 작업 디렉토리 설정
WORKDIR /app

# 패키지 매니저 설정 (yarn 사용)
RUN corepack enable && corepack prepare yarn@stable --activate

# 의존성 파일 복사
COPY package.json yarn.lock ./

# 의존성 설치
RUN yarn install --frozen-lockfile

# 소스 코드 복사
COPY . .

# 빌드
RUN yarn build

# Production stage
FROM node:18-alpine

# 비 root 사용자 생성
RUN addgroup -g 1001 -S kiko && \
    adduser -S kiko -u 1001

# 작업 디렉토리 설정
WORKDIR /app

# 패키지 매니저 설정
RUN corepack enable && corepack prepare yarn@stable --activate

# 프로덕션 의존성만 설치
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile --production && yarn cache clean

# 빌드된 앱 복사
COPY --from=builder --chown=kiko:kiko /app/build ./build
COPY --from=builder --chown=kiko:kiko /app/package.json ./package.json

# 포트 노출
EXPOSE 3000

# 사용자 전환
USER kiko

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# 애플리케이션 실행
CMD ["node", "build"] 