<script lang="ts">
  /**
   * 오디오 재생 컨트롤 컴포넌트
   * 
   * 기능:
   * - 재생/일시정지/정지
   * - 볼륨 조절
   * - 진행률 표시 및 탐색
   * - 재생 속도 조절
   * - 시간 표시
   */
  
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';
  import { audioState, audioActions, formattedCurrentTime, formattedDuration } from '$lib/stores/audioStore';
  import { audioService } from '$lib/services/audioService';
  
  // Props
  export let audioUrl: string;
  export let className = '';
  export let compact = false;
  
  // 이벤트 디스패처
  const dispatch = createEventDispatcher<{
    timeUpdate: { currentTime: number };
    play: void;
    pause: void;
    seek: { time: number };
    loadingChange: { isLoading: boolean };
    error: { message: string };
  }>();
  
  // 내부 상태
  let isUserSeeking = false;
  let seekValue = 0;
  let isInitialized = false;
  
  // 반응형 상태
  $: isPlaying = $audioState.isPlaying;
  $: currentTime = $audioState.currentTime;
  $: duration = $audioState.duration;
  $: volume = $audioState.volume;
  $: playbackRate = $audioState.playbackRate;
  $: isLoading = $audioState.isLoading;
  $: error = $audioState.error;
  
  // 진행률 계산
  $: progress = duration > 0 ? (currentTime / duration) * 100 : 0;
  
  // audioUrl 변경 시 오디오 로드
  $: {
    if (audioUrl && !isInitialized) {
      loadAudio();
    }
  }
  
  // 오디오 로드 함수
  async function loadAudio() {
    if (!audioUrl || isInitialized) return;
    
    try {
      await audioService.loadAudio(audioUrl);
      isInitialized = true;
      dispatch('loadingChange', { isLoading: false });
    } catch (err) {
      console.error('Failed to load audio:', err);
      dispatch('error', { message: '오디오 로드에 실패했습니다' });
    }
  }
  
  // 재생/일시정지 토글
  async function togglePlay() {
    try {
      await audioService.togglePlay();
      
      if (isPlaying) {
        dispatch('pause');
      } else {
        dispatch('play');
      }
    } catch (err) {
      console.error('Failed to toggle play:', err);
      dispatch('error', { message: '재생 제어에 실패했습니다' });
    }
  }
  
  // 탐색 (시간 이동)
  function handleSeek(event: Event) {
    const target = event.target as HTMLInputElement;
    const newTime = (parseFloat(target.value) / 100) * duration;
    
    audioService.seekTo(newTime);
    dispatch('seek', { time: newTime });
  }
  
  // 탐색 시작
  function handleSeekStart() {
    isUserSeeking = true;
  }
  
  // 탐색 종료
  function handleSeekEnd() {
    isUserSeeking = false;
  }
  
  // 볼륨 조절
  function handleVolumeChange(event: Event) {
    const target = event.target as HTMLInputElement;
    const newVolume = parseFloat(target.value) / 100;
    
    audioService.setVolume(newVolume);
  }
  
  // 재생 속도 조절
  function handlePlaybackRateChange(rate: number) {
    audioService.setPlaybackRate(rate);
  }
  
  // 키보드 단축키
  function handleKeydown(event: KeyboardEvent) {
    if (event.target instanceof HTMLInputElement) return;
    
    switch (event.key) {
      case ' ':
        event.preventDefault();
        togglePlay();
        break;
      case 'ArrowLeft':
        if (event.shiftKey) {
          event.preventDefault();
          skipTime(-10);
        }
        break;
      case 'ArrowRight':
        if (event.shiftKey) {
          event.preventDefault();
          skipTime(10);
        }
        break;
    }
  }
  
  // 시간 스킵
  function skipTime(seconds: number) {
    const newTime = Math.max(0, Math.min(duration, currentTime + seconds));
    audioService.seekTo(newTime);
  }
  
  // 스토어 구독 - 시간 업데이트 이벤트 디스패치
  $: {
    if (currentTime !== undefined) {
      dispatch('timeUpdate', { currentTime });
    }
  }
  
  // 로딩 상태 변경 이벤트
  $: {
    if (isLoading !== undefined) {
      dispatch('loadingChange', { isLoading });
    }
  }
  
  // 에러 상태 변경 이벤트
  $: {
    if (error) {
      dispatch('error', { message: error });
    }
  }
  
  onMount(() => {
    document.addEventListener('keydown', handleKeydown);
    
    // audioUrl이 있으면 바로 로드
    if (audioUrl) {
      loadAudio();
    }
  });
  
  onDestroy(() => {
    document.removeEventListener('keydown', handleKeydown);
  });
</script>

<!-- 컨트롤 컨테이너 -->
<div 
  class="audio-controls {className}" 
  class:compact
  role="region"
  aria-label="오디오 재생 컨트롤"
>
  <!-- 에러 표시 -->
  {#if error}
    <div class="error-banner" role="alert" aria-live="assertive">
      <span class="error-icon">⚠️</span>
      <span class="error-message">{error}</span>
    </div>
  {/if}
  
  <!-- 메인 컨트롤 영역 -->
  <div class="controls-main">
    <!-- 재생 컨트롤 -->
    <div class="play-controls">
      <!-- 재생/일시정지 버튼 -->
      <button
        class="play-button btn btn-primary"
        class:loading={isLoading}
        on:click={togglePlay}
        disabled={isLoading || !!error}
        aria-label={isPlaying ? '일시정지' : '재생'}
        aria-pressed={isPlaying}
      >
        {#if isLoading}
          <span class="loading loading-spinner loading-xs"></span>
        {:else if isPlaying}
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
            <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
          </svg>
        {:else}
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z"/>
          </svg>
        {/if}
      </button>
      
      <!-- 10초 뒤로 -->
      <button
        class="skip-button btn btn-ghost btn-sm"
        on:click={() => skipTime(-10)}
        disabled={isLoading || !!error}
        aria-label="10초 뒤로"
      >
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 6v6l4 2.5"/>
          <path d="M12 2C8.5 2 5.5 4.5 4.5 8"/>
          <path d="M4.5 8L2 6l2.5-2"/>
        </svg>
        <span class="text-xs">10s</span>
      </button>
      
      <!-- 10초 앞으로 -->
      <button
        class="skip-button btn btn-ghost btn-sm"
        on:click={() => skipTime(10)}
        disabled={isLoading || !!error}
        aria-label="10초 앞으로"
      >
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 6v6l4 2.5"/>
          <path d="M12 2c3.5 0 6.5 2.5 7.5 6"/>
          <path d="M19.5 8L22 6l-2.5-2"/>
        </svg>
        <span class="text-xs">10s</span>
      </button>
    </div>
    
    <!-- 진행률 바 -->
    <div class="progress-section">
      <div class="time-display">
        <span class="current-time">{$formattedCurrentTime}</span>
        <span class="duration">{$formattedDuration}</span>
      </div>
      
      <div class="progress-container">
        <input
          type="range"
          class="progress-slider range range-primary"
          min="0"
          max="100"
          step="0.1"
          value={isUserSeeking ? seekValue : progress}
          on:input={(e) => {
            seekValue = parseFloat(e.currentTarget.value);
          }}
          on:mousedown={handleSeekStart}
          on:mouseup={handleSeekEnd}
          on:change={handleSeek}
          disabled={isLoading || duration === 0 || !!error}
          aria-label="재생 진행률"
          aria-valuemin="0"
          aria-valuemax="100"
          aria-valuenow={progress}
          aria-valuetext="{$formattedCurrentTime} / {$formattedDuration}"
        />
      </div>
    </div>
    
    <!-- 추가 컨트롤 (컴팩트 모드가 아닐 때) -->
    {#if !compact}
      <div class="additional-controls">
        <!-- 볼륨 컨트롤 -->
        <div class="volume-control">
          <label class="volume-label" for="volume-slider">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
            </svg>
          </label>
          <input
            id="volume-slider"
            type="range"
            class="volume-slider range range-xs range-secondary"
            min="0"
            max="100"
            step="1"
            value={volume * 100}
            on:input={handleVolumeChange}
            aria-label="볼륨"
            aria-valuemin="0"
            aria-valuemax="100"
            aria-valuenow={volume * 100}
          />
          <span class="volume-display text-xs">{Math.round(volume * 100)}%</span>
        </div>
        
        <!-- 재생 속도 컨트롤 -->
        <div class="playback-rate-control">
          <label class="rate-label text-xs">속도:</label>
          <div class="rate-buttons">
            {#each [0.5, 0.75, 1, 1.25, 1.5, 2] as rate}
              <button
                class="rate-button btn btn-xs"
                class:btn-primary={playbackRate === rate}
                class:btn-ghost={playbackRate !== rate}
                on:click={() => handlePlaybackRateChange(rate)}
                aria-label="재생 속도 {rate}배"
                aria-pressed={playbackRate === rate}
              >
                {rate}x
              </button>
            {/each}
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .audio-controls {
    @apply bg-base-200 border border-base-300 rounded-lg p-4 shadow-sm;
  }
  
  .audio-controls.compact {
    @apply p-2;
  }
  
  .error-banner {
    @apply alert alert-error mb-3 text-sm;
  }
  
  .error-icon {
    @apply text-lg;
  }
  
  .controls-main {
    @apply flex flex-col gap-4;
  }
  
  .audio-controls.compact .controls-main {
    @apply gap-2;
  }
  
  .play-controls {
    @apply flex items-center justify-center gap-2;
  }
  
  .play-button {
    @apply w-12 h-12 rounded-full flex items-center justify-center;
  }
  
  .audio-controls.compact .play-button {
    @apply w-10 h-10;
  }
  
  .skip-button {
    @apply flex flex-col items-center gap-1;
  }
  
  .progress-section {
    @apply flex flex-col gap-2;
  }
  
  .time-display {
    @apply flex justify-between text-sm text-base-content/70;
  }
  
  .progress-container {
    @apply w-full;
  }
  
  .progress-slider {
    @apply w-full;
  }
  
  .additional-controls {
    @apply flex flex-col gap-3 border-t border-base-300 pt-3;
  }
  
  .volume-control {
    @apply flex items-center gap-2;
  }
  
  .volume-label {
    @apply cursor-pointer;
  }
  
  .volume-slider {
    @apply flex-1;
  }
  
  .volume-display {
    @apply min-w-[3rem] text-center;
  }
  
  .playback-rate-control {
    @apply flex items-center gap-2;
  }
  
  .rate-buttons {
    @apply flex gap-1;
  }
  
  .rate-button {
    @apply min-w-[3rem];
  }
  
  /* 반응형 */
  @media (min-width: 768px) {
    .additional-controls {
      @apply flex-row justify-between;
    }
    
    .volume-control {
      @apply flex-1 max-w-xs;
    }
  }
</style> 