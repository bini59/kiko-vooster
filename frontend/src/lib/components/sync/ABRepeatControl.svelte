<script lang="ts">
  /**
   * A/B 구간 반복 재생 컨트롤 컴포넌트
   * 
   * 기능:
   * - A/B 포인트 설정 및 표시
   * - 반복 재생 토글
   * - 시각적 진행률 표시
   * - 반복 횟수 카운트
   * - 키보드 단축키 지원
   */
  
  import { createEventDispatcher } from 'svelte';
  import { audioState, abRepeatState, abRepeatActions, formattedCurrentTime } from '$lib/stores/audioStore';
  import { audioService } from '$lib/services/audioService';
  
  // Props
  export let compact = false;
  export let className = '';
  
  // 이벤트 디스패처
  const dispatch = createEventDispatcher<{
    pointSet: { type: 'A' | 'B'; time: number };
    repeatToggle: { isActive: boolean };
    seek: { time: number };
  }>();
  
  // 반응형 상태
  $: pointA = $abRepeatState.pointA;
  $: pointB = $abRepeatState.pointB;
  $: isActive = $abRepeatState.isActive;
  $: repeatCount = $abRepeatState.repeatCount;
  $: currentTime = $audioState.currentTime;
  $: duration = $audioState.duration;
  
  // UI 상태 계산
  $: hasValidRange = pointA !== null && pointB !== null && pointA < pointB;
  $: rangeDuration = hasValidRange ? (pointB! - pointA!) : 0;
  $: rangeProgress = hasValidRange && isActive 
    ? Math.max(0, Math.min(1, (currentTime - pointA!) / rangeDuration))
    : 0;
  
  // A 포인트 설정
  function setPointA() {
    audioService.setPointA();
    dispatch('pointSet', { type: 'A', time: currentTime });
    announceToScreenReader(`A 포인트를 ${formatTime(currentTime)}로 설정했습니다`);
  }
  
  // B 포인트 설정
  function setPointB() {
    audioService.setPointB();
    dispatch('pointSet', { type: 'B', time: currentTime });
    announceToScreenReader(`B 포인트를 ${formatTime(currentTime)}로 설정했습니다`);
  }
  
  // 반복 토글
  function toggleRepeat() {
    if (!hasValidRange) {
      announceToScreenReader('A와 B 포인트를 먼저 설정해주세요');
      return;
    }
    
    audioService.toggleABRepeat();
    dispatch('repeatToggle', { isActive: !isActive });
    announceToScreenReader(!isActive ? 'AB 반복 재생을 시작합니다' : 'AB 반복 재생을 종료합니다');
  }
  
  // 포인트 클리어
  function clearPoints() {
    audioService.clearABPoints();
    announceToScreenReader('A/B 포인트를 초기화했습니다');
  }
  
  // 특정 포인트로 이동
  function seekToPoint(time: number | null) {
    if (time !== null) {
      dispatch('seek', { time });
      audioService.seekTo(time);
      announceToScreenReader(`${formatTime(time)}로 이동합니다`);
    }
  }
  
  // 시간 포맷
  function formatTime(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  }
  
  // 스크린 리더 알림
  function announceToScreenReader(message: string) {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    setTimeout(() => document.body.removeChild(announcement), 1000);
  }
  
  // 키보드 이벤트 핸들러
  function handleKeydown(event: KeyboardEvent) {
    if (event.altKey) {
      switch (event.key.toLowerCase()) {
        case 'a':
          event.preventDefault();
          setPointA();
          break;
        case 'b':
          event.preventDefault();
          setPointB();
          break;
        case 'r':
          event.preventDefault();
          toggleRepeat();
          break;
        case 'c':
          event.preventDefault();
          clearPoints();
          break;
      }
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<!-- 메인 컨테이너 -->
<div 
  class="ab-repeat-control {className}"
  class:compact
  role="region"
  aria-label="AB 반복 재생 컨트롤"
>
  <!-- 헤더 -->
  <div class="control-header">
    <h3 class="control-title">
      {#if compact}
        AB 반복
      {:else}
        A/B 구간 반복 재생
      {/if}
    </h3>
    
    {#if isActive && hasValidRange}
      <div class="repeat-status">
        <span class="badge badge-primary">
          {repeatCount}회 반복
        </span>
      </div>
    {/if}
  </div>
  
  <!-- 시각적 타임라인 -->
  {#if !compact && hasValidRange}
    <div class="timeline-container">
      <div class="timeline" aria-label="AB 구간 타임라인">
        <!-- 전체 진행률 배경 -->
        <div class="timeline-background"></div>
        
        <!-- AB 구간 표시 -->
        <div 
          class="ab-range"
          style="left: {(pointA! / duration) * 100}%; width: {(rangeDuration / duration) * 100}%"
        ></div>
        
        <!-- 현재 위치 표시 -->
        <div 
          class="current-position"
          style="left: {(currentTime / duration) * 100}%"
          aria-label="현재 재생 위치"
        ></div>
        
        <!-- A 포인트 마커 -->
        {#if pointA !== null}
          <button
            class="point-marker point-a"
            style="left: {(pointA / duration) * 100}%"
            aria-label="A 포인트: {formatTime(pointA)}"
            on:click={() => seekToPoint(pointA)}
          >
            A
          </button>
        {/if}
        
        <!-- B 포인트 마커 -->
        {#if pointB !== null}
          <button
            class="point-marker point-b"
            style="left: {(pointB / duration) * 100}%"
            aria-label="B 포인트: {formatTime(pointB)}"
            on:click={() => seekToPoint(pointB)}
          >
            B
          </button>
        {/if}
      </div>
      
      <!-- 타임라인 범례 -->
      <div class="timeline-legend">
        <span class="legend-item">
          <div class="legend-color bg-primary"></div>
          AB 구간
        </span>
        <span class="legend-item">
          <div class="legend-color bg-accent"></div>
          현재 위치
        </span>
      </div>
    </div>
  {/if}
  
  <!-- 포인트 설정 버튼들 -->
  <div class="point-controls">
    <div class="point-group">
      <button
        class="btn btn-outline btn-sm"
        class:btn-success={pointA !== null}
        on:click={setPointA}
        aria-label="현재 위치를 A 포인트로 설정"
        title="Alt + A"
      >
        {#if compact}
          A
        {:else}
          A 포인트 설정
        {/if}
        {#if pointA !== null}
          <span class="point-time">({formatTime(pointA)})</span>
        {/if}
      </button>
      
      <button
        class="btn btn-outline btn-sm"
        class:btn-success={pointB !== null}
        on:click={setPointB}
        aria-label="현재 위치를 B 포인트로 설정"
        title="Alt + B"
      >
        {#if compact}
          B
        {:else}
          B 포인트 설정
        {/if}
        {#if pointB !== null}
          <span class="point-time">({formatTime(pointB)})</span>
        {/if}
      </button>
    </div>
    
    {#if !compact}
      <div class="current-time-display">
        <span class="text-sm text-base-content/60">현재: {$formattedCurrentTime}</span>
      </div>
    {/if}
  </div>
  
  <!-- 반복 컨트롤 -->
  <div class="repeat-controls">
    <button
      class="btn btn-primary btn-sm"
      class:btn-active={isActive}
      disabled={!hasValidRange}
      on:click={toggleRepeat}
      aria-label={isActive ? 'AB 반복 재생 중지' : 'AB 반복 재생 시작'}
      title="Alt + R"
    >
      {#if isActive}
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        {compact ? '정지' : '반복 정지'}
      {:else}
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        {compact ? '반복' : 'AB 반복'}
      {/if}
    </button>
    
    <button
      class="btn btn-ghost btn-sm"
      on:click={clearPoints}
      aria-label="A/B 포인트 초기화"
      title="Alt + C"
    >
      {#if compact}
        ×
      {:else}
        초기화
      {/if}
    </button>
  </div>
  
  <!-- 반복 정보 (확장 모드) -->
  {#if !compact && hasValidRange}
    <div class="repeat-info">
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">구간 길이</span>
          <span class="info-value">{formatTime(rangeDuration)}</span>
        </div>
        <div class="info-item">
          <span class="info-label">반복 횟수</span>
          <span class="info-value">{repeatCount}회</span>
        </div>
      </div>
    </div>
  {/if}
  
  <!-- 도움말 (확장 모드) -->
  {#if !compact}
    <div class="help-section">
      <details class="collapse collapse-arrow bg-base-200">
        <summary class="collapse-title text-sm font-medium">키보드 단축키</summary>
        <div class="collapse-content">
          <div class="space-y-1 text-xs">
            <div><kbd class="kbd kbd-xs">Alt</kbd> + <kbd class="kbd kbd-xs">A</kbd> : A 포인트 설정</div>
            <div><kbd class="kbd kbd-xs">Alt</kbd> + <kbd class="kbd kbd-xs">B</kbd> : B 포인트 설정</div>
            <div><kbd class="kbd kbd-xs">Alt</kbd> + <kbd class="kbd kbd-xs">R</kbd> : 반복 토글</div>
            <div><kbd class="kbd kbd-xs">Alt</kbd> + <kbd class="kbd kbd-xs">C</kbd> : 초기화</div>
          </div>
        </div>
      </details>
    </div>
  {/if}
</div>

<style>
  /* 메인 컨테이너 */
  .ab-repeat-control {
    @apply bg-base-100 rounded-lg border border-base-300;
    @apply p-4 space-y-4;
  }
  
  .ab-repeat-control.compact {
    @apply p-3 space-y-3;
  }
  
  /* 헤더 */
  .control-header {
    @apply flex items-center justify-between;
  }
  
  .control-title {
    @apply text-lg font-semibold text-base-content;
  }
  
  .compact .control-title {
    @apply text-base;
  }
  
  .repeat-status {
    @apply flex items-center gap-2;
  }
  
  /* 타임라인 */
  .timeline-container {
    @apply space-y-2;
  }
  
  .timeline {
    @apply relative h-8 bg-base-200 rounded-full overflow-hidden;
    @apply border border-base-300;
  }
  
  .timeline-background {
    @apply absolute inset-0 bg-base-200;
  }
  
  .ab-range {
    @apply absolute top-0 bottom-0 bg-primary/30;
    @apply border-x border-primary/50;
  }
  
  .current-position {
    @apply absolute top-0 bottom-0 w-0.5 bg-accent;
    @apply shadow-sm z-10;
  }
  
  .point-marker {
    @apply absolute -top-1 -bottom-1 w-6 text-xs font-bold;
    @apply bg-base-100 border-2 rounded;
    @apply flex items-center justify-center;
    @apply hover:scale-110 transition-transform;
    @apply focus:outline-none focus:ring-2 focus:ring-primary;
    transform: translateX(-50%);
    z-index: 20;
  }
  
  .point-a {
    @apply border-success text-success;
  }
  
  .point-b {
    @apply border-warning text-warning;
  }
  
  .timeline-legend {
    @apply flex gap-4 text-xs text-base-content/60;
  }
  
  .legend-item {
    @apply flex items-center gap-1;
  }
  
  .legend-color {
    @apply w-3 h-3 rounded;
  }
  
  /* 포인트 컨트롤 */
  .point-controls {
    @apply flex items-center justify-between gap-4;
  }
  
  .point-group {
    @apply flex gap-2;
  }
  
  .point-time {
    @apply text-xs opacity-70;
  }
  
  .current-time-display {
    @apply text-right;
  }
  
  /* 반복 컨트롤 */
  .repeat-controls {
    @apply flex gap-2 justify-center;
  }
  
  .compact .repeat-controls {
    @apply justify-start;
  }
  
  /* 반복 정보 */
  .repeat-info {
    @apply bg-base-50 rounded p-3;
  }
  
  .info-grid {
    @apply grid grid-cols-2 gap-4;
  }
  
  .info-item {
    @apply text-center;
  }
  
  .info-label {
    @apply block text-sm text-base-content/60;
  }
  
  .info-value {
    @apply block text-lg font-semibold text-base-content;
  }
  
  /* 도움말 */
  .help-section {
    @apply mt-4;
  }
  
  /* 접근성 개선 */
  .point-marker:focus {
    @apply outline-none ring-2 ring-primary;
  }
  
  /* 다크모드 최적화 */
  [data-theme="dark"] .ab-repeat-control {
    @apply border-base-600;
  }
  
  [data-theme="dark"] .timeline {
    @apply bg-base-300 border-base-600;
  }
  
  [data-theme="dark"] .repeat-info {
    @apply bg-base-200;
  }
  
  /* 모바일 최적화 */
  @media (max-width: 640px) {
    .point-controls {
      @apply flex-col gap-2;
    }
    
    .timeline {
      @apply h-6;
    }
    
    .point-marker {
      @apply w-5 text-xs;
    }
  }
  
  /* 고대비 모드 */
  @media (prefers-contrast: high) {
    .ab-range {
      @apply border-2;
    }
    
    .point-marker {
      @apply border-4;
    }
  }
  
  /* 모션 감소 모드 */
  @media (prefers-reduced-motion: reduce) {
    .point-marker {
      @apply transition-none;
    }
  }
</style> 