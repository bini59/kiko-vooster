# 🤝 기여 가이드라인

Kiko 프로젝트에 기여해주셔서 감사합니다! 이 문서는 프로젝트 기여 방법을 안내합니다.

## 📋 기여 방법

### 1. 이슈 생성
- 버그 리포트, 기능 제안, 질문 등은 GitHub Issues를 활용해주세요
- 이슈 템플릿을 따라 명확한 정보를 제공해주세요

### 2. Fork & Clone
```bash
# 1. GitHub에서 Fork
# 2. 로컬로 클론
git clone https://github.com/[your-username]/kiko-vooster.git
cd kiko-vooster

# 3. 원본 저장소를 upstream으로 추가
git remote add upstream https://github.com/[original-owner]/kiko-vooster.git
```

### 3. 개발 환경 설정
```bash
# README.md의 개발 환경 설정 가이드를 따라주세요
# ENV_SETUP.md를 참조하여 환경 변수를 설정해주세요
```

## 🌿 브랜치 전략

### 브랜치 구조
```
main
├── develop
├── feature/[기능명]
├── hotfix/[버그명]
└── release/[버전]
```

### 브랜치 설명
- **`main`**: 프로덕션 배포용 브랜치 (항상 안정 상태 유지)
- **`develop`**: 개발 통합 브랜치 (다음 릴리즈 준비)
- **`feature/*`**: 새로운 기능 개발
- **`hotfix/*`**: 긴급 버그 수정
- **`release/*`**: 릴리즈 준비 (버전 태깅, 최종 테스트)

### 브랜치 네이밍 규칙
```bash
# 기능 개발
feature/auth-login
feature/player-controls
feature/vocabulary-search

# 버그 수정
hotfix/player-sync-issue
hotfix/login-redirect-bug

# 기타 작업
chore/update-dependencies
docs/api-documentation
style/ui-improvements
```

## 🔄 워크플로우

### 1. 기능 개발 워크플로우
```bash
# 1. develop 브랜치에서 최신 코드 가져오기
git checkout develop
git pull upstream develop

# 2. 기능 브랜치 생성
git checkout -b feature/new-feature

# 3. 개발 진행
# ... 코딩 ...

# 4. 커밋 (conventional commits 규칙 준수)
git add .
git commit -m "feat: add user authentication"

# 5. 테스트 실행 및 확인
npm test  # 또는 pytest

# 6. 푸시
git push origin feature/new-feature

# 7. Pull Request 생성
# GitHub에서 PR 생성하여 develop 브랜치로 머지 요청
```

### 2. 핫픽스 워크플로우
```bash
# 1. main 브랜치에서 핫픽스 브랜치 생성
git checkout main
git checkout -b hotfix/critical-bug

# 2. 버그 수정
# ... 수정 ...

# 3. 테스트 및 커밋
git commit -m "fix: resolve critical login bug"

# 4. main과 develop 양쪽에 머지
git checkout main
git merge hotfix/critical-bug
git checkout develop
git merge hotfix/critical-bug

# 5. 태그 생성 (버전 업)
git tag -a v1.0.1 -m "Hotfix v1.0.1"
```

## 📝 커밋 규칙

### Conventional Commits 사용
```bash
<타입>(<범위>): <설명>

[선택적 본문]

[선택적 푸터]
```

### 커밋 타입
- **`feat`**: 새로운 기능 추가
- **`fix`**: 버그 수정
- **`docs`**: 문서 변경
- **`style`**: 코드 포맷팅, 세미콜론 누락 등 (로직 변경 없음)
- **`refactor`**: 코드 리팩토링 (기능 변경 없음)
- **`test`**: 테스트 코드 추가/수정
- **`chore`**: 빌드 프로세스, 도구 설정 등

### 커밋 메시지 예시
```bash
feat(auth): add Google OAuth login
fix(player): resolve audio sync timing issue
docs(readme): update installation instructions
style(components): apply prettier formatting
refactor(api): optimize database queries
test(auth): add unit tests for login service
chore(deps): update dependencies to latest versions
```

## 🧪 테스트 가이드라인

### 테스트 커버리지
- 새로운 기능에는 반드시 테스트 코드 추가
- 버그 수정 시 회귀 테스트 추가
- 목표 커버리지: 80% 이상

### Frontend 테스트
```bash
cd frontend
pnpm test                # 단위 테스트
pnpm test:e2e           # E2E 테스트
pnpm test:coverage      # 커버리지 리포트
```

### Backend 테스트
```bash
cd backend
pytest                  # 단위 테스트
pytest --cov           # 커버리지 포함
pytest -v              # 상세 출력
```

## 📋 코드 리뷰 가이드라인

### PR 요구사항
- [ ] 명확한 PR 제목과 설명
- [ ] 관련 이슈 번호 연결 (#123)
- [ ] 테스트 코드 포함
- [ ] CI/CD 통과
- [ ] 최소 1명의 승인

### 코드 리뷰 체크리스트
- [ ] 코드가 프로젝트 스타일 가이드를 준수하는가?
- [ ] 보안 취약점이 없는가?
- [ ] 성능에 영향을 주는 변경사항은 없는가?
- [ ] 테스트가 충분한가?
- [ ] 문서 업데이트가 필요한가?

### 리뷰어 가이드라인
- **건설적인 피드백**: 개선점을 제안할 때는 구체적인 대안 제시
- **빠른 리뷰**: 24시간 내 첫 리뷰 권장
- **칭찬도 중요**: 좋은 코드나 접근법에 대한 긍정적 피드백

## 🎯 코드 스타일

### TypeScript/JavaScript
```typescript
// ✅ 좋은 예시
interface User {
  id: string;
  name: string;
  email: string;
}

const createUser = async (userData: User): Promise<User> => {
  // 명확한 타입 정의와 async/await 사용
  return await userService.create(userData);
};

// ❌ 나쁜 예시
const createUser = (userData) => {
  // 타입 정의 없음, 명확하지 않은 반환값
  return userService.create(userData);
};
```

### Python
```python
# ✅ 좋은 예시
from typing import Optional
from pydantic import BaseModel

class User(BaseModel):
    id: str
    name: str
    email: str

async def create_user(user_data: User) -> Optional[User]:
    """사용자를 생성합니다."""
    try:
        return await user_service.create(user_data)
    except Exception as e:
        logger.error(f"User creation failed: {e}")
        return None

# ❌ 나쁜 예시
def create_user(user_data):
    return user_service.create(user_data)
```

### 파일 구조
```
# ✅ 도메인별 구조
src/lib/auth/
├── components/
├── stores/
├── services/
└── types/

# ❌ 타입별 구조 (지양)
src/
├── components/
├── stores/
├── services/
└── types/
```

## 🚀 성능 가이드라인

### Frontend
- 컴포넌트 lazy loading 활용
- 이미지 최적화 (WebP, 적절한 크기)
- Bundle size 모니터링
- Core Web Vitals 준수

### Backend
- 데이터베이스 쿼리 최적화
- 캐싱 전략 활용
- 적절한 인덱스 사용
- N+1 쿼리 방지

## 🔐 보안 가이드라인

### 일반 사항
- 환경 변수로 민감 정보 관리
- 입력값 검증 및 필터링
- HTTPS 강제 사용
- CORS 적절히 설정

### Frontend
- XSS 방지를 위한 입력값 이스케이프
- CSP (Content Security Policy) 적용
- 민감 정보 클라이언트 저장 금지

### Backend
- SQL Injection 방지
- JWT 토큰 적절한 만료 시간 설정
- Rate limiting 적용
- 적절한 로깅 (민감 정보 제외)

## 📚 문서화

### 필수 문서화 항목
- [ ] API 엔드포인트 (OpenAPI/Swagger)
- [ ] 컴포넌트 props 및 사용법
- [ ] 복잡한 비즈니스 로직
- [ ] 환경 설정 및 배포 가이드

### 문서 작성 가이드라인
- 명확하고 간결한 설명
- 코드 예시 포함
- 최신 정보 유지
- 한국어 우선, 영어 병기

## 🆘 도움이 필요할 때

### 질문하기 전에
1. README.md와 관련 문서를 먼저 확인
2. 기존 이슈에서 유사한 문제 검색
3. 에러 메시지와 재현 단계 정리

### 질문 방법
- **GitHub Issues**: 버그 리포트, 기능 제안
- **GitHub Discussions**: 일반적인 질문, 아이디어 공유
- **PR Comments**: 코드 리뷰 관련 질문

## 🎉 기여자 인정

- 모든 기여자는 README.md의 Contributors 섹션에 추가됩니다
- 특별한 기여에 대해서는 릴리즈 노트에서 언급됩니다
- 정기적인 기여자에게는 maintainer 권한을 부여할 수 있습니다

---

다시 한 번 기여해주셔서 감사합니다! 🙏
질문이 있으시면 언제든지 이슈를 생성하거나 논의 게시판을 활용해주세요. 