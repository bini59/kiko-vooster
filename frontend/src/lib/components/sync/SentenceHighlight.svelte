<script lang="ts">
  /**
   * 문장별 하이라이트 컴포넌트
   * 
   * 기능:
   * - 현재 재생 중인 문장 자동 하이라이트
   * - 문장 클릭 시 해당 시간으로 탐색
   * - 키보드 네비게이션 (화살표 키)
   * - 접근성 지원 (ARIA, 스크린 리더)
   * - 단어 클릭 시 사전 팝업 (향후 확장)
   */
  
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';
  import { audioState } from '$lib/stores/audioStore';
  import { highlightState, scriptActions } from '$lib/stores/scriptStore';
  import { audioService } from '$lib/services/audioService';
  
  // Props
  export let script: any = null;
  export let className = '';
  export let showWordTooltips = true;
  export let autoScroll = true;
  
  // 이벤트 디스패처
  const dispatch = createEventDispatcher<{
    sentenceClick: { sentenceId: string; startTime: number };
    wordClick: { word: string; sentenceId: string };
    navigationChange: { sentenceId: string; index: number };
  }>();
  
  // 내부 상태
  let containerElement: HTMLElement;
  let sentenceElements: HTMLElement[] = [];
  let focusedSentenceIndex = 0;
  let announceText = '';
  
  // 반응형 상태
  $: currentTime = $audioState.currentTime;
  $: isPlaying = $audioState.isPlaying;
  $: currentSentenceId = $highlightState.currentSentenceId;
  $: highlightedSentences = $highlightState.highlightedSentences;
  
  // 스크립트 데이터
  $: sentences = script?.sentences || [];
  $: mappings = script?.mappings || [];
  
  // 현재 재생 중인 문장 찾기
  $: {
    if (isPlaying && mappings.length > 0) {
      const activeMappings = mappings.filter((m: any) => m.isActive);
      const currentMapping = activeMappings.find((m: any) => 
        currentTime >= m.startTime && currentTime < m.endTime
      );
      
      if (currentMapping) {
        const newSentenceId = currentMapping.sentenceId;
        if (newSentenceId !== currentSentenceId) {
          scriptActions.setCurrentSentence(newSentenceId);
          
          // 자동 스크롤
          if (autoScroll) {
            scrollToCurrentSentence(newSentenceId);
          }
          
          // 스크린 리더 알림
          const sentence = sentences.find((s: any) => s.id === newSentenceId);
          if (sentence) {
            announceText = `현재 문장: ${sentence.content}`;
          }
        }
      }
    }
  }
  
  // 문장 클릭 핸들러
  function handleSentenceClick(sentenceId: string) {
    const mapping = mappings.find((m: any) => m.sentenceId === sentenceId && m.isActive);
    if (mapping) {
      // audioService를 통해 해당 문장으로 점프
      audioService.jumpToSentence(sentenceId, mappings);
      
      dispatch('sentenceClick', { 
        sentenceId, 
        startTime: mapping.startTime 
      });
      
      const sentence = sentences.find((s: any) => s.id === sentenceId);
      announceText = `${sentence?.content} 구간으로 이동합니다`;
    }
  }
  
  // 단어 클릭 핸들러
  function handleWordClick(event: MouseEvent, sentenceId: string) {
    if (!showWordTooltips) return;
    
    const target = event.target as HTMLElement;
    if (target.classList.contains('word')) {
      const word = target.textContent?.trim() || '';
      dispatch('wordClick', { word, sentenceId });
      announceText = `단어 "${word}" 선택됨`;
    }
  }
  
  // 키보드 네비게이션
  function handleKeydown(event: KeyboardEvent) {
    if (!sentences.length) return;
    
    switch (event.key) {
      case 'ArrowUp':
      case 'ArrowLeft':
        event.preventDefault();
        navigateToSentence(focusedSentenceIndex - 1);
        break;
        
      case 'ArrowDown':
      case 'ArrowRight':
        event.preventDefault();
        navigateToSentence(focusedSentenceIndex + 1);
        break;
        
      case 'Enter':
      case ' ':
        event.preventDefault();
        const currentSentence = sentences[focusedSentenceIndex];
        if (currentSentence) {
          handleSentenceClick(currentSentence.id);
        }
        break;
        
      case 'Home':
        event.preventDefault();
        navigateToSentence(0);
        break;
        
      case 'End':
        event.preventDefault();
        navigateToSentence(sentences.length - 1);
        break;
    }
  }
  
  // 문장 네비게이션
  function navigateToSentence(index: number) {
    const clampedIndex = Math.max(0, Math.min(sentences.length - 1, index));
    focusedSentenceIndex = clampedIndex;
    
    const sentence = sentences[clampedIndex];
    if (sentence && sentenceElements[clampedIndex]) {
      sentenceElements[clampedIndex].focus();
      dispatch('navigationChange', { 
        sentenceId: sentence.id, 
        index: clampedIndex 
      });
      
      announceText = `문장 ${clampedIndex + 1}: ${sentence.content}`;
    }
  }
  
  // 현재 문장으로 스크롤
  function scrollToCurrentSentence(sentenceId: string) {
    const index = sentences.findIndex((s: any) => s.id === sentenceId);
    if (index >= 0 && sentenceElements[index]) {
      sentenceElements[index].scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      });
    }
  }
  
  // 문장이 현재 재생 중인지 확인
  function isSentenceCurrent(sentenceId: string): boolean {
    return sentenceId === currentSentenceId;
  }
  
  // 문장이 하이라이트되어야 하는지 확인
  function isSentenceHighlighted(sentenceId: string): boolean {
    return highlightedSentences.has(sentenceId);
  }
  
  // 문장을 단어로 분할 (향후 사전 기능용)
  function splitIntoWords(content: string): string[] {
    // 일본어 텍스트를 단어 단위로 분할
    // 현재는 간단한 공백 기준, 향후 형태소 분석 적용 가능
    return content.split(/(\s+|(?<=[ひらがなカタカナ漢字])(?=[ひらがなカタカナ漢字])|(?<=[a-zA-Z])(?=[a-zA-Z]))/);
  }
  
  // 문장 텍스트 렌더링 (단어별 분할)
  function renderSentenceWithWords(sentence: any) {
    if (!showWordTooltips) {
      return sentence.content;
    }
    
    const words = splitIntoWords(sentence.content);
    return words.map((word, index) => {
      if (word.trim()) {
        return `<span class="word" data-word="${word.trim()}" data-index="${index}">${word}</span>`;
      }
      return word;
    }).join('');
  }
  
  onMount(() => {
    // 첫 번째 문장에 초기 포커스
    if (sentences.length > 0 && sentenceElements[0]) {
      sentenceElements[0].focus();
    }
  });
</script>

<svelte:window on:keydown={handleKeydown} />

<!-- 접근성: 스크린 리더 알림 -->
<div class="sr-only" aria-live="polite" aria-atomic="true">
  {announceText}
</div>

<!-- 메인 컨테이너 -->
<div 
  bind:this={containerElement}
  class="sentence-highlight {className}"
  role="region"
  aria-label="스크립트 텍스트 - 화살표 키로 문장 탐색, 엔터/스페이스로 해당 구간 재생"
>
  <!-- 스크립트 헤더 -->
  {#if script}
    <header class="script-header">
      <h2 class="script-title">{script.title || '스크립트'}</h2>
      <div class="script-meta">
        <span class="sentence-count">{sentences.length}개 문장</span>
        {#if script.language}
          <span class="language-tag" lang={script.language}>
            {script.language.toUpperCase()}
          </span>
        {/if}
      </div>
    </header>
  {/if}
  
  <!-- 사용법 안내 (접근성) -->
  <div class="usage-hint sr-only">
    화살표 키로 문장을 탐색하고, 엔터 키나 스페이스 키로 해당 구간을 재생할 수 있습니다.
    {#if showWordTooltips}
      단어를 클릭하면 사전 정보를 볼 수 있습니다.
    {/if}
  </div>
  
  <!-- 문장 리스트 -->
  <div class="sentences-container">
    {#if sentences.length === 0}
      <div class="empty-state">
        <p class="empty-message">스크립트를 불러오는 중...</p>
      </div>
    {:else}
             {#each sentences as sentence, index (sentence.id)}
         {@const mapping = mappings.find((m: any) => m.sentenceId === sentence.id && m.isActive)}
         {@const isCurrent = isSentenceCurrent(sentence.id)}
         {@const isHighlighted = isSentenceHighlighted(sentence.id)}
         
         <div
           bind:this={sentenceElements[index]}
           class="sentence-item"
           class:current={isCurrent}
           class:highlighted={isHighlighted}
           class:has-mapping={mapping}
           role="button"
           tabindex="0"
           aria-current={isCurrent ? 'true' : 'false'}
           aria-label="문장 {index + 1}: {sentence.content} - {mapping ? `재생 시간: ${mapping.startTime.toFixed(1)}초부터 ${mapping.endTime.toFixed(1)}초까지` : '매핑 정보 없음'}"
           on:click={() => handleSentenceClick(sentence.id)}
           on:keydown|stopPropagation
           on:mouseup={(e) => handleWordClick(e, sentence.id)}
         >
          <!-- 문장 번호 -->
          <span class="sentence-number" aria-hidden="true">
            {index + 1}
          </span>
          
          <!-- 문장 내용 -->
          <div class="sentence-content" lang={script?.language || 'ja'}>
            {#if showWordTooltips}
              {@html renderSentenceWithWords(sentence)}
            {:else}
              {sentence.content}
            {/if}
          </div>
          
          <!-- 타이밍 정보 -->
          {#if mapping}
            <div class="sentence-timing">
              <span class="start-time">{mapping.startTime.toFixed(1)}s</span>
              <span class="duration">({(mapping.endTime - mapping.startTime).toFixed(1)}s)</span>
              {#if mapping.confidence < 0.8}
                <span class="low-confidence" title="매핑 신뢰도가 낮습니다">⚠️</span>
              {/if}
            </div>
          {:else}
            <div class="sentence-timing no-mapping">
              <span class="no-mapping-text">매핑 없음</span>
            </div>
          {/if}
          
          <!-- 현재 재생 인디케이터 -->
          {#if isCurrent}
            <div class="current-indicator" aria-hidden="true">
              <span class="play-icon">▶</span>
            </div>
          {/if}
        </div>
      {/each}
    {/if}
  </div>
  
  <!-- 키보드 단축키 안내 -->
  <footer class="keyboard-hints">
    <details class="keyboard-help">
      <summary>키보드 단축키</summary>
      <ul>
        <li><kbd>↑</kbd><kbd>↓</kbd> 문장 탐색</li>
        <li><kbd>Enter</kbd><kbd>Space</kbd> 구간 재생</li>
        <li><kbd>Home</kbd><kbd>End</kbd> 처음/끝으로</li>
      </ul>
    </details>
  </footer>
</div>

<style>
  .sentence-highlight {
    @apply flex flex-col h-full bg-base-100;
  }
  
  /* 스크립트 헤더 */
  .script-header {
    @apply flex flex-col gap-2 p-4 border-b border-base-300;
  }
  
  .script-title {
    @apply text-lg font-semibold text-base-content;
  }
  
  .script-meta {
    @apply flex items-center gap-3 text-sm text-base-content/70;
  }
  
  .language-tag {
    @apply badge badge-outline;
  }
  
  /* 문장 컨테이너 */
  .sentences-container {
    @apply flex-1 overflow-y-auto p-4 space-y-2;
  }
  
  /* 빈 상태 */
  .empty-state {
    @apply flex items-center justify-center h-full;
  }
  
  .empty-message {
    @apply text-base-content/50 text-center;
  }
  
  /* 문장 아이템 */
  .sentence-item {
    @apply relative flex items-start gap-3 p-3 rounded-lg border border-base-300
           cursor-pointer transition-all duration-200 hover:bg-base-200
           focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2;
  }
  
  .sentence-item.current {
    @apply bg-primary/10 border-primary shadow-lg;
  }
  
  .sentence-item.highlighted {
    @apply bg-accent/10 border-accent;
  }
  
  .sentence-item:not(.has-mapping) {
    @apply opacity-60 cursor-not-allowed;
  }
  
  /* 문장 번호 */
  .sentence-number {
    @apply flex-shrink-0 w-6 h-6 bg-base-300 text-base-content/70 rounded-full
           flex items-center justify-center text-xs font-medium;
  }
  
  .sentence-item.current .sentence-number {
    @apply bg-primary text-primary-content;
  }
  
  /* 문장 내용 */
  .sentence-content {
    @apply flex-1 text-base leading-relaxed text-base-content;
    font-family: 'Noto Sans JP', sans-serif;
  }
  
  .sentence-item.current .sentence-content {
    @apply font-medium;
  }
  
  /* 단어 하이라이트 */
  :global(.sentence-content .word) {
    @apply hover:bg-info/20 hover:text-info-content rounded px-1 cursor-pointer
           transition-colors duration-150;
  }
  
  /* 타이밍 정보 */
  .sentence-timing {
    @apply flex-shrink-0 text-xs text-base-content/50 flex items-center gap-1;
  }
  
  .sentence-timing.no-mapping {
    @apply text-warning;
  }
  
  .low-confidence {
    @apply text-warning cursor-help;
  }
  
  /* 현재 재생 인디케이터 */
  .current-indicator {
    @apply absolute -left-2 top-1/2 transform -translate-y-1/2;
  }
  
  .play-icon {
    @apply text-primary text-lg animate-pulse;
  }
  
  /* 키보드 단축키 안내 */
  .keyboard-hints {
    @apply p-4 border-t border-base-300;
  }
  
  .keyboard-help summary {
    @apply text-sm text-base-content/70 cursor-pointer;
  }
  
  .keyboard-help ul {
    @apply mt-2 space-y-1 text-xs text-base-content/60;
  }
  
  .keyboard-help kbd {
    @apply inline-block px-1.5 py-0.5 bg-base-300 text-base-content rounded text-xs font-mono;
  }
  
  /* 반응형 */
  @media (max-width: 768px) {
    .sentence-item {
      @apply flex-col gap-2;
    }
    
    .sentence-number {
      @apply self-start;
    }
    
    .sentence-timing {
      @apply self-end;
    }
  }
  
  /* 다크모드 대응 */
  @media (prefers-color-scheme: dark) {
    .sentence-item {
      @apply border-base-content/20;
    }
    
    .sentence-item:hover {
      @apply bg-base-content/10;
    }
  }
  
  /* 고대비 모드 */
  @media (prefers-contrast: high) {
    .sentence-item {
      @apply border-2;
    }
    
    .sentence-item.current {
      @apply border-4 border-primary;
    }
  }
  
  /* 모션 감소 모드 */
  @media (prefers-reduced-motion: reduce) {
    .sentence-item {
      @apply transition-none;
    }
    
    .play-icon {
      @apply animate-none;
    }
  }
</style> 