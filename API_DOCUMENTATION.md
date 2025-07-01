# 📚 Kiko API 문서

Kiko 일본어 라디오 학습 플랫폼의 REST API 문서입니다.

## 🔗 기본 정보

- **Base URL**: `http://localhost:8000/api/v1` (개발)
- **Content-Type**: `application/json`
- **Authentication**: Bearer JWT Token
- **API Version**: v1.0.0

## 🔐 인증 (Authentication)

### JWT Token 방식

모든 보호된 엔드포인트는 Authorization 헤더에 JWT 토큰이 필요합니다.

```http
Authorization: Bearer <your-jwt-token>
```

### 토큰 획득

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

**응답:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

## 📝 API 엔드포인트

### 🔑 인증 (Auth) 

#### 회원가입
- **POST** `/auth/register`
- **Body**: `{ "email": "string", "password": "string", "name": "string", "japanese_level": "beginner" }`
- **Response**: JWT Token

#### 로그인
- **POST** `/auth/login` 
- **Body**: `{ "email": "string", "password": "string" }`
- **Response**: JWT Token

#### 사용자 정보 조회
- **GET** `/auth/me`
- **Headers**: `Authorization: Bearer <token>`
- **Response**: 사용자 프로필 정보

#### 로그아웃
- **POST** `/auth/logout`
- **Headers**: `Authorization: Bearer <token>`
- **Response**: 로그아웃 메시지

---

### 👤 사용자 (Users)

#### 프로필 조회
- **GET** `/users/profile`
- **Headers**: `Authorization: Bearer <token>`
- **Response**: 사용자 프로필 정보

#### 프로필 업데이트
- **PUT** `/users/profile`
- **Headers**: `Authorization: Bearer <token>`
- **Body**: `{ "name": "string", "japanese_level": "string", "bio": "string" }`

#### 학습 통계 조회
- **GET** `/users/stats`
- **Headers**: `Authorization: Bearer <token>`
- **Response**: 
```json
{
  "total_listening_time": 120,
  "words_learned": 45,
  "scripts_completed": 3,
  "current_streak": 5,
  "level_progress": 23.5
}
```

#### 사용자 설정 조회/업데이트
- **GET** `/users/preferences`
- **PUT** `/users/preferences`
- **Headers**: `Authorization: Bearer <token>`

---

### 📜 스크립트 (Scripts)

#### 스크립트 목록 조회
- **GET** `/scripts/`
- **Query Parameters**: 
  - `category`: 카테고리 필터
  - `difficulty`: 난이도 필터  
  - `limit`: 결과 개수 (기본: 20)
  - `offset`: 오프셋 (기본: 0)

#### 특정 스크립트 조회
- **GET** `/scripts/{script_id}`
- **Response**: 스크립트 상세 정보 + 모든 문장

#### 스크립트 문장 목록
- **GET** `/scripts/{script_id}/sentences`
- **Response**: 타임스탬프가 포함된 문장 목록

#### 재생 진행률 업데이트
- **POST** `/scripts/{script_id}/progress`
- **Headers**: `Authorization: Bearer <token>`
- **Body**: 
```json
{
  "script_id": "script_1",
  "current_time": 45.5,
  "completed_sentences": ["sent_1", "sent_2"],
  "last_played": "2024-01-01T12:00:00Z"
}
```

#### 북마크 추가/제거
- **POST** `/scripts/{script_id}/bookmark`
- **DELETE** `/scripts/{script_id}/bookmark`
- **Headers**: `Authorization: Bearer <token>`

---

### 📚 단어 (Words)

#### 단어 검색
- **GET** `/words/search?q={검색어}&limit=20`
- **Response**: 단어 검색 결과 (뜻, 예문 포함)

#### 단어장 조회
- **GET** `/words/vocabulary`
- **Headers**: `Authorization: Bearer <token>`
- **Query Parameters**:
  - `tags`: 태그 필터
  - `mastery_level`: 숙련도 필터 (0-5)
  - `limit`: 결과 개수 (기본: 50)

#### 단어장에 단어 추가
- **POST** `/words/vocabulary`
- **Headers**: `Authorization: Bearer <token>`
- **Body**: 
```json
{
  "word_text": "天気",
  "tags": ["날씨", "기본단어"],
  "notes": "뉴스에서 자주 나오는 단어"
}
```

#### 단어 정보 업데이트
- **PUT** `/words/vocabulary/{word_id}`
- **Headers**: `Authorization: Bearer <token>`
- **Body**: 
```json
{
  "mastery_level": 3,
  "tags": ["날씨", "필수단어"],
  "notes": "완전히 외웠음"
}
```

#### 복습할 단어 목록
- **GET** `/words/review?count=10&mode=mixed`
- **Headers**: `Authorization: Bearer <token>`
- **Response**: 복습이 필요한 단어들

#### 복습 결과 제출
- **POST** `/words/review/{word_id}/result`
- **Headers**: `Authorization: Bearer <token>`
- **Body**: 
```json
{
  "correct": true,
  "response_time": 2.5
}
```

#### 단어장 통계
- **GET** `/words/stats`
- **Headers**: `Authorization: Bearer <token>`
- **Response**: 총 단어 수, 숙련도 분포, 복습 통계

---

## 📊 상태 코드

| 코드 | 설명 |
|------|------|
| 200 | 성공 |
| 201 | 생성됨 |
| 400 | 잘못된 요청 |
| 401 | 인증 필요 |
| 403 | 권한 없음 |
| 404 | 찾을 수 없음 |
| 422 | 유효성 검사 실패 |
| 500 | 서버 오류 |

## 🚨 오류 응답 형식

```json
{
  "detail": "오류 메시지",
  "code": "ERROR_CODE",
  "path": "/api/v1/endpoint",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 🔍 데이터 모델

### 사용자 (User)
```json
{
  "id": "string",
  "email": "string", 
  "name": "string",
  "japanese_level": "beginner|intermediate|advanced",
  "created_at": "datetime",
  "last_login": "datetime"
}
```

### 스크립트 (Script)
```json
{
  "id": "string",
  "title": "string",
  "description": "string", 
  "audio_url": "string",
  "duration": "integer",
  "difficulty_level": "string",
  "category": "string",
  "sentences": ["Sentence"]
}
```

### 문장 (Sentence)
```json
{
  "id": "string",
  "text": "string",
  "reading": "string",
  "translation": "string", 
  "start_time": "float",
  "end_time": "float",
  "difficulty_level": "string"
}
```

### 단어 (Word)
```json
{
  "id": "string",
  "text": "string",
  "reading": "string",
  "meaning": "string",
  "part_of_speech": "string",
  "example_sentence": "string",
  "example_translation": "string"
}
```

## 🔧 개발 도구

### API 문서 접속
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 헬스체크
- **엔드포인트**: `GET /health`
- **용도**: 서비스 상태 확인, Docker 헬스체크

### 예제 요청 (cURL)

#### 로그인
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password"}'
```

#### 스크립트 목록 조회
```bash
curl -X GET "http://localhost:8000/api/v1/scripts/?category=news&limit=10"
```

#### 단어 검색
```bash
curl -X GET "http://localhost:8000/api/v1/words/search?q=天気"
```

---

## 📞 지원

- **GitHub Issues**: https://github.com/your-org/kiko-vooster/issues
- **API 상태**: http://status.kiko-app.com
- **개발자 문서**: https://docs.kiko-app.com 