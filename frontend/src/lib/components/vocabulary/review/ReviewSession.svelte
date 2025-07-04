<!--
  복습 세션 메인 컨테이너
  세 가지 복습 모드를 통합 관리하고 진행 상태를 추적
-->
<script lang="ts">
  import { createEventDispatcher, onDestroy } from 'svelte';
  import { get } from 'svelte/store';
  import { ReviewSessionMode } from '$lib/types/vocabulary';
  import { reviewActions, reviewProgress, currentReviewWord, isReviewComplete } from '$lib/stores/vocabularyStore';
  import FlashcardMode from './FlashcardMode.svelte';
  import FillInBlanksMode from './FillInBlanksMode.svelte';
  import SpellingMode from './SpellingMode.svelte';
  import ReviewProgress from './ReviewProgress.svelte';
  import type { 
    UserWord, 
    ReviewProgress as ReviewProgressType,
    ReviewSettings,
    ReviewResult
  } from '$lib/types/vocabulary';

  export let words: UserWord[] = [];
  export let settings: ReviewSettings = {
    mode: ReviewSessionMode.FLASHCARD,
    showReading: true,
    showExample: true,
    timeLimit: undefined,
    showHints: true,
    autoAdvance: false,
    shuffleWords: true,
    repeatIncorrect: true
  };

  const dispatch = createEventDispatcher<{
    complete: { results: ReviewResult };
    exit: void;
  }>();

  let currentIndex = 0;
  let reviewWords: UserWord[] = [];
  let sessionStartTime = Date.now();
  let responseTimes: number[] = [];
  let incorrectWords: UserWord[] = [];
  let showProgress = true;

  // 스토어에서 상태를 가져옴
  $: progress = $reviewProgress;
  $: currentWord = $currentReviewWord;
  $: isSessionCompleted = $isReviewComplete;

  // 세션 초기화
  function initializeSession() {
    if (!words.length) return;

    reviewWords = settings.shuffleWords ? shuffleArray([...words]) : [...words];
    currentIndex = 0;
    
    sessionStartTime = Date.now();
    responseTimes = [];
    incorrectWords = [];

    // reviewActions를 통해 복습 세션 시작
    // 이미 words가 전달되었으므로 별도 API 호출 없이 로컬 상태만 설정
  }

  function shuffleArray<T>(array: T[]): T[] {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  }

  async function handleAnswer(event: { detail: any }) {
    const { correct, responseTime, userAnswer, difficulty } = event.detail;
    
    if (!currentWord) return;

    try {
      // reviewActions를 통해 답변 제출
      await reviewActions.submitAnswer(
        userAnswer || '',
        correct,
        responseTime
      );

      responseTimes.push(responseTime);

      // 틀린 단어 수집 (나중에 다시 복습용)
      if (!correct && settings.repeatIncorrect) {
        incorrectWords.push(currentWord);
      }

      // 자동 진행이 아닌 경우 수동으로 다음 단어로 이동
      if (!settings.autoAdvance) {
        // UI에서 "다음" 버튼을 기다림
      } else {
        // 자동 진행인 경우 지연 후 다음 단어
        setTimeout(() => {
          nextWord();
        }, correct ? 1500 : 2500);
      }
    } catch (error) {
      console.error('Failed to submit answer:', error);
      // 에러가 발생해도 세션은 계속 진행
    }
  }

  function nextWord() {
    reviewActions.nextWord();
    
    // 세션 완료 체크
    if (get(isReviewComplete)) {
      completeSession();
    }
  }

  function completeSession() {
    const totalTime = Date.now() - sessionStartTime;
    const currentProgress = get(reviewProgress);
    
    if (!currentProgress) return;

    const results: ReviewResult = {
      totalWords: currentProgress.totalWords,
      correctAnswers: currentProgress.correctAnswers,
      incorrectAnswers: currentProgress.incorrectAnswers,
      accuracyRate: currentProgress.accuracyRate,
      averageResponseTime: currentProgress.averageResponseTime,
      totalTime,
      incorrectWords: incorrectWords.map(w => w.id),
      sessionDate: new Date().toISOString()
    };

    dispatch('complete', { results });
  }

  function exitSession() {
    dispatch('exit');
  }

  function restartSession() {
    // 틀린 단어들로 재시작하거나 전체 단어로 재시작
    const wordsToRestart = incorrectWords.length > 0 && settings.repeatIncorrect 
      ? incorrectWords 
      : reviewWords;
    
    words = wordsToRestart;
    incorrectWords = [];
    initializeSession();
  }

  function changeMode(newMode: ReviewSessionMode) {
    settings.mode = newMode;
    settings = { ...settings }; // reactive update
  }

  function toggleProgress() {
    showProgress = !showProgress;
  }

  function handleKeydown(event: KeyboardEvent) {
    if (isSessionCompleted) return;

    switch (event.key) {
      case 'Escape':
        exitSession();
        break;
      case 'ArrowRight':
      case ' ':
        if (!settings.autoAdvance) {
          event.preventDefault();
          nextWord();
        }
        break;
      case '1':
      case '2':
      case '3':
        // 플래시카드 모드에서 숫자키로 난이도 선택
        if (settings.mode === ReviewSessionMode.FLASHCARD) {
          event.preventDefault();
          const difficulty = ['hard', 'medium', 'easy'][parseInt(event.key) - 1] as 'hard' | 'medium' | 'easy';
          handleAnswer({
            detail: {
              correct: difficulty !== 'hard',
              responseTime: 0,
              difficulty
            }
          });
        }
        break;
    }
  }

  // 컴포넌트 마운트 시 세션 초기화
  $: if (words.length > 0) {
    initializeSession();
  }

  onDestroy(() => {
    // 정리 작업
  });
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="review-session">
  {#if !isSessionCompleted && currentWord}
    <!-- 헤더 -->
    <div class="session-header">
      <div class="header-left">
        <button 
          class="btn btn-ghost btn-sm" 
          on:click={exitSession}
          aria-label="복습 종료"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
          종료
        </button>
      </div>

      <div class="header-center">
        <div class="mode-selector">
          <button 
            class="btn btn-sm"
            class:btn-primary={settings.mode === ReviewSessionMode.FLASHCARD}
            class:btn-ghost={settings.mode !== ReviewSessionMode.FLASHCARD}
            on:click={() => changeMode(ReviewSessionMode.FLASHCARD)}
          >
            플래시카드
          </button>
          <button 
            class="btn btn-sm"
            class:btn-primary={settings.mode === ReviewSessionMode.FILL_IN_BLANKS}
            class:btn-ghost={settings.mode !== ReviewSessionMode.FILL_IN_BLANKS}
            on:click={() => changeMode(ReviewSessionMode.FILL_IN_BLANKS)}
          >
            빈칸채우기
          </button>
          <button 
            class="btn btn-sm"
            class:btn-primary={settings.mode === ReviewSessionMode.SPELLING}
            class:btn-ghost={settings.mode !== ReviewSessionMode.SPELLING}
            on:click={() => changeMode(ReviewSessionMode.SPELLING)}
          >
            철자게임
          </button>
        </div>
      </div>

      <div class="header-right">
        <button 
          class="btn btn-ghost btn-sm" 
          on:click={toggleProgress}
          aria-label="진행도 보기/숨기기"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4"></path>
          </svg>
          통계
        </button>
      </div>
    </div>

    <!-- 진행도 (선택적 표시) -->
    {#if showProgress && progress}
      <div class="progress-section">
        <ReviewProgress {progress} compact={true} />
      </div>
    {/if}

    <!-- 복습 모드 -->
    <div class="review-mode-container">
      {#if settings.mode === ReviewSessionMode.FLASHCARD}
        <FlashcardMode 
          word={currentWord}
          autoAdvance={settings.autoAdvance}
          timeLimit={settings.timeLimit}
          on:answer={handleAnswer}
          on:next={nextWord}
        />
      {:else if settings.mode === ReviewSessionMode.FILL_IN_BLANKS}
        <FillInBlanksMode 
          word={currentWord}
          autoAdvance={settings.autoAdvance}
          timeLimit={settings.timeLimit}
          showHint={settings.showHints}
          on:answer={handleAnswer}
          on:next={nextWord}
        />
      {:else if settings.mode === ReviewSessionMode.SPELLING}
        <SpellingMode 
          word={currentWord}
          autoAdvance={settings.autoAdvance}
          timeLimit={settings.timeLimit}
          showHints={settings.showHints}
          on:answer={handleAnswer}
          on:next={nextWord}
        />
      {/if}
    </div>
  {:else if isSessionCompleted}
    <!-- 완료 화면 -->
    <div class="completion-screen">
      <div class="completion-header">
        <div class="completion-icon">
          <svg class="w-16 h-16 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
        </div>
        <h2 class="completion-title">복습 완료!</h2>
        <p class="completion-subtitle">수고하셨습니다. 학습 결과를 확인해보세요.</p>
      </div>

      <div class="completion-stats">
        {#if progress}
          <ReviewProgress {progress} compact={false} />
        {/if}
      </div>

      <div class="completion-actions">
        <button 
          class="btn btn-primary" 
          on:click={restartSession}
        >
          다시 복습하기
        </button>
        <button 
          class="btn btn-ghost" 
          on:click={exitSession}
        >
          단어장으로 돌아가기
        </button>
      </div>
    </div>
  {:else}
    <!-- 로딩 또는 오류 상태 -->
    <div class="loading-screen">
      <div class="loading-content">
        <div class="loading-spinner"></div>
        <p>복습을 준비하고 있습니다...</p>
      </div>
    </div>
  {/if}
</div>

<style>
  .review-session {
    min-height: 100vh;
    background: hsl(var(--b1));
    display: flex;
    flex-direction: column;
  }

  .session-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background: hsl(var(--b2));
    border-bottom: 1px solid hsl(var(--b3));
    position: sticky;
    top: 0;
    z-index: 10;
  }

  .header-left, .header-right {
    flex: 1;
  }

  .header-right {
    display: flex;
    justify-content: flex-end;
  }

  .header-center {
    flex: 2;
    display: flex;
    justify-content: center;
  }

  .mode-selector {
    display: flex;
    gap: 0.5rem;
    background: hsl(var(--b3));
    padding: 0.25rem;
    border-radius: 0.75rem;
  }

  .progress-section {
    padding: 1rem 2rem;
    background: hsl(var(--b1));
    border-bottom: 1px solid hsl(var(--b3));
  }

  .review-mode-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 2rem;
    max-width: 1000px;
    margin: 0 auto;
    width: 100%;
  }

  .completion-screen {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 2rem;
    max-width: 800px;
    margin: 0 auto;
    width: 100%;
    gap: 2rem;
  }

  .completion-header {
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }

  .completion-icon {
    width: 5rem;
    height: 5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background: hsl(var(--su) / 0.1);
    border-radius: 50%;
  }

  .completion-title {
    font-size: 2rem;
    font-weight: 700;
    color: hsl(var(--bc));
  }

  .completion-subtitle {
    font-size: 1.1rem;
    color: hsl(var(--bc) / 0.7);
  }

  .completion-stats {
    width: 100%;
    max-width: 600px;
  }

  .completion-actions {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    justify-content: center;
  }

  .loading-screen {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 2rem;
  }

  .loading-content {
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }

  .loading-spinner {
    width: 3rem;
    height: 3rem;
    border: 3px solid hsl(var(--b3));
    border-top: 3px solid hsl(var(--p));
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  /* 모바일 반응형 */
  @media (max-width: 768px) {
    .session-header {
      padding: 0.75rem 1rem;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .header-center {
      order: 3;
      flex: 100%;
      margin-top: 0.5rem;
    }

    .mode-selector {
      width: 100%;
      justify-content: center;
    }

    .mode-selector .btn {
      flex: 1;
      font-size: 0.8rem;
    }

    .progress-section {
      padding: 0.75rem 1rem;
    }

    .review-mode-container {
      padding: 1rem;
    }

    .completion-screen {
      padding: 1.5rem 1rem;
      gap: 1.5rem;
    }

    .completion-title {
      font-size: 1.5rem;
    }

    .completion-actions {
      flex-direction: column;
      width: 100%;
      max-width: 300px;
    }
  }

  /* 접근성 */
  @media (prefers-reduced-motion: reduce) {
    .loading-spinner {
      animation: none;
    }
  }
</style> 