<!--
  플래시카드 복습 모드
  앞면(단어)/뒷면(뜻) 전환하며 학습하는 모드
-->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { UserWord, FlashcardState } from '$lib/types/vocabulary';

  export let word: UserWord;
  export let autoAdvance = false;
  export let timeLimit: number | undefined = undefined;

  const dispatch = createEventDispatcher<{
    answer: { correct: boolean; responseTime: number; difficulty: 'easy' | 'medium' | 'hard' };
    next: void;
  }>();

  let state: FlashcardState = {
    showAnswer: false,
    isAnswered: false,
    difficulty: 'medium'
  };

  let startTime = Date.now();
  let timeRemaining = timeLimit || 0;
  let timerInterval: number;

  $: if (timeLimit && !state.isAnswered) {
    clearInterval(timerInterval);
    timeRemaining = timeLimit;
    timerInterval = setInterval(() => {
      timeRemaining--;
      if (timeRemaining <= 0) {
        clearInterval(timerInterval);
        showAnswer();
      }
    }, 1000);
  }

  function flipCard() {
    if (!state.isAnswered) {
      state.showAnswer = !state.showAnswer;
    }
  }

  function showAnswer() {
    state.showAnswer = true;
  }

  function selectDifficulty(difficulty: 'easy' | 'medium' | 'hard') {
    state.difficulty = difficulty;
    state.isAnswered = true;
    
    const responseTime = Date.now() - startTime;
    const correct = difficulty !== 'hard'; // hard는 틀린 것으로 간주

    clearInterval(timerInterval);
    
    dispatch('answer', { 
      correct, 
      responseTime, 
      difficulty 
    });

    if (autoAdvance) {
      setTimeout(() => {
        dispatch('next');
      }, 1500);
    }
  }

  function nextWord() {
    dispatch('next');
  }

  function reset() {
    state = {
      showAnswer: false,
      isAnswered: false,
      difficulty: 'medium'
    };
    startTime = Date.now();
    if (timeLimit) {
      timeRemaining = timeLimit;
    }
  }

  // 컴포넌트가 새 단어를 받으면 리셋
  $: if (word) {
    reset();
  }
</script>

<div class="flashcard-container">
  <!-- 타이머 표시 -->
  {#if timeLimit && !state.isAnswered}
    <div class="timer-bar mb-4">
      <div class="flex justify-between items-center mb-2">
        <span class="text-sm text-base-content/70">남은 시간</span>
        <span class="text-sm font-mono">{timeRemaining}초</span>
      </div>
      <progress 
        class="progress progress-primary w-full" 
        value={timeRemaining} 
        max={timeLimit}
        aria-label="남은 시간"
      ></progress>
    </div>
  {/if}

  <!-- 플래시카드 -->
  <div 
    class="flashcard" 
    class:flipped={state.showAnswer}
    on:click={flipCard}
    on:keydown={(e) => e.key === 'Enter' || e.key === ' ' ? flipCard() : null}
    tabindex="0"
    role="button"
    aria-label="플래시카드 클릭하여 답 확인"
  >
    <div class="flashcard-inner">
      <!-- 앞면 (질문) -->
      <div class="flashcard-front">
        <div class="card-content">
          <div class="word-text">{word.word?.text || ''}</div>
          {#if word.word?.reading}
            <div class="word-reading">{word.word.reading}</div>
          {/if}
          
          <div class="instruction">
            <svg class="w-6 h-6 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122"></path>
            </svg>
            <p class="text-sm">클릭하여 뜻 확인</p>
          </div>
        </div>
      </div>

      <!-- 뒷면 (답) -->
      <div class="flashcard-back">
        <div class="card-content">
          <div class="word-meaning">{word.word?.meaning || ''}</div>
          
          {#if word.word?.exampleSentence}
            <div class="example-section">
              <div class="example-sentence">{word.word.exampleSentence}</div>
              {#if word.word.exampleTranslation}
                <div class="example-translation">{word.word.exampleTranslation}</div>
              {/if}
            </div>
          {/if}

          <div class="difficulty-section">
            <p class="difficulty-question">얼마나 잘 기억하셨나요?</p>
            <div class="difficulty-buttons">
              <button 
                class="btn btn-error btn-sm" 
                on:click|stopPropagation={() => selectDifficulty('hard')}
                disabled={state.isAnswered}
              >
                어려움
              </button>
              <button 
                class="btn btn-warning btn-sm" 
                on:click|stopPropagation={() => selectDifficulty('medium')}
                disabled={state.isAnswered}
              >
                보통
              </button>
              <button 
                class="btn btn-success btn-sm" 
                on:click|stopPropagation={() => selectDifficulty('easy')}
                disabled={state.isAnswered}
              >
                쉬움
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 답변 완료 후 다음 버튼 -->
  {#if state.isAnswered && !autoAdvance}
    <div class="next-section">
      <button 
        class="btn btn-primary" 
        on:click={nextWord}
      >
        다음 단어
        <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
        </svg>
      </button>
    </div>
  {/if}
</div>

<style>
  .flashcard-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.5rem;
    max-width: 500px;
    margin: 0 auto;
    padding: 1rem;
  }

  .flashcard {
    width: 100%;
    height: 400px;
    perspective: 1000px;
    cursor: pointer;
    border-radius: 1rem;
  }

  .flashcard-inner {
    position: relative;
    width: 100%;
    height: 100%;
    text-align: center;
    transition: transform 0.6s;
    transform-style: preserve-3d;
  }

  .flashcard.flipped .flashcard-inner {
    transform: rotateY(180deg);
  }

  .flashcard-front, .flashcard-back {
    position: absolute;
    width: 100%;
    height: 100%;
    backface-visibility: hidden;
    border-radius: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  }

  .flashcard-front {
    background: linear-gradient(135deg, hsl(var(--p)) 0%, hsl(var(--s)) 100%);
    color: hsl(var(--pc));
  }

  .flashcard-back {
    background: linear-gradient(135deg, hsl(var(--s)) 0%, hsl(var(--a)) 100%);
    color: hsl(var(--sc));
    transform: rotateY(180deg);
  }

  .card-content {
    padding: 2rem;
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    gap: 1rem;
  }

  .word-text {
    font-size: 2.5rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
  }

  .word-reading {
    font-size: 1.2rem;
    opacity: 0.9;
    font-style: italic;
  }

  .word-meaning {
    font-size: 1.8rem;
    font-weight: 600;
    margin-bottom: 1rem;
  }

  .instruction {
    margin-top: auto;
    opacity: 0.8;
  }

  .example-section {
    margin: 1rem 0;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 0.5rem;
    backdrop-filter: blur(10px);
  }

  .example-sentence {
    font-size: 1rem;
    margin-bottom: 0.5rem;
    font-style: italic;
  }

  .example-translation {
    font-size: 0.9rem;
    opacity: 0.8;
  }

  .difficulty-section {
    margin-top: auto;
  }

  .difficulty-question {
    font-size: 1rem;
    margin-bottom: 1rem;
    font-weight: 500;
  }

  .difficulty-buttons {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    justify-content: center;
  }

  .next-section {
    text-align: center;
  }

  .timer-bar {
    width: 100%;
    max-width: 500px;
  }

  /* 모바일 반응형 */
  @media (max-width: 640px) {
    .flashcard {
      height: 350px;
    }

    .word-text {
      font-size: 2rem;
    }

    .word-meaning {
      font-size: 1.5rem;
    }

    .card-content {
      padding: 1.5rem;
    }

    .difficulty-buttons {
      gap: 0.25rem;
    }

    .difficulty-buttons .btn {
      font-size: 0.8rem;
      padding: 0.5rem 0.75rem;
    }
  }

  /* 접근성 */
  .flashcard:focus {
    outline: 2px solid hsl(var(--pf));
    outline-offset: 2px;
  }

  /* 애니메이션 감소 설정 */
  @media (prefers-reduced-motion: reduce) {
    .flashcard-inner {
      transition: none;
    }
  }
</style> 