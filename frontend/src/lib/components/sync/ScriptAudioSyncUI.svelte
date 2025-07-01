<script lang="ts">
  /**
   * 스크립트-오디오 싱크 메인 UI 컨테이너
   * 
   * 반응형 레이아웃:
   * - 모바일: 세로 스택 (오디오 컨트롤 -> 스크립트 -> AB 컨트롤)
   * - 데스크톱: 사이드바 (스크립트 메인 + AB 컨트롤 사이드)
   */
  
  import { onMount, onDestroy } from 'svelte';
  import { audioState, abRepeatState } from '$lib/stores/audioStore';
  import { currentScript, highlightState, scriptActions } from '$lib/stores/scriptStore';
  import { audioService } from '$lib/services/audioService';
  import SentenceHighlight from './SentenceHighlight.svelte';
  import ABRepeatControl from './ABRepeatControl.svelte';
  import AudioControls from '../audio/AudioControls.svelte';
  
  // Props
  export let scriptId: string;
  export let audioUrl: string;
  export let className: string = '';
  
  // 반응형 상태
  let isMobile = false;
  let containerElement: HTMLElement;
  
  // 접근성 상태
  let announceText = '';
  let skipLinksVisible = false;
  
  // 리사이즈 감지
  function checkViewport() {
    isMobile = window.innerWidth < 768; // md breakpoint
  }
  
  // 스킵 링크 처리
  function handleSkipToScript() {
    const scriptPanel = containerElement?.querySelector('#script-panel');
    (scriptPanel as HTMLElement)?.focus();
    announceText = '스크립트 패널로 이동했습니다';
  }
  
  function handleSkipToControls() {
    const controls = containerElement?.querySelector('#ab-controls');
    (controls as HTMLElement)?.focus();
    announceText = 'AB 반복 컨트롤로 이동했습니다';
  }
  
  // 키보드 단축키 처리
  function handleGlobalKeydown(event: KeyboardEvent) {
    // 입력 필드에서는 단축키 비활성화
    if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
      return;
    }
    
    switch (event.key.toLowerCase()) {
      case ' ':
        event.preventDefault();
        // 재생/일시정지 토글 (스페이스바)
        audioService.togglePlay().catch(err => {
          console.error('Toggle play failed:', err);
        });
        announceText = $audioState.isPlaying ? '재생 일시정지' : '재생 시작';
        break;
      
      case 'a':
        if (event.altKey) {
          event.preventDefault();
          // A 포인트 설정 (Alt + A)
          audioService.setPointA();
          announceText = `A 포인트를 ${$audioState.currentTime.toFixed(1)}초로 설정했습니다`;
        }
        break;
        
      case 'b':
        if (event.altKey) {
          event.preventDefault();
          // B 포인트 설정 (Alt + B)
          audioService.setPointB();
          announceText = `B 포인트를 ${$audioState.currentTime.toFixed(1)}초로 설정했습니다`;
        }
        break;
        
      case 'r':
        if (event.altKey) {
          event.preventDefault();
          // AB 반복 토글 (Alt + R)
          audioService.toggleABRepeat();
          announceText = $abRepeatState.isActive ? 'AB 반복 종료' : 'AB 반복 시작';
        }
        break;
        
      case 'escape':
        // 스킵 링크 숨기기
        skipLinksVisible = false;
        break;
    }
  }
  
  // 포커스 이벤트 (스킵 링크 표시)
  function handleFocus() {
    skipLinksVisible = true;
  }
  
  onMount(() => {
    checkViewport();
    window.addEventListener('resize', checkViewport);
    document.addEventListener('keydown', handleGlobalKeydown);
    document.addEventListener('focusin', handleFocus);
    
    // 테스트용 스크립트 데이터 로드
    if (scriptId) {
      loadScript(scriptId);
    }
  });
  
  onDestroy(() => {
    window.removeEventListener('resize', checkViewport);
    document.removeEventListener('keydown', handleGlobalKeydown);
    document.removeEventListener('focusin', handleFocus);
  });
  
  // 스크립트 로드 (테스트용)
  async function loadScript(id: string) {
    // TODO: 실제 API 호출로 대체
    const mockScript = {
      id,
      title: '일본어 라디오 뉴스',
      language: 'ja',
      sentences: [
        { id: 's1', content: 'おはようございます。', orderIndex: 0 },
        { id: 's2', content: '今日のニュースをお伝えします。', orderIndex: 1 },
        { id: 's3', content: '天気予報では、今日は晴れの予定です。', orderIndex: 2 },
        { id: 's4', content: '最高気温は25度になる見込みです。', orderIndex: 3 },
        { id: 's5', content: 'それでは、詳しいニュースをどうぞ。', orderIndex: 4 }
      ],
      mappings: [
        { id: 'm1', sentenceId: 's1', startTime: 0, endTime: 2.5, mappingType: 'auto' as const, confidence: 0.9, isActive: true },
        { id: 'm2', sentenceId: 's2', startTime: 2.5, endTime: 6.0, mappingType: 'auto' as const, confidence: 0.85, isActive: true },
        { id: 'm3', sentenceId: 's3', startTime: 6.0, endTime: 11.5, mappingType: 'auto' as const, confidence: 0.88, isActive: true },
        { id: 'm4', sentenceId: 's4', startTime: 11.5, endTime: 16.0, mappingType: 'auto' as const, confidence: 0.82, isActive: true },
        { id: 'm5', sentenceId: 's5', startTime: 16.0, endTime: 20.5, mappingType: 'auto' as const, confidence: 0.87, isActive: true }
      ],
      metadata: {}
    };
    
    scriptActions.setScript(mockScript);
  }
</script>

<svelte:window on:keydown={handleGlobalKeydown} />

<!-- 접근성: 스크린 리더 알림 -->
<div class="sr-only" aria-live="polite" aria-atomic="true">
  {announceText}
</div>

<!-- 스킵 링크 (키보드 접근성) -->
{#if skipLinksVisible}
  <div class="skip-links">
    <a href="#script-panel" on:click={handleSkipToScript} class="skip-link">
      스크립트로 바로가기
    </a>
    <a href="#ab-controls" on:click={handleSkipToControls} class="skip-link">
      AB 컨트롤로 바로가기
    </a>
  </div>
{/if}

<!-- 메인 컨테이너 -->
<div 
  bind:this={containerElement}
  class="script-audio-sync-ui {className}"
  role="application"
  aria-label="스크립트-오디오 싱크 플레이어"
  data-mobile={isMobile}
>
  <!-- 오디오 컨트롤 (상단 고정) -->
  <header class="audio-header">
    <AudioControls {audioUrl} />
  </header>
  
  <!-- 메인 콘텐츠 영역 -->
  <main class="content-area">
    {#if isMobile}
      <!-- 모바일 레이아웃: 세로 스택 -->
      <div class="mobile-layout">
        <!-- 스크립트 패널 -->
        <section 
          id="script-panel"
          class="script-section"
          tabindex="-1"
          aria-label="스크립트 텍스트"
        >
          <SentenceHighlight script={$currentScript} />
        </section>
        
        <!-- AB 반복 컨트롤 (하단 고정) -->
        <aside 
          id="ab-controls"
          class="ab-controls-mobile"
          tabindex="-1"
          aria-label="AB 반복 재생 컨트롤"
        >
          <ABRepeatControl compact={true} />
        </aside>
      </div>
    {:else}
      <!-- 데스크톱 레이아웃: 사이드바 -->
      <div class="desktop-layout">
        <!-- 스크립트 패널 (메인) -->
        <section 
          id="script-panel"
          class="script-section-desktop"
          tabindex="-1"
          aria-label="스크립트 텍스트"
        >
          <SentenceHighlight script={$currentScript} />
        </section>
        
        <!-- 사이드바 (AB 컨트롤 + 설정) -->
        <aside 
          id="ab-controls"
          class="sidebar"
          tabindex="-1"
          aria-label="컨트롤 패널"
        >
          <div class="sidebar-content">
            <ABRepeatControl compact={false} />
            
            <!-- 추가 설정 영역 -->
            <div class="settings-section">
              <h3 class="settings-title">설정</h3>
              <div class="setting-item">
                <label class="label cursor-pointer justify-start gap-3">
                  <input 
                    type="checkbox" 
                    class="checkbox checkbox-primary"
                    checked={$highlightState.isAutoHighlight}
                    on:change={scriptActions.toggleAutoHighlight}
                  />
                  <span class="label-text">자동 하이라이트</span>
                </label>
              </div>
            </div>
          </div>
        </aside>
      </div>
    {/if}
  </main>
</div>

<style>
  /* 기본 레이아웃 */
  .script-audio-sync-ui {
    @apply flex flex-col h-screen bg-base-100;
    font-family: 'Inter', system-ui, sans-serif;
  }
  
  /* 스킵 링크 */
  .skip-links {
    @apply fixed top-0 left-0 z-50 flex gap-2 p-2;
  }
  
  .skip-link {
    @apply btn btn-sm btn-primary opacity-0 -translate-y-full;
    @apply focus:opacity-100 focus:translate-y-0;
    @apply transition-all duration-200;
  }
  
  /* 오디오 헤더 */
  .audio-header {
    @apply sticky top-0 z-10 bg-base-100 border-b border-base-300;
    @apply shadow-sm backdrop-blur-sm;
  }
  
  /* 콘텐츠 영역 */
  .content-area {
    @apply flex-1 overflow-hidden;
  }
  
  /* 모바일 레이아웃 */
  .mobile-layout {
    @apply flex flex-col h-full;
  }
  
  .script-section {
    @apply flex-1 overflow-y-auto p-4;
    @apply border-b border-base-300;
  }
  
  .ab-controls-mobile {
    @apply sticky bottom-0 bg-base-100 border-t border-base-300;
    @apply p-4 shadow-lg backdrop-blur-sm;
  }
  
  /* 데스크톱 레이아웃 */
  .desktop-layout {
    @apply flex h-full;
  }
  
  .script-section-desktop {
    @apply flex-1 overflow-y-auto p-6;
    @apply border-r border-base-300;
  }
  
  .sidebar {
    @apply w-80 bg-base-50 overflow-y-auto;
    @apply border-l border-base-200;
  }
  
  .sidebar-content {
    @apply p-6 space-y-6;
  }
  
  /* 설정 섹션 */
  .settings-section {
    @apply space-y-4;
  }
  
  .settings-title {
    @apply text-lg font-semibold text-base-content;
  }
  
  .setting-item {
    @apply py-2;
  }
  
  /* 접근성 개선 */
  .script-audio-sync-ui:focus-within .skip-links {
    @apply block;
  }
  
  /* 다크모드 최적화 */
  [data-theme="dark"] .audio-header {
    @apply bg-base-100/95;
  }
  
  [data-theme="dark"] .ab-controls-mobile {
    @apply bg-base-100/95;
  }
  
  [data-theme="dark"] .sidebar {
    @apply bg-base-200;
  }
  
  /* 반응형 세부 조정 */
  @media (max-width: 640px) {
    .script-section {
      @apply p-3;
    }
    
    .ab-controls-mobile {
      @apply p-3;
    }
  }
  
  /* 고대비 모드 */
  @media (prefers-contrast: high) {
    .audio-header,
    .ab-controls-mobile {
      @apply border-2;
    }
  }
  
  /* 모션 감소 모드 */
  @media (prefers-reduced-motion: reduce) {
    .skip-link {
      @apply transition-none;
    }
  }
</style> 