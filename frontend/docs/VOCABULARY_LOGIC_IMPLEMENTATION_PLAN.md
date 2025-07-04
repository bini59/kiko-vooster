# 단어장 로직 구현 계획서

## 📋 개요

**프로젝트**: Kiko Vooster - 일본어 학습 플랫폼  
**작업**: T-010 단어장 UI 로직 및 복습 기능 구현  
**계획 수립일**: 2025년 1월 7일  
**담당**: Claude Sonnet (AI Agent)

---

## 🔍 코드베이스 분석 결과

### ✅ 이미 완료된 부분

#### 백엔드 API (100% 완료)
- **API 엔드포인트**: 모든 필요한 REST API 구현됨
  - `/words/search` - 단어 검색 (JMdict 연동)
  - `/vocabulary/list` - 사용자 단어장 조회
  - `/vocabulary/add` - 단어장에 단어 추가
  - `/vocabulary/{word_id}` - 단어 정보 업데이트/삭제
  - `/vocabulary/stats` - 단어장 통계
  - `/review/words` - 복습할 단어 목록
  - `/review/result` - 복습 결과 제출
- **서비스 레이어**: WordService, VocabularyService, ReviewService 완전 구현
- **데이터 검증**: Pydantic 모델 기반 입출력 검증
- **인증/권한**: JWT Bearer 토큰 기반 보안
- **에러 처리**: 포괄적인 예외 처리 및 로깅

#### 프론트엔드 UI (100% 완료)
- **컴포넌트**: 모든 UI 컴포넌트 완성 (T-009 완료)
  - WordCard, WordDetailModal, WordSearchBar
  - VocabularyList, ReviewSession, FlashcardMode 등
- **타입 시스템**: 완전한 TypeScript 타입 정의 (45개 인터페이스/enum)
- **스타일링**: DaisyUI/TailwindCSS 기반 일관된 디자인
- **접근성**: WCAG 2.1 AA 기준 준수

#### 인프라스트럭처 (구조 완료)
- **API 클라이언트**: 재시도, 인증, 에러 처리 로직 완성
- **상태 관리**: Svelte stores 기본 구조 설정
- **라우팅**: 페이지 구조 및 네비게이션 완성

### ❌ 구현 필요한 부분

#### 1. API 연동 로직 (vocabularyStore)
- **현재 상태**: 기본 구조만 있음, 실제 API 호출 구현 필요
- **필요 작업**: 모든 CRUD 동작의 실제 백엔드 연결

#### 2. 복습 기능 로직
- **현재 상태**: UI는 완성, 실제 세션 관리 로직 필요
- **필요 작업**: 복습 진행/결과 저장/통계 업데이트

---

## 🎯 구현 계획

### Phase 1: 단어장 기본 CRUD 로직 (T-010-002)

#### 1.1 vocabularyStore 실제 API 연동
**목표**: 모든 단어장 관련 액션이 실제 백엔드와 연동되도록 구현

**구현할 함수들:**
```typescript
// 이미 구조는 있지만 실제 API 호출 로직 구현 필요
- loadUserWords() - GET /vocabulary/list
- searchWords() - GET /words/search 
- addWord() - POST /vocabulary/add
- updateWord() - PUT /vocabulary/{word_id}
- removeWord() - DELETE /vocabulary/{word_id}
- loadStats() - GET /vocabulary/stats
```

**에러 처리 전략:**
- 네트워크 에러: 자동 재시도 + 사용자 알림
- 인증 에러: 토큰 갱신 시도 + 로그인 페이지 리다이렉트
- 비즈니스 에러: 사용자 친화적 메시지 표시
- 낙관적 업데이트: UI 먼저 업데이트, 실패 시 롤백

#### 1.2 상태 동기화 로직
**목표**: UI 상태와 서버 상태의 일관성 보장

**구현 사항:**
- 페이지네이션과 필터링의 서버 사이드 처리
- 실시간 검색 디바운싱
- 로딩 상태 적절한 표시
- 에러 상태 복구 메커니즘

#### 1.3 단어 상세 팝업 연동
**목표**: WordDetailModal의 모든 기능 동작

**구현 사항:**
- 단어 정보 실시간 로드
- 편집/삭제 기능 백엔드 연동
- 태그 자동완성 (기존 태그 목록 활용)
- 숙련도 업데이트 즉시 반영

### Phase 2: 복습 모드 로직 구현 (T-010-003)

#### 2.1 복습 세션 관리
**목표**: ReviewSession 컴포넌트의 실제 복습 로직 구현

**구현할 기능들:**
```typescript
// reviewSession store 실제 로직
- startReview() - GET /review/words → 복습 단어 로드
- submitAnswer() - 답안 검증 및 기록
- nextWord() - 다음 단어로 진행
- endReview() - POST /review/result → 결과 서버 저장
```

**복습 모드별 로직:**
- **FlashcardMode**: 앞면/뒷면 전환, 난이도 평가
- **FillInBlanksMode**: 빈칸 자동 생성, 답안 검증
- **SpellingMode**: 히라가나/가타가나/한자 입력 검증

#### 2.2 진행도 및 결과 처리
**목표**: 복습 진행 상황 실시간 표시 및 결과 저장

**구현 사항:**
- 실시간 정답률/응답시간 계산
- 틀린 단어 재복습 큐 관리
- 복습 완료 후 통계 업데이트
- 숙련도 자동 조정 알고리즘

#### 2.3 복습 설정 관리
**목표**: 사용자 맞춤형 복습 경험 제공

**구현 사항:**
- 복습 모드/시간제한/힌트 설정 저장
- 복습 단어 필터링 (숙련도별, 태그별)
- 학습 통계 기반 개인화 추천

---

## 🔧 기술적 구현 세부사항

### 상태 관리 패턴

#### Store 구조 최적화
```typescript
// vocabularyStore.ts - 실제 구현 패턴
export const vocabularyActions = {
  // 낙관적 업데이트 패턴
  async addWord(wordText: string, tags: string[]) {
    // 1. UI 즉시 업데이트
    vocabularyState.update(state => ({
      ...state,
      userWords: [...state.userWords, optimisticWord],
      loading: false
    }));
    
    try {
      // 2. 서버 요청
      const result = await vocabularyApi.addWord(wordText, tags);
      
      // 3. 성공 시 실제 데이터로 교체
      vocabularyState.update(state => ({
        ...state,
        userWords: state.userWords.map(w => 
          w.id === optimisticWord.id ? result.word : w
        )
      }));
    } catch (error) {
      // 4. 실패 시 롤백
      vocabularyState.update(state => ({
        ...state,
        userWords: state.userWords.filter(w => w.id !== optimisticWord.id),
        error: error.message
      }));
    }
  }
};
```

#### API 호출 패턴
```typescript
// 통일된 에러 처리 및 로딩 상태 관리
async function withLoading<T>(
  operation: () => Promise<T>,
  loadingKey: keyof VocabularyState = 'loading'
): Promise<T> {
  vocabularyState.update(state => ({ ...state, [loadingKey]: true, error: null }));
  
  try {
    const result = await operation();
    vocabularyState.update(state => ({ ...state, [loadingKey]: false }));
    return result;
  } catch (error) {
    vocabularyState.update(state => ({ 
      ...state, 
      [loadingKey]: false, 
      error: error.message 
    }));
    throw error;
  }
}
```

### 복습 로직 알고리즘

#### 스페이싱 반복 알고리즘 (Spaced Repetition)
```typescript
// 숙련도 기반 다음 복습 일정 계산
function calculateNextReview(
  masteryLevel: number, 
  correct: boolean, 
  responseTime: number
): Date {
  const baseIntervals = [1, 3, 7, 14, 30, 90]; // 일 단위
  let nextLevel = correct ? 
    Math.min(masteryLevel + 1, 5) : 
    Math.max(masteryLevel - 1, 0);
    
  // 응답 시간 보정 (빠른 답변 = 숙련도 높음)
  if (responseTime < 2000 && correct) nextLevel = Math.min(nextLevel + 1, 5);
  if (responseTime > 10000) nextLevel = Math.max(nextLevel - 1, 0);
  
  const intervalDays = baseIntervals[nextLevel];
  return new Date(Date.now() + intervalDays * 24 * 60 * 60 * 1000);
}
```

#### 복습 단어 선별 로직
```typescript
// 복습 우선순위 결정
function selectReviewWords(
  allWords: UserWord[], 
  count: number, 
  mode: ReviewMode
): UserWord[] {
  const now = new Date();
  
  // 1. 복습 예정 단어 (nextReview 지난 것들)
  const dueWords = allWords.filter(w => 
    w.nextReview && new Date(w.nextReview) <= now
  );
  
  // 2. 새 단어 (reviewCount === 0)
  const newWords = allWords.filter(w => w.reviewCount === 0);
  
  // 3. 어려운 단어 (masteryLevel < 3)
  const difficultWords = allWords.filter(w => w.masteryLevel < 3);
  
  // 모드별 선별 전략
  switch (mode) {
    case ReviewMode.NEW: return newWords.slice(0, count);
    case ReviewMode.REVIEW: return dueWords.slice(0, count);
    case ReviewMode.MIXED: 
      return [...dueWords, ...newWords, ...difficultWords]
        .slice(0, count);
  }
}
```

---

## 🗂️ 파일별 구현 계획

### 수정할 파일들

#### 1. `frontend/src/lib/stores/vocabularyStore.ts`
**작업**: 실제 API 호출 로직 구현
- `loadUserWords()` - 페이지네이션/필터링 포함
- `searchWords()` - 디바운싱 및 결과 캐싱
- `addWord()` - 낙관적 업데이트
- `updateWord()` - 즉시 UI 반영
- `removeWord()` - 확인 후 삭제

#### 2. `frontend/src/lib/api/vocabulary.ts`
**작업**: API 요청 실제 구현
- 기존 인터페이스는 완성, 실제 HTTP 요청 로직 추가
- 에러 처리 및 재시도 로직 추가

#### 3. `frontend/src/lib/components/vocabulary/review/`
**작업**: 복습 모드 실제 로직 연결
- `ReviewSession.svelte` - 세션 관리 로직
- `FlashcardMode.svelte` - 답안 검증 로직
- `FillInBlanksMode.svelte` - 빈칸 생성/검증
- `SpellingMode.svelte` - 입력 검증 로직

#### 4. `frontend/src/routes/vocabulary/+page.svelte`
**작업**: 메인 페이지 상태 연결
- 실제 데이터 로드 및 표시
- 에러/로딩 상태 적절한 처리

### 새로 만들 파일들

#### 1. `frontend/src/lib/utils/vocabulary.ts`
**목적**: 단어장 관련 유틸리티 함수
```typescript
// 복습 알고리즘, 검증 함수, 포맷팅 등
export function calculateNextReview(...)
export function validateJapaneseInput(...)
export function formatMasteryLevel(...)
```

#### 2. `frontend/src/lib/utils/reviewAlgorithm.ts`
**목적**: 복습 스페이싱 알고리즘
```typescript
// 스페이싱 반복, 우선순위 계산 등
export class SpacedRepetitionEngine { ... }
```

---

## ⚠️ 위험 요소 및 대응책

### 기술적 위험

#### 1. API 응답 지연
**위험**: 단어 검색이나 복습 로딩이 느릴 수 있음
**대응**: 
- 검색어 디바운싱 (300ms)
- 결과 캐싱 (5분 TTL)
- 스켈레톤 UI로 로딩 상태 표시

#### 2. 오프라인 상황
**위험**: 네트워크 연결이 끊어진 경우
**대응**:
- IndexedDB를 활용한 오프라인 캐시
- 동기화 큐 시스템 구현
- 오프라인 상태 표시

#### 3. 복습 세션 중단
**위험**: 브라우저 새로고침으로 복습 진행 상황 손실
**대응**:
- 세션 상태를 localStorage에 주기적 저장
- 페이지 재로드 시 복구 메커니즘
- beforeunload 이벤트로 경고

### UX 위험

#### 1. 복습 피로도
**위험**: 긴 복습 세션으로 인한 사용자 피로
**대응**:
- 기본 복습 단어 수 제한 (10개)
- 진행도 표시로 동기부여
- 휴식 권장 알림

#### 2. 데이터 손실 우려
**위험**: 사용자가 단어장 삭제 등을 실수할 가능성
**대응**:
- 삭제 전 확인 모달
- 실행 취소 기능 (토스트 알림)
- 중요 작업 이후 성공 피드백

---

## 📊 성공 기준

### 기능적 완성도
- [ ] 모든 CRUD 작업 정상 동작 (100%)
- [ ] 복습 모드 3종 모두 완전 구현 (100%)  
- [ ] 에러 상황 적절한 처리 (100%)
- [ ] 오프라인 기본 대응 (80%)

### 성능 지표
- [ ] 단어 검색 응답 시간 < 500ms
- [ ] 페이지 전환 지연 < 200ms
- [ ] 복습 세션 시작 시간 < 1s
- [ ] API 에러율 < 1%

### 사용자 경험
- [ ] 직관적인 에러 메시지
- [ ] 적절한 로딩 상태 표시
- [ ] 일관된 피드백 시스템
- [ ] 접근성 기준 유지

---

## 🚀 다음 단계

### T-010-002: 단어장 상태 관리 구현
1. vocabularyStore 실제 API 연동
2. 에러 처리 및 상태 관리 개선  
3. 단어 상세 팝업 완전 동작
4. 검색 및 필터링 최적화

### T-010-003: 복습 기능 로직 구현
1. 복습 세션 관리 시스템
2. 3가지 복습 모드 로직 완성
3. 결과 저장 및 통계 업데이트
4. 스페이싱 반복 알고리즘 적용

---

**완료 확인**: ✅ T-010-001 코드베이스 분석 및 구현 계획 수립 **DONE** 