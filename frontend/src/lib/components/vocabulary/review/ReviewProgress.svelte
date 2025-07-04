<!--
  복습 진행도 표시 컴포넌트
  현재 진행 상황, 정답률, 남은 단어 수를 표시
-->
<script lang="ts">
  import type { ReviewProgress } from '$lib/types/vocabulary';

  export let progress: ReviewProgress;
  export let compact = false;

  $: progressPercentage = progress.totalWords > 0 
    ? (progress.currentIndex / progress.totalWords) * 100 
    : 0;

  $: accuracyPercentage = Math.round(progress.accuracyRate);

  function formatTime(milliseconds: number): string {
    const seconds = Math.round(milliseconds / 1000);
    if (seconds < 60) {
      return `${seconds}초`;
    } else {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes}분 ${remainingSeconds}초`;
    }
  }
</script>

<div class="review-progress" class:compact>
  {#if !compact}
    <!-- 전체 버전 -->
    <div class="progress-header">
      <h3 class="progress-title">복습 진행 상황</h3>
    </div>

    <div class="progress-main">
      <!-- 전체 진행률 -->
      <div class="progress-section">
        <div class="section-header">
          <span class="section-label">진행률</span>
          <span class="section-value">{progress.currentIndex} / {progress.totalWords}</span>
        </div>
        <div class="progress-bar-container">
          <progress 
            class="progress progress-primary w-full" 
            value={progressPercentage} 
            max="100"
            aria-label="복습 진행률"
          ></progress>
          <span class="progress-percentage">{Math.round(progressPercentage)}%</span>
        </div>
      </div>

      <!-- 정답률 -->
      <div class="progress-section">
        <div class="section-header">
          <span class="section-label">정답률</span>
          <span class="section-value">{progress.correctAnswers} / {progress.correctAnswers + progress.incorrectAnswers}</span>
        </div>
        <div class="progress-bar-container">
          <progress 
            class="progress progress-success w-full" 
            value={accuracyPercentage} 
            max="100"
            aria-label="정답률"
          ></progress>
          <span class="progress-percentage">{accuracyPercentage}%</span>
        </div>
      </div>

      <!-- 통계 정보 -->
      <div class="stats-grid">
        <div class="stat-item correct">
          <div class="stat-icon">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
          </div>
          <div class="stat-info">
            <div class="stat-value">{progress.correctAnswers}</div>
            <div class="stat-label">정답</div>
          </div>
        </div>

        <div class="stat-item incorrect">
          <div class="stat-icon">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </div>
          <div class="stat-info">
            <div class="stat-value">{progress.incorrectAnswers}</div>
            <div class="stat-label">오답</div>
          </div>
        </div>

        <div class="stat-item remaining">
          <div class="stat-icon">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
          </div>
          <div class="stat-info">
            <div class="stat-value">{progress.remainingWords}</div>
            <div class="stat-label">남은 단어</div>
          </div>
        </div>

        <div class="stat-item time">
          <div class="stat-icon">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
            </svg>
          </div>
          <div class="stat-info">
            <div class="stat-value">{formatTime(progress.averageResponseTime)}</div>
            <div class="stat-label">평균 응답시간</div>
          </div>
        </div>
      </div>
    </div>
  {:else}
    <!-- 컴팩트 버전 -->
    <div class="compact-progress">
      <div class="compact-header">
        <span class="compact-current">{progress.currentIndex} / {progress.totalWords}</span>
        <span class="compact-accuracy">{accuracyPercentage}% 정답</span>
      </div>
      <progress 
        class="progress progress-primary w-full h-2" 
        value={progressPercentage} 
        max="100"
        aria-label="복습 진행률"
      ></progress>
      <div class="compact-stats">
        <span class="correct-count">✓ {progress.correctAnswers}</span>
        <span class="incorrect-count">✗ {progress.incorrectAnswers}</span>
        <span class="remaining-count">⏳ {progress.remainingWords}</span>
      </div>
    </div>
  {/if}
</div>

<style>
  .review-progress {
    background: hsl(var(--b2));
    border-radius: 1rem;
    overflow: hidden;
  }

  .review-progress:not(.compact) {
    padding: 1.5rem;
  }

  .progress-header {
    margin-bottom: 1.5rem;
    text-align: center;
  }

  .progress-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: hsl(var(--bc));
  }

  .progress-main {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .progress-section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .section-label {
    font-weight: 600;
    color: hsl(var(--bc));
  }

  .section-value {
    font-weight: 500;
    color: hsl(var(--bc) / 0.7);
    font-size: 0.9rem;
  }

  .progress-bar-container {
    position: relative;
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .progress-percentage {
    font-weight: 600;
    color: hsl(var(--p));
    font-size: 0.9rem;
    min-width: 3rem;
    text-align: right;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 1rem;
    margin-top: 0.5rem;
  }

  .stat-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    background: hsl(var(--b1));
    border-radius: 0.75rem;
    border: 1px solid hsl(var(--b3));
    transition: all 0.2s ease;
  }

  .stat-item:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px hsl(var(--b3) / 0.4);
  }

  .stat-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 0.5rem;
    flex-shrink: 0;
  }

  .stat-item.correct .stat-icon {
    background: hsl(var(--su) / 0.1);
    color: hsl(var(--su));
  }

  .stat-item.incorrect .stat-icon {
    background: hsl(var(--er) / 0.1);
    color: hsl(var(--er));
  }

  .stat-item.remaining .stat-icon {
    background: hsl(var(--w) / 0.1);
    color: hsl(var(--w));
  }

  .stat-item.time .stat-icon {
    background: hsl(var(--in) / 0.1);
    color: hsl(var(--in));
  }

  .stat-info {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .stat-value {
    font-size: 1.25rem;
    font-weight: 700;
    color: hsl(var(--bc));
    line-height: 1.2;
  }

  .stat-label {
    font-size: 0.75rem;
    color: hsl(var(--bc) / 0.6);
    font-weight: 500;
  }

  /* 컴팩트 버전 스타일 */
  .compact-progress {
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .compact-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.9rem;
  }

  .compact-current {
    font-weight: 600;
    color: hsl(var(--p));
  }

  .compact-accuracy {
    font-weight: 500;
    color: hsl(var(--su));
  }

  .compact-stats {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.8rem;
    margin-top: 0.25rem;
  }

  .correct-count {
    color: hsl(var(--su));
    font-weight: 500;
  }

  .incorrect-count {
    color: hsl(var(--er));
    font-weight: 500;
  }

  .remaining-count {
    color: hsl(var(--bc) / 0.7);
    font-weight: 500;
  }

  /* 모바일 반응형 */
  @media (max-width: 640px) {
    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .stat-item {
      padding: 0.75rem;
    }

    .stat-icon {
      width: 2rem;
      height: 2rem;
    }

    .stat-value {
      font-size: 1.1rem;
    }

    .compact-header {
      font-size: 0.8rem;
    }

    .compact-stats {
      font-size: 0.75rem;
    }
  }

  /* 접근성 */
  @media (prefers-reduced-motion: reduce) {
    .stat-item {
      transition: none;
    }

    .stat-item:hover {
      transform: none;
      box-shadow: none;
    }
  }

  /* 다크모드 지원 */
  @media (prefers-color-scheme: dark) {
    .stat-item:hover {
      box-shadow: 0 4px 12px hsl(var(--b3) / 0.8);
    }
  }
</style> 