<!--
  복습 모드 페이지
  단어장에서 선택된 단어들로 복습 세션을 진행
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { get } from 'svelte/store';
  import { ReviewSessionMode, ReviewMode, GameMode } from '$lib/types/vocabulary';
  import { vocabularyState, vocabularyActions, reviewActions, reviewSession } from '$lib/stores/vocabularyStore';
  import { isLoggedIn } from '$lib/stores/authStore';
  import ReviewSession from '$lib/components/vocabulary/review/ReviewSession.svelte';
  import type { UserWord, ReviewSettings, ReviewResult } from '$lib/types/vocabulary';

  // URL 파라미터에서 복습 설정을 받아옴
  let words: UserWord[] = [];
  let settings: ReviewSettings = {
    mode: ReviewSessionMode.FLASHCARD,
    showReading: true,
    showExample: true,
    timeLimit: undefined,
    showHints: true,
    autoAdvance: false,
    shuffleWords: true,
    repeatIncorrect: true
  };

  let isLoading = true;
  let error: string | null = null;

  onMount(async () => {
    try {
      // 로그인 상태 확인
      if (!get(isLoggedIn)) {
        goto('/auth/login?redirect=/vocabulary/review');
        return;
      }

      // URL 파라미터에서 설정 읽기
      const urlParams = $page.url.searchParams;
      const mode = urlParams.get('mode') as keyof typeof ReviewSessionMode;
      const wordIds = urlParams.get('words')?.split(',') || [];
      const timeLimit = urlParams.get('timeLimit');
      const showHints = urlParams.get('showHints');
      const autoAdvance = urlParams.get('autoAdvance');
      const shuffleWords = urlParams.get('shuffleWords');

      // 설정 적용
      if (mode && ReviewSessionMode[mode]) {
        settings.mode = ReviewSessionMode[mode];
      }
      if (timeLimit) {
        settings.timeLimit = parseInt(timeLimit);
      }
      if (showHints !== null) {
        settings.showHints = showHints === 'true';
      }
      if (autoAdvance !== null) {
        settings.autoAdvance = autoAdvance === 'true';
      }
      if (shuffleWords !== null) {
        settings.shuffleWords = shuffleWords === 'true';
      }

      // 단어장 데이터 로드 (필요한 경우)
      await vocabularyActions.loadUserWords();

      // 복습할 단어들 로드
      if (wordIds.length > 0) {
        await loadWordsForReview(wordIds);
      } else {
        // 기본적으로 복습 대상 단어들 로드
        await loadDueWords();
      }

      isLoading = false;
    } catch (err) {
      console.error('Failed to initialize review session:', err);
      error = '복습 세션을 시작할 수 없습니다.';
      isLoading = false;
    }
  });

  async function loadWordsForReview(wordIds: string[]) {
    try {
      // 전체 단어장에서 특정 ID들만 필터링
      const allWords = get(vocabularyState).userWords;
      words = allWords.filter(word => wordIds.includes(word.id));
      
      if (words.length === 0) {
        error = '선택된 단어들을 찾을 수 없습니다.';
      }
    } catch (err) {
      console.error('Failed to load specific words:', err);
      error = '단어 로드에 실패했습니다.';
    }
  }

  async function loadDueWords() {
    try {
      // 복습이 필요한 단어들 (숙련도가 낮거나 오래된 단어들)
      const allWords = get(vocabularyState).userWords;
      
      // 숙련도 3 이하이거나 최근 7일 내 복습하지 않은 단어들
      const now = new Date();
      const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      
      words = allWords.filter(word => {
        const lastReviewed = word.lastReviewed ? new Date(word.lastReviewed) : new Date(0);
        return word.masteryLevel <= 3 || lastReviewed < sevenDaysAgo;
      }).slice(0, 15); // 최대 15개
      
      if (words.length === 0) {
        words = allWords.slice(0, 10); // 단어가 없으면 최근 10개
      }
    } catch (err) {
      console.error('Failed to load due words:', err);
      error = '복습 대상 단어 로드에 실패했습니다.';
    }
  }

  function handleReviewComplete(event: { detail: { results: ReviewResult } }) {
    const { results } = event.detail;
    
    // reviewActions를 통해 복습 종료 처리
    reviewActions.endReview();
    
    // 결과 페이지로 이동하거나 단어장으로 돌아가기
    goto(`/vocabulary?completed=true&accuracy=${Math.round(results.accuracyRate)}`);
  }

  function handleReviewExit() {
    // 사용자가 복습을 중단한 경우
    reviewActions.endReview();
    goto('/vocabulary');
  }
</script>

<svelte:head>
  <title>복습 - Kiko Vooster</title>
  <meta name="description" content="일본어 단어 복습 세션" />
</svelte:head>

{#if isLoading}
  <div class="loading-container">
    <div class="loading-content">
      <div class="loading-spinner"></div>
      <p>복습을 준비하고 있습니다...</p>
    </div>
  </div>
{:else if error}
  <div class="error-container">
    <div class="error-content">
      <div class="error-icon">
        <svg class="w-16 h-16 text-error" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.704-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
        </svg>
      </div>
      <h2 class="error-title">복습 시작 오류</h2>
      <p class="error-message">{error}</p>
      <div class="error-actions">
        <button 
          class="btn btn-primary" 
          on:click={() => goto('/vocabulary')}
        >
          단어장으로 돌아가기
        </button>
        <button 
          class="btn btn-ghost" 
          on:click={() => window.location.reload()}
        >
          다시 시도
        </button>
      </div>
    </div>
  </div>
{:else if words.length === 0}
  <div class="empty-container">
    <div class="empty-content">
      <div class="empty-icon">
        <svg class="w-16 h-16 text-base-content/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
        </svg>
      </div>
      <h2 class="empty-title">복습할 단어가 없습니다</h2>
      <p class="empty-message">단어장에 단어를 추가한 후 복습을 시작해보세요.</p>
      <div class="empty-actions">
        <button 
          class="btn btn-primary" 
          on:click={() => goto('/vocabulary')}
        >
          단어장으로 가기
        </button>
      </div>
    </div>
  </div>
{:else}
  <ReviewSession 
    {words} 
    {settings}
    on:complete={handleReviewComplete}
    on:exit={handleReviewExit}
  />
{/if}

<style>
  .loading-container, .error-container, .empty-container {
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 2rem;
    background: hsl(var(--b1));
  }

  .loading-content, .error-content, .empty-content {
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.5rem;
    max-width: 400px;
  }

  .loading-spinner {
    width: 3rem;
    height: 3rem;
    border: 3px solid hsl(var(--b3));
    border-top: 3px solid hsl(var(--p));
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  .error-icon, .empty-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 5rem;
    height: 5rem;
    border-radius: 50%;
    background: hsl(var(--er) / 0.1);
  }

  .empty-icon {
    background: hsl(var(--bc) / 0.1);
  }

  .error-title, .empty-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: hsl(var(--bc));
  }

  .error-message, .empty-message {
    color: hsl(var(--bc) / 0.7);
    line-height: 1.6;
  }

  .error-actions, .empty-actions {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    justify-content: center;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  /* 모바일 반응형 */
  @media (max-width: 640px) {
    .loading-container, .error-container, .empty-container {
      padding: 1rem;
    }

    .error-actions, .empty-actions {
      flex-direction: column;
      width: 100%;
      max-width: 250px;
    }

    .error-title, .empty-title {
      font-size: 1.25rem;
    }
  }

  /* 접근성 */
  @media (prefers-reduced-motion: reduce) {
    .loading-spinner {
      animation: none;
    }
  }
</style> 