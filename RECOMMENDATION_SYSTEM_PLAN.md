# 📻 추천 라디오/애니 OST 리스트 시스템 구현 계획

**태스크**: T-016 추천 라디오/애니 OST 리스트 기능  
**서브태스크**: T-016-001 코드베이스 분석 및 구현 계획 수립  
**날짜**: 2024-01-XX  

---

## 1. 🔍 기존 코드베이스 분석

### 1.1 활용 가능한 기존 구조

#### **데이터베이스 레이어**
- ✅ `scripts` 테이블: `category`, `difficulty_level`, `metadata` 필드 보유
- ✅ `users` 테이블: `japanese_level`, `preferences` JSONB 필드
- ✅ `user_scripts_progress`: 학습 이력 추적
- ✅ `bookmarks`: 사용자 선호도 데이터
- ✅ `user_words`: 단어 학습 레벨 분석 가능

#### **서비스 패턴**
- ✅ **도메인별 서비스**: `WordService`, `VocabularyService`, `UserService`
- ✅ **외부 API 연동**: `JMdictService` 패턴으로 캐싱 + 재시도 로직 완비
- ✅ **데이터베이스 매니저**: `DatabaseManager` 통합 데이터 접근
- ✅ **FastAPI 라우터**: `/api/v1/` 버전 관리 체계

#### **프론트엔드 패턴**
- ✅ **Svelte Stores**: 상태 관리 패턴 확립
- ✅ **컴포넌트 모듈화**: `lib/components/<domain>/` 구조
- ✅ **API 연동**: 기존 fetch 패턴 재사용 가능

---

## 2. 🎯 추천 시스템 설계

### 2.1 추천 알고리즘 전략

#### **A. 개인화 추천 (70% 가중치)**
```typescript
interface PersonalizedRecommendation {
  userLevel: 'beginner' | 'intermediate' | 'advanced';
  learningHistory: {
    completedCategories: string[];
    preferredDifficulty: string;
    averageSessionTime: number;
  };
  vocabularyProgress: {
    masteredWords: number;
    currentLevel: number;
  };
}
```

#### **B. 콘텐츠 기반 추천 (20% 가중치)**
```typescript
interface ContentBasedRecommendation {
  similarScripts: {
    category: string;
    difficulty: string;
    duration: number;
    tags: string[];
  };
  trendingContent: {
    popularityScore: number;
    recentEngagement: number;
  };
}
```

#### **C. 협업 필터링 (10% 가중치)**
```typescript
interface CollaborativeRecommendation {
  similarUsers: {
    sharedPreferences: string[];
    commonCompletions: string[];
  };
  communityTrends: {
    mostBookmarked: string[];
    highestRated: string[];
  };
}
```

### 2.2 외부 데이터 소스 통합

#### **라디오 콘텐츠 API**
- **NHK らじる★らじる**: 공개 라디오 프로그램 정보
- **J-WAVE**: 팟캐스트 및 음악 프로그램
- **文化放送**: 애니메/게임 관련 라디오

#### **애니메 OST API**
- **Spotify Web API**: 애니메 플레이리스트 및 OST
- **Apple Music API**: 일본 애니메 차트
- **YouTube Music API**: 인기 애니메 송 트렌드

#### **메타데이터 확장**
```json
{
  "recommendation_metadata": {
    "source": "spotify|apple_music|nhk|jwave",
    "popularity_score": 85,
    "trend_factor": 1.2,
    "similar_content_ids": ["uuid1", "uuid2"],
    "target_audience": ["anime_fans", "jlpt_n3"],
    "seasonal_relevance": "spring_2024",
    "mood_tags": ["upbeat", "nostalgic", "study_friendly"]
  }
}
```

---

## 3. 🏗️ 아키텍처 설계

### 3.1 백엔드 구조

#### **새로운 서비스 모듈**
```plaintext
backend/app/services/recommendation/
├── recommendation_service.py      # 메인 추천 엔진
├── content_aggregator_service.py  # 외부 API 통합
├── user_profile_service.py        # 사용자 프로필 분석
├── trending_service.py            # 트렌드 분석
└── recommendation_cache.py        # 추천 결과 캐싱
```

#### **데이터베이스 확장**
```sql
-- 추천 성능 추적
CREATE TABLE recommendation_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    script_id UUID NOT NULL REFERENCES scripts(id),
    recommendation_type VARCHAR(50), -- 'personalized', 'trending', 'similar'
    interaction_type VARCHAR(20),    -- 'view', 'play', 'bookmark', 'skip'
    recommendation_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 외부 콘텐츠 메타데이터
CREATE TABLE external_content_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name VARCHAR(50) NOT NULL,  -- 'spotify', 'nhk', 'youtube_music'
    external_id VARCHAR(200) NOT NULL,
    content_data JSONB NOT NULL,
    last_synced TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    
    UNIQUE(source_name, external_id)
);

-- 추천 알고리즘 성능 메트릭
CREATE TABLE recommendation_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    algorithm_version VARCHAR(20),
    click_through_rate FLOAT,
    completion_rate FLOAT,
    user_satisfaction_score FLOAT,
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3.2 API 엔드포인트 설계

#### **추천 API 구조**
```python
# backend/app/api/v1/recommendations.py

@router.get("/recommendations/personalized")
async def get_personalized_recommendations(
    user_id: UUID,
    limit: int = 10,
    category: Optional[str] = None,
    difficulty: Optional[str] = None
) -> RecommendationResponse

@router.get("/recommendations/trending") 
async def get_trending_content(
    period: str = "week",  # day, week, month
    limit: int = 20
) -> TrendingResponse

@router.get("/recommendations/similar/{script_id}")
async def get_similar_content(
    script_id: UUID,
    limit: int = 5
) -> SimilarContentResponse

@router.post("/recommendations/feedback")
async def track_recommendation_interaction(
    interaction: RecommendationInteraction
) -> InteractionResponse
```

### 3.3 프론트엔드 구조

#### **새로운 컴포넌트 모듈**
```plaintext
frontend/src/lib/
├── components/recommendation/
│   ├── RecommendationList.svelte      # 추천 리스트 컨테이너
│   ├── RecommendationCard.svelte      # 개별 추천 카드
│   ├── TrendingSection.svelte         # 트렌딩 콘텐츠 섹션
│   ├── PersonalizedSection.svelte     # 개인화 추천 섹션
│   └── RecommendationFilters.svelte   # 필터 및 설정
├── stores/
│   └── recommendationStore.ts         # 추천 상태 관리
└── hooks/
    └── useRecommendations.ts          # 추천 API 훅
```

#### **상태 관리 구조**
```typescript
// frontend/src/lib/stores/recommendationStore.ts
interface RecommendationState {
  personalized: RecommendationItem[];
  trending: RecommendationItem[];
  similar: RecommendationItem[];
  filters: {
    category: string | null;
    difficulty: string | null;
    duration: [number, number] | null;
  };
  loading: {
    personalized: boolean;
    trending: boolean;
    similar: boolean;
  };
  lastUpdated: Record<string, Date>;
}
```

---

## 4. 🔄 구현 단계별 계획

### Phase 1: 기초 인프라 (1주)
1. **데이터베이스 스키마 확장**
   - 추천 관련 테이블 생성
   - 기존 scripts 테이블 메타데이터 확장
   - 인덱스 최적화

2. **백엔드 서비스 기초**
   - `RecommendationService` 기본 클래스
   - `ContentAggregatorService` 외부 API 연동 기초
   - 기본 API 엔드포인트 구현

3. **프론트엔드 컴포넌트 기초**
   - `RecommendationList` 컴포넌트 기본 구조
   - `recommendationStore` 상태 관리
   - API 연동 훅 구현

### Phase 2: 외부 데이터 통합 (1주)
1. **외부 API 연동**
   - Spotify Web API 통합
   - NHK 라디오 API 연동
   - YouTube Music API 연동

2. **데이터 수집 및 정규화**
   - 외부 콘텐츠 메타데이터 수집
   - 데이터 정규화 및 저장
   - 주기적 동기화 크론잡

3. **캐싱 시스템 확장**
   - 외부 API 응답 캐싱
   - 추천 결과 캐싱
   - 캐시 무효화 전략

### Phase 3: 추천 알고리즘 구현 (1-2주)
1. **개인화 추천 엔진**
   - 사용자 프로필 분석
   - 학습 이력 기반 추천
   - 선호도 점수 계산

2. **콘텐츠 기반 추천**
   - 유사 콘텐츠 탐지
   - 카테고리/난이도 매칭
   - 메타데이터 기반 필터링

3. **트렌드 분석**
   - 인기도 점수 계산
   - 시간대별 트렌드 분석
   - 계절/이벤트 기반 추천

### Phase 4: UI/UX 완성 (1주)
1. **프론트엔드 UI 완성**
   - 반응형 추천 카드 디자인
   - 필터 및 정렬 옵션
   - 로딩 및 에러 상태 처리

2. **사용자 상호작용**
   - 추천 피드백 수집
   - 즐겨찾기/북마크 통합
   - 개인화 설정 UI

3. **성능 최적화**
   - 무한 스크롤 구현
   - 이미지 lazy loading
   - API 요청 최적화

### Phase 5: 성능 분석 및 최적화 (1주)
1. **추천 성능 분석**
   - A/B 테스트 프레임워크
   - 클릭율/완주율 추적
   - 사용자 만족도 측정

2. **알고리즘 튜닝**
   - 추천 정확도 개선
   - 가중치 조정
   - 신규 사용자 cold start 문제 해결

3. **시스템 최적화**
   - 데이터베이스 쿼리 최적화
   - 캐싱 전략 개선
   - API 응답 시간 최적화

---

## 5. 🎯 성공 지표 및 품질 기준

### 5.1 기능적 요구사항
- ✅ **개인화 추천**: 사용자별 맞춤 콘텐츠 10개 이상 제공
- ✅ **트렌딩 콘텐츠**: 실시간 인기 콘텐츠 20개 이상 제공  
- ✅ **유사 콘텐츠**: 현재 스크립트와 유사한 콘텐츠 5개 이상 제공
- ✅ **필터링**: 카테고리, 난이도, 재생시간별 필터 지원

### 5.2 성능 요구사항
- ✅ **응답 시간**: 추천 API p95 ≤ 300ms
- ✅ **정확도**: 개인화 추천 클릭률 ≥ 15%
- ✅ **만족도**: 사용자 만족도 점수 ≥ 4.0/5.0
- ✅ **캐시 적중률**: ≥ 80% (개인화 추천 제외)

### 5.3 비즈니스 지표
- ✅ **사용자 참여**: 추천 콘텐츠 재생율 ≥ 25%
- ✅ **학습 지속성**: 추천 통해 학습 세션 30% 증가
- ✅ **콘텐츠 발견**: 신규 콘텐츠 탐색율 ≥ 40%

---

## 6. 🔧 기술 스택 및 도구

### 6.1 백엔드 기술
- **추천 엔진**: Python scikit-learn (유사도 계산)
- **외부 API**: aiohttp (비동기 HTTP 클라이언트)
- **캐싱**: Redis (추천 결과 캐싱)
- **스케줄링**: APScheduler (데이터 동기화)

### 6.2 프론트엔드 기술
- **상태 관리**: Svelte stores + 커스텀 훅
- **UI 컴포넌트**: DaisyUI + TailwindCSS
- **API 통신**: fetch API + error boundary
- **성능 최적화**: Intersection Observer (무한 스크롤)

### 6.3 외부 서비스
- **Spotify Web API**: 애니메 OST 및 플레이리스트
- **YouTube Music API**: 트렌드 분석 및 인기 차트
- **NHK API**: 라디오 프로그램 정보
- **Last.fm API**: 음악 메타데이터 보강

---

## 7. 📋 다음 단계 (T-016-002)

### T-016-001 완료 후 다음 서브태스크:

1. **T-016-002**: 데이터베이스 스키마 확장 및 마이그레이션
2. **T-016-003**: 외부 API 연동 서비스 구현  
3. **T-016-004**: 추천 알고리즘 엔진 개발
4. **T-016-005**: 프론트엔드 UI 컴포넌트 구현
5. **T-016-006**: 성능 최적화 및 A/B 테스트
6. **T-016-007**: 통합 테스트 및 품질 검증

---

**✅ T-016-001 완료 조건**: 이 구현 계획서 승인 + 기술적 아키텍처 검토 완료 