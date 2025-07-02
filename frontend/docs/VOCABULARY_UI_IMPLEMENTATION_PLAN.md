# 단어장 UI 구현 계획서

## 1. 코드베이스 분석 결과

### 기존 패턴 분석
- **타입 시스템**: TypeScript 강타입, interface 기반 모델링
- **상태 관리**: Svelte stores (writable, derived) + actions 패턴
- **스타일링**: DaisyUI + TailwindCSS, 모바일 우선 반응형
- **접근성**: ARIA 속성, 키보드 내비게이션, 스크린 리더 지원
- **API**: 중앙화된 클라이언트, 재시도 로직, 인증 토큰 관리

### 기존 컴포넌트 구조
```
components/
├── common/          # 공통 UI (NotificationContainer 등)
├── auth/           # 인증 관련 컴포넌트
├── sync/           # 스크립트-오디오 싱크 관련
└── audio/          # 오디오 플레이어 컨트롤
```

## 2. 단어장 UI 아키텍처 설계

### 2.1 컴포넌트 구조
```
components/vocabulary/
├── core/
│   ├── WordCard.svelte           # 단어 카드 (기본 표시 단위)
│   ├── WordDetailModal.svelte    # 단어 상세 정보 모달
│   ├── WordSearchBar.svelte      # 단어 검색 인터페이스
│   └── TagSelector.svelte        # 태그 선택/관리
├── lists/
│   ├── VocabularyList.svelte     # 사용자 단어장 리스트
│   ├── SearchResults.svelte      # 검색 결과 리스트
│   └── WordPagination.svelte     # 페이지네이션
├── review/
│   ├── ReviewModeSelector.svelte # 복습 모드 선택 (플래시카드/빈칸/철자)
│   ├── FlashcardMode.svelte     # 플래시카드 복습
│   ├── FillInBlanksMode.svelte  # 빈칸 채우기
│   ├── SpellingGameMode.svelte  # 철자 게임
│   └── ReviewProgress.svelte     # 복습 진행도
├── stats/
│   ├── VocabularyStats.svelte   # 단어장 통계
│   └── ReviewStats.svelte       # 복습 통계
└── common/
    ├── MasteryLevel.svelte      # 숙련도 표시/조절
    ├── WordTags.svelte          # 단어 태그 표시
    └── LoadingSpinner.svelte    # 로딩 인디케이터
```

### 2.2 데이터 타입 정의
```typescript
// frontend/src/lib/types/vocabulary.ts
export interface Word {
  id: string;
  text: string;
  reading?: string;
  meaning: string;
  partOfSpeech: PartOfSpeech;
  difficultyLevel: DifficultyLevel;
  exampleSentence?: string;
  exampleTranslation?: string;
  audioUrl?: string;
  createdAt: string;
  updatedAt: string;
}

export interface UserWord {
  id: string;
  userId: string;
  wordId: string;
  word?: Word;
  masteryLevel: number; // 0-5
  reviewCount: number;
  tags: string[];
  notes?: string;
  addedAt: string;
  lastReviewed?: string;
  nextReview?: string;
  updatedAt: string;
}

export interface VocabularyState {
  userWords: UserWord[];
  searchResults: Word[];
  currentFilter: VocabularyFilter;
  currentPage: number;
  totalPages: number;
  loading: boolean;
  error: string | null;
}

export interface ReviewSession {
  id: string;
  mode: ReviewMode;
  words: UserWord[];
  currentIndex: number;
  correctAnswers: number;
  totalAnswers: number;
  startTime: string;
}
```

### 2.3 상태 관리 설계
```typescript
// frontend/src/lib/stores/vocabularyStore.ts
export const vocabularyState = writable<VocabularyState>(initialState);
export const reviewSession = writable<ReviewSession | null>(null);

// 유도 스토어
export const filteredWords = derived(
  [vocabularyState],
  ([$state]) => applyFilters($state.userWords, $state.currentFilter)
);

export const reviewProgress = derived(
  [reviewSession],
  ([$session]) => $session ? calculateProgress($session) : null
);

// 액션
export const vocabularyActions = {
  loadUserWords,
  searchWords,
  addWord,
  updateWord,
  removeWord,
  updateMasteryLevel,
  // ... 기타 액션들
};
```

## 3. 구현 로드맵

### Phase 1: 기본 단어장 UI (T-009-002)
**목표**: 단어 리스트, 검색, 상세 보기, 저장 기능

**구현 순서**:
1. 단어장 타입 정의 (`vocabulary.ts`)
2. 단어장 스토어 구현 (`vocabularyStore.ts`)
3. 단어장 API 서비스 (`vocabularyApi.ts`)
4. 기본 컴포넌트:
   - `WordCard.svelte`: 단어 카드 UI
   - `WordDetailModal.svelte`: 단어 상세/편집 모달
   - `VocabularyList.svelte`: 단어장 리스트 컨테이너
   - `WordSearchBar.svelte`: 검색 인터페이스

**검증 기준**:
- [ ] 단어 리스트 정상 표시
- [ ] 단어 검색 및 필터링 동작
- [ ] 단어 추가/편집/삭제 가능
- [ ] 반응형 및 접근성 준수

### Phase 2: 복습 모드 UI (T-009-003)
**목표**: 플래시카드, 빈칸 채우기, 철자 게임 모드

**구현 순서**:
1. 복습 관련 타입 정의
2. 복습 세션 스토어 구현
3. 복습 모드 컴포넌트:
   - `ReviewModeSelector.svelte`: 모드 선택
   - `FlashcardMode.svelte`: 플래시카드 게임
   - `FillInBlanksMode.svelte`: 빈칸 채우기
   - `SpellingGameMode.svelte`: 철자 맞추기
   - `ReviewProgress.svelte`: 진행도 표시

**검증 기준**:
- [ ] 각 복습 모드 정상 동작
- [ ] 게임 로직 및 스코어링 정확
- [ ] 키보드 입력 및 접근성 지원
- [ ] 복습 결과 저장 및 진행도 추적

### Phase 3: 통합 및 최적화 (T-009-004)
**목표**: 전체 UI 통합, 성능 최적화, 품질 검증

**구현 순서**:
1. 단어장/복습 모드 간 연동
2. 단어장 통계 및 분석 UI
3. 성능 최적화 (가상화, 지연 로딩)
4. 접근성 검증 및 개선
5. 크로스 브라우저 테스트

## 4. 주요 기술적 고려사항

### 4.1 성능 최적화
- **가상 스크롤링**: 대량 단어 리스트 처리
- **지연 로딩**: 단어 상세 정보 및 오디오
- **캐싱**: API 응답 및 복습 세션 상태
- **디바운싱**: 검색 입력 최적화

### 4.2 접근성 (WCAG 2.1 AA)
- **키보드 내비게이션**: 모든 인터렉션 키보드 지원
- **스크린 리더**: ARIA 라벨, 역할, 상태 제공
- **컬러 콘트라스트**: 충분한 대비 확보
- **포커스 관리**: 모달/드롭다운 포커스 트래핑

### 4.3 반응형 디자인
- **모바일 우선**: 터치 친화적 인터페이스
- **브레이크포인트**: 768px(태블릿), 1024px(데스크톱)
- **유연한 레이아웃**: Flexbox/Grid 활용
- **터치 타겟**: 최소 44px 크기 보장

### 4.4 상태 관리
- **일관성**: 단일 진실의 원천(Single Source of Truth)
- **예측 가능성**: 순수 함수 기반 상태 변경
- **디버깅**: Redux DevTools 호환 로깅
- **지속성**: 중요 상태 로컬 스토리지 저장

## 5. 공통 모듈 및 유틸리티

### 5.1 재사용 가능한 훅
```typescript
// hooks/useVocabulary.ts
export function useVocabulary() {
  // 단어장 관련 로직
}

// hooks/useReview.ts  
export function useReview() {
  // 복습 세션 관리 로직
}

// hooks/useKeyboardShortcuts.ts
export function useKeyboardShortcuts() {
  // 키보드 단축키 처리
}
```

### 5.2 유틸리티 함수
```typescript
// utils/japanese.ts
export function analyzeJapanese(text: string);
export function generateFurigana(text: string);

// utils/srs.ts (Spaced Repetition System)
export function calculateNextReview(masteryLevel: number);
export function updateMasteryLevel(correct: boolean, currentLevel: number);

// utils/gameLogic.ts
export function generateFillInBlanks(sentence: string);
export function checkSpelling(input: string, correct: string);
```

## 6. 위험 요소 및 대응책

### 6.1 기술적 위험
- **대량 데이터 성능**: 가상화 및 페이지네이션으로 대응
- **오디오 로딩 지연**: 프리로딩 및 캐싱 전략
- **메모리 누수**: 컴포넌트 언마운트 시 정리 로직

### 6.2 사용자 경험 위험
- **복잡한 UI**: 단계별 온보딩 및 도움말
- **데이터 손실**: 오프라인 지원 및 자동 저장
- **접근성 부족**: 전문가 리뷰 및 자동화 테스트

### 6.3 일정 위험
- **기능 범위 확대**: MVP 기능에 집중, 점진적 개선
- **기술 부채**: 코드 리뷰 및 리팩토링 시간 확보
- **통합 이슈**: 조기 통합 테스트 및 CI/CD 파이프라인

## 7. 성공 지표

### 7.1 기능적 지표
- [ ] 모든 단어장 기능 정상 동작
- [ ] 3가지 복습 모드 구현 완료
- [ ] 반응형 UI (모바일/태블릿/데스크톱)
- [ ] 접근성 검사 100% 통과

### 7.2 성능 지표
- [ ] 초기 로딩 시간 < 2.5초
- [ ] 단어 검색 응답 시간 < 300ms
- [ ] 복습 모드 전환 시간 < 200ms
- [ ] 메모리 사용량 < 50MB

### 7.3 품질 지표
- [ ] TypeScript 에러 0개
- [ ] ESLint 경고 0개
- [ ] 접근성 오류 0개
- [ ] 크로스 브라우저 호환성 확인

---

이 계획서는 단어장 UI 구현의 전체적인 방향성과 구체적인 실행 방안을 제시합니다. 각 Phase별로 점진적으로 구현하여 위험을 최소화하고, 기존 코드베이스의 패턴을 최대한 활용하여 일관성을 유지합니다. 