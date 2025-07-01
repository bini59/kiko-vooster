# 스크립트-오디오 싱크 UI 구현 계획

## 1. 기존 코드베이스 분석 결과

### ✅ 현재 상태

- **프레임워크**: SvelteKit 5.0.0 + TypeScript
- **스타일링**: TailwindCSS 4.1.11 + DaisyUI 5.0.43
- **폰트**: Inter (기본) + Noto Sans JP (일본어)
- **테마**: 라이트/다크 모드 지원
- **구조**: 기본 랜딩 페이지만 구현된 상태

### ✅ 기존 디자인 시스템

```javascript
// 색상 팔레트
primary: "#ff2323" (빨강 계열)
secondary: "#f6d860" (노랑 계열)
accent: "#37cdbe" (청록 계열)

// 폰트
font-sans: Inter (기본)
font-jp: Noto Sans JP (일본어)
```

### ✅ 기존 패턴

- DaisyUI 컴포넌트 활용 (btn, hero, stats, alert, mockup-browser)
- 반응형 클래스 (sm:, lg: 등) 사용
- 애니메이션 (animate-fade-in) 적용
- 의미있는 아이콘과 이모지 활용

## 2. UI/UX 설계 및 요구사항

### 🎯 사용자 스토리 기반 UI 설계

#### 핵심 사용자 스토리

1. **"라디오를 들으며 현재 문장을 하이라이트해 눈으로 따라가기 편했으면 좋겠다"**

   - 실시간 문장 하이라이트 (카라오케 모드)
   - 시각적으로 명확한 활성 상태 표시

2. **"문장을 클릭하면 해당 구간이 바로 재생되길 원한다"**

   - 클릭 가능한 문장 UI
   - 호버/포커스 상태 시각적 피드백

3. **"구간 반복 재생으로 발음·억양을 반복 청취하고 따라 읽을 수 있다"**
   - AB 반복 컨트롤 UI
   - 직관적인 구간 설정 인터페이스

### 🎨 UI 컴포넌트 아키텍처

#### 메인 컨테이너: ScriptAudioSyncUI

```
ScriptAudioSyncUI/
├── AudioPlayerControls/          # 오디오 플레이어 컨트롤
│   ├── PlayPauseButton
│   ├── ProgressBar
│   ├── VolumeControl
│   └── TimeDisplay
├── ScriptPanel/                  # 스크립트 표시 영역
│   ├── SentenceHighlight        # 문장별 하이라이트
│   ├── SentenceClickHandler     # 문장 클릭 처리
│   └── ScrollTracker            # 자동 스크롤
└── ABRepeatControl/             # AB 반복 컨트롤
    ├── SetPointA
    ├── SetPointB
    ├── ClearPoints
    └── RepeatToggle
```

### 📱 반응형 설계

#### 모바일 레이아웃 (< 768px)

```
┌─────────────────────┐
│   Audio Controls    │ ← 고정 상단
├─────────────────────┤
│                     │
│   Script Panel      │ ← 스크롤 가능
│   (세로 중심)        │
│                     │
├─────────────────────┤
│  AB Repeat Control  │ ← 고정 하단
└─────────────────────┘
```

#### 데스크톱 레이아웃 (≥ 768px)

```
┌───────────────────────────────────┐
│        Audio Controls             │ ← 상단 고정
├─────────────────┬─────────────────┤
│                 │                 │
│  Script Panel   │   AB Repeat     │ ← 사이드 패널
│  (메인 영역)     │   Control       │
│                 │   + 설정        │
│                 │                 │
└─────────────────┴─────────────────┘
```

### ♿ 접근성 (WCAG 2.1 AA) 설계

#### 키보드 네비게이션

- **Tab**: 문장 간 이동
- **Enter/Space**: 문장 선택 및 재생
- **Arrow Keys**: 문장별 정밀 이동
- **A/B**: AB 구간 설정 단축키
- **R**: 반복 재생 토글

#### ARIA 라벨링

```html
<!-- 메인 컨테이너 -->
<div role="application" aria-label="스크립트-오디오 싱크 플레이어">
  <!-- 스크립트 영역 -->
  <div role="document" aria-live="polite" aria-label="스크립트 텍스트">
    <!-- 현재 활성 문장 -->
    <p
      role="button"
      aria-current="true"
      aria-label="현재 재생 중인 문장: {문장내용}"
      tabindex="0"
    >
      <!-- AB 반복 컨트롤 -->
    </p>

    <div role="group" aria-label="AB 반복 재생 컨트롤"></div>
  </div>
</div>
```

#### 시각적 접근성

- **고대비 모드**: 다크/라이트 테마별 충분한 색상 대비
- **포커스 표시**: 명확한 포커스 링 및 하이라이트
- **텍스트 크기**: 사용자 조절 가능한 폰트 사이즈
- **모션 감소**: `prefers-reduced-motion` 고려

## 3. 기술적 구현 계획

### 🏗️ 컴포넌트 모듈 구조

```
src/lib/
├── components/
│   ├── audio/
│   │   ├── AudioPlayer.svelte           # 메인 오디오 플레이어
│   │   ├── AudioControls.svelte         # 플레이어 컨트롤
│   │   ├── ProgressBar.svelte           # 진행바
│   │   └── VolumeControl.svelte         # 음량 조절
│   ├── script/
│   │   ├── ScriptPanel.svelte           # 스크립트 패널
│   │   ├── SentenceHighlight.svelte     # 문장 하이라이트
│   │   └── ScrollTracker.svelte         # 자동 스크롤
│   ├── sync/
│   │   ├── ScriptAudioSyncUI.svelte     # 메인 싱크 UI
│   │   ├── ABRepeatControl.svelte       # AB 반복 컨트롤
│   │   └── SyncStatusIndicator.svelte   # 싱크 상태 표시
│   └── common/
│       ├── LoadingSpinner.svelte
│       ├── ErrorBoundary.svelte
│       └── AccessibilityControls.svelte
├── stores/
│   ├── audioStore.ts                    # 오디오 상태 관리
│   ├── scriptStore.ts                   # 스크립트 상태 관리
│   ├── syncStore.ts                     # 싱크 상태 관리
│   └── settingsStore.ts                 # 사용자 설정
├── types/
│   ├── audio.ts                         # 오디오 관련 타입
│   ├── script.ts                        # 스크립트 관련 타입
│   └── sync.ts                          # 싱크 관련 타입
├── utils/
│   ├── audioUtils.ts                    # 오디오 처리 유틸
│   ├── scriptUtils.ts                   # 스크립트 처리 유틸
│   └── accessibilityUtils.ts            # 접근성 유틸
└── api/
    ├── audioAPI.ts                      # 오디오 API 클라이언트
    ├── scriptAPI.ts                     # 스크립트 API 클라이언트
    └── syncAPI.ts                       # 싱크 API 클라이언트
```

### 🔄 상태 관리 설계 (Svelte Stores)

#### 오디오 상태 (audioStore.ts)

```typescript
interface AudioState {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  playbackRate: number;
  buffered: TimeRanges | null;
}
```

#### 스크립트 상태 (scriptStore.ts)

```typescript
interface ScriptState {
  sentences: Sentence[];
  currentSentenceId: string | null;
  highlightedSentences: Set<string>;
  scrollPosition: number;
}
```

#### 싱크 상태 (syncStore.ts)

```typescript
interface SyncState {
  isConnected: boolean;
  abRepeat: {
    pointA: number | null;
    pointB: number | null;
    isActive: boolean;
  };
  mappings: SentenceMapping[];
  editMode: boolean;
}
```

### 🎯 API 연동 인터페이스

#### WebSocket 실시간 동기화

```typescript
// 위치 업데이트 메시지
interface PositionUpdateMessage {
  type: "POSITION_UPDATE";
  currentTime: number;
  sentenceId: string;
  isPlaying: boolean;
}

// 매핑 편집 메시지
interface MappingEditMessage {
  type: "MAPPING_EDIT";
  sentenceId: string;
  startTime: number;
  endTime: number;
}
```

#### REST API 클라이언트

```typescript
class SyncAPIClient {
  // 매핑 조회
  async getScriptMappings(scriptId: string): Promise<SentenceMapping[]>;

  // 매핑 생성/수정
  async updateSentenceMapping(
    data: SentenceMappingUpdate
  ): Promise<SentenceMapping>;

  // AI 자동 정렬
  async autoAlignScript(scriptId: string): Promise<AutoAlignResponse>;
}
```

## 4. 구현 로드맵 및 우선순위

### 🚀 Phase 1: 기본 구조 (T-005-002)

1. **ScriptAudioSyncUI 메인 컨테이너** ⭐⭐⭐

   - 반응형 레이아웃 기본 구조
   - 모바일/데스크톱 레이아웃 분기

2. **SentenceHighlight 컴포넌트** ⭐⭐⭐

   - 문장별 하이라이트 표시
   - 클릭/탭 이벤트 처리
   - 현재 활성 문장 시각적 표시

3. **ABRepeatControl 컴포넌트** ⭐⭐⭐
   - A/B 구간 설정 버튼
   - 반복 재생 토글
   - 구간 삭제 기능

### 🔧 Phase 2: 접근성 및 고급 기능 (T-005-003)

1. **접근성 강화** ⭐⭐

   - ARIA 라벨링 완성
   - 키보드 네비게이션 구현
   - 스크린 리더 최적화

2. **반응형 최적화** ⭐⭐

   - 다양한 화면 크기 테스트
   - 터치 인터페이스 최적화
   - 모바일 성능 최적화

3. **통합 테스트** ⭐
   - 브라우저 호환성 테스트
   - 접근성 자동 검사
   - 사용성 테스트

### 📋 체크리스트별 우선순위

#### 높음 (🔴 Must Have)

- [ ] ScriptAudioSyncUI 메인 컨테이너 마크업
- [ ] SentenceHighlight 기본 기능
- [ ] ABRepeatControl 기본 UI
- [ ] 모바일/PC 반응형 레이아웃
- [ ] 기본 ARIA 라벨링

#### 중간 (🟡 Should Have)

- [ ] 키보드 네비게이션 완성
- [ ] 다크모드 스타일 최적화
- [ ] 애니메이션 및 트랜지션
- [ ] 사용자 설정 연동

#### 낮음 (🟢 Could Have)

- [ ] 고급 접근성 기능
- [ ] 성능 최적화
- [ ] 추가 브라우저 지원
- [ ] A11y 테스트 자동화

## 5. 품질 보증 계획

### 🔍 검증 기준

1. **기능 완성도**: 모든 핵심 UI 요소 정상 동작
2. **접근성**: WCAG 2.1 AA 기준 90% 이상 준수
3. **반응형**: 320px~1920px 모든 해상도 지원
4. **성능**: 초기 렌더링 ≤ 100ms, 인터랙션 ≤ 16ms
5. **브라우저 호환**: Chrome, Safari, Firefox 최신 2버전

### 🧪 테스트 전략

- **유닛 테스트**: 각 컴포넌트별 단위 테스트
- **통합 테스트**: 컴포넌트 간 상호작용 테스트
- **접근성 테스트**: axe-core 자동 검사 + 수동 검사
- **시각적 회귀 테스트**: 스토리북 기반 스냅샷 테스트
- **사용성 테스트**: 실제 사용자 시나리오 기반 테스트

## 6. 예외 상황 대응 계획

### ⚠️ 기술적 제약사항

- **CSS 호환성 이슈**: PostCSS autoprefixer 활용
- **접근성 구현 난이도**: 단계적 구현, 핵심 기능 우선
- **성능 최적화**: 가상화, lazy loading 고려

### 🔄 대안 설계

- **복잡한 애니메이션**: `prefers-reduced-motion` 고려한 fallback
- **모바일 성능**: 필수 기능만 남기고 점진적 향상
- **브라우저 호환**: 폴리필 및 기능 감지 기반 분기

---

## 📝 T-005-001 완료 체크리스트

### ✅ 기존 코드 구조 및 패턴 분석 완료

- [x] SvelteKit + TailwindCSS + DaisyUI 구조 파악
- [x] 기존 디자인 시스템 및 컬러 팔레트 확인
- [x] 폰트 및 테마 설정 분석
- [x] 현재 구현 상태 및 미완료 영역 파악

### ✅ UI/UX, 접근성, 반응형 설계 문서화

- [x] 사용자 스토리 기반 UI 설계
- [x] 모바일/데스크톱 레이아웃 와이어프레임
- [x] WCAG 2.1 AA 접근성 계획
- [x] 키보드 네비게이션 및 ARIA 설계

### ✅ 공통 모듈 인터페이스 및 연동 플로우 정의

- [x] 컴포넌트 아키텍처 및 모듈 구조 설계
- [x] Svelte Store 기반 상태 관리 설계
- [x] API 연동 인터페이스 정의 (REST + WebSocket)
- [x] 타입 정의 및 유틸리티 함수 계획

### ✅ 구현 로드맵 및 우선순위 수립

- [x] Phase별 구현 계획 (기본 구조 → 접근성 → 통합)
- [x] 우선순위별 체크리스트 (Must/Should/Could Have)
- [x] 품질 보증 및 테스트 전략
- [x] 예외 상황 대응 및 대안 설계

**🎯 T-005-001 서브태스크 완료 준비됨!**
