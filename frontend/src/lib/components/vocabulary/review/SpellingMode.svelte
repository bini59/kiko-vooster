<!--
  철자 게임 복습 모드
  단어의 철자를 순서대로 입력하여 학습하는 모드
-->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { UserWord, SpellingGameState, SpellingHint } from '$lib/types/vocabulary';

  export let word: UserWord;
  export let autoAdvance = false;
  export let timeLimit: number | undefined = undefined;
  export let showHints = true;

  const dispatch = createEventDispatcher<{
    answer: { correct: boolean; responseTime: number; userAnswer: string };
    next: void;
  }>();

  let state: SpellingGameState = {
    targetWord: '',
    userInput: '',
    hints: [],
    isSubmitted: false,
    showHiragana: false
  };

  let startTime = Date.now();
  let timeRemaining = timeLimit || 0;
  let timerInterval: number;
  let inputElement: HTMLInputElement;

  $: if (timeLimit && !state.isSubmitted) {
    clearInterval(timerInterval);
    timeRemaining = timeLimit;
    timerInterval = setInterval(() => {
      timeRemaining--;
      if (timeRemaining <= 0) {
        clearInterval(timerInterval);
        submitAnswer();
      }
    }, 1000);
  }

  function initializeSpelling() {
    if (!word.word?.text) return;
    
    state.targetWord = word.word.text;
    state.userInput = '';
    state.isSubmitted = false;
    state.showHiragana = false;
    
    // 힌트 생성
    if (showHints) {
      state.hints = generateHints(state.targetWord);
    } else {
      state.hints = [];
    }
  }

  function generateHints(targetWord: string): SpellingHint[] {
    const hints: SpellingHint[] = [];
    
    // 글자 수 힌트
    hints.push({
      type: 'length',
      value: `${targetWord.length}글자`,
      revealed: true
    });

    // 첫 글자 힌트
    if (targetWord.length > 1) {
      hints.push({
        type: 'character',
        value: `첫 글자: ${targetWord[0]}`,
        revealed: false
      });
    }

    // 마지막 글자 힌트
    if (targetWord.length > 2) {
      hints.push({
        type: 'character',
        value: `마지막 글자: ${targetWord[targetWord.length - 1]}`,
        revealed: false
      });
    }

    // 히라가나 읽기 힌트
    if (word.word?.reading) {
      hints.push({
        type: 'reading',
        value: `읽기: ${word.word.reading}`,
        revealed: false
      });
    }

    return hints;
  }

  function revealHint(index: number) {
    state.hints[index].revealed = true;
    state = { ...state }; // reactive update
  }

  function toggleHiragana() {
    state.showHiragana = !state.showHiragana;
  }

  function checkSpelling(): boolean {
    return state.userInput.trim() === state.targetWord;
  }

  function submitAnswer() {
    if (state.isSubmitted) return;
    
    state.isSubmitted = true;
    clearInterval(timerInterval);
    
    const responseTime = Date.now() - startTime;
    const correct = checkSpelling();
    
    dispatch('answer', {
      correct,
      responseTime,
      userAnswer: state.userInput
    });

    if (autoAdvance && correct) {
      setTimeout(() => {
        dispatch('next');
      }, 2000);
    }
  }

  function nextWord() {
    dispatch('next');
  }

  function reset() {
    state = {
      targetWord: '',
      userInput: '',
      hints: [],
      isSubmitted: false,
      showHiragana: false
    };
    startTime = Date.now();
    if (timeLimit) {
      timeRemaining = timeLimit;
    }
    initializeSpelling();
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !state.isSubmitted) {
      event.preventDefault();
      submitAnswer();
    }
  }

  function focusInput() {
    if (inputElement) {
      inputElement.focus();
    }
  }

  // 컴포넌트가 새 단어를 받으면 리셋
  $: if (word) {
    reset();
  }

  // 입력값 변화 감지
  $: {
    // 입력 중 실시간 피드백을 위한 로직 (선택적)
    if (state.userInput && !state.isSubmitted) {
      // 여기에 실시간 검증 로직 추가 가능
    }
  }
</script>

<div class="spelling-container">
  <!-- 타이머 표시 -->
  {#if timeLimit && !state.isSubmitted}
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

  <!-- 단어 정보 -->
  <div class="word-info">
    <div class="meaning-section">
      <span class="text-sm text-base-content/70">뜻</span>
      <div class="word-meaning">{word.word?.meaning || ''}</div>
    </div>
    
    {#if word.word?.exampleSentence}
      <div class="example-section">
        <span class="text-sm text-base-content/70">예문</span>
        <div class="example-sentence">{word.word.exampleSentence}</div>
        {#if word.word.exampleTranslation}
          <div class="example-translation">{word.word.exampleTranslation}</div>
        {/if}
      </div>
    {/if}
  </div>

  <!-- 철자 입력 -->
  <div class="spelling-input-section">
    <h3 class="instruction">일본어로 입력해주세요</h3>
    
    <div class="input-container">
      <input
        bind:this={inputElement}
        bind:value={state.userInput}
        type="text"
        class="spelling-input"
        class:correct={state.isSubmitted && checkSpelling()}
        class:incorrect={state.isSubmitted && !checkSpelling()}
        placeholder="ここに入力してください"
        disabled={state.isSubmitted}
        on:keydown={handleKeyDown}
        aria-label="단어 철자 입력"
        autocomplete="off"
        spellcheck="false"
      />
      
      <!-- 히라가나 표시 토글 (입력 중에만) -->
      {#if !state.isSubmitted && word.word?.reading}
        <button
          type="button"
          class="hiragana-toggle btn btn-ghost btn-sm"
          on:click={toggleHiragana}
          aria-label="히라가나 읽기 보기/숨기기"
        >
          {state.showHiragana ? '읽기 숨기기' : '읽기 보기'}
        </button>
      {/if}
    </div>

    {#if state.showHiragana && word.word?.reading}
      <div class="hiragana-display">
        📖 {word.word.reading}
      </div>
    {/if}
  </div>

  <!-- 힌트 섹션 -->
  {#if showHints && state.hints.length > 0}
    <div class="hints-section">
      <h4>💡 힌트</h4>
      <div class="hints-grid">
        {#each state.hints as hint, i}
          <div class="hint-item">
            {#if hint.revealed}
              <div class="hint-content revealed">
                {hint.value}
              </div>
            {:else}
              <button
                class="hint-button btn btn-outline btn-sm"
                on:click={() => revealHint(i)}
                disabled={state.isSubmitted}
              >
                힌트 {i + 1} 보기
              </button>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- 정답 표시 (제출 후) -->
  {#if state.isSubmitted}
    <div class="result-section">
      <div class="result-header">
        {#if checkSpelling()}
          <div class="success-message">
            <svg class="w-8 h-8 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            정답입니다!
          </div>
        {:else}
          <div class="error-message">
            <svg class="w-8 h-8 text-error" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            틀렸습니다
          </div>
        {/if}
      </div>

      <div class="answer-comparison">
        <div class="answer-row">
          <span class="label">정답:</span>
          <span class="correct-answer">{state.targetWord}</span>
          {#if word.word?.reading}
            <span class="reading">({word.word.reading})</span>
          {/if}
        </div>
        <div class="answer-row">
          <span class="label">입력:</span>
          <span class="user-answer" class:correct={checkSpelling()} class:incorrect={!checkSpelling()}>
            {state.userInput || '(미입력)'}
          </span>
        </div>
      </div>
    </div>
  {/if}

  <!-- 제출/다음 버튼 -->
  <div class="action-section">
    {#if !state.isSubmitted}
      <button 
        class="btn btn-primary" 
        on:click={submitAnswer}
        disabled={!state.userInput.trim()}
      >
        정답 확인
      </button>
      <button 
        class="btn btn-ghost btn-sm" 
        on:click={focusInput}
      >
        입력창 포커스
      </button>
    {:else if !autoAdvance}
      <button 
        class="btn btn-primary" 
        on:click={nextWord}
      >
        다음 단어
        <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
        </svg>
      </button>
    {/if}
  </div>
</div>

<style>
  .spelling-container {
    max-width: 600px;
    margin: 0 auto;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .word-info {
    background: hsl(var(--b2));
    border-radius: 1rem;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .meaning-section {
    text-align: center;
  }

  .word-meaning {
    font-size: 1.5rem;
    font-weight: 600;
    color: hsl(var(--p));
    margin-top: 0.5rem;
  }

  .example-section {
    padding: 1rem;
    background: hsl(var(--b3));
    border-radius: 0.75rem;
  }

  .example-sentence {
    font-size: 1.1rem;
    margin: 0.5rem 0;
    font-style: italic;
    color: hsl(var(--bc));
  }

  .example-translation {
    font-size: 0.9rem;
    color: hsl(var(--bc) / 0.7);
  }

  .spelling-input-section {
    background: hsl(var(--b1));
    border: 2px solid hsl(var(--b3));
    border-radius: 1rem;
    padding: 2rem;
    text-align: center;
  }

  .instruction {
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 1.5rem;
    color: hsl(var(--bc));
  }

  .input-container {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }

  .spelling-input {
    width: 100%;
    max-width: 300px;
    padding: 1rem 1.5rem;
    border: 3px solid hsl(var(--b3));
    border-radius: 0.75rem;
    font-size: 1.5rem;
    text-align: center;
    background: hsl(var(--b1));
    transition: all 0.2s ease;
    font-family: 'Hiragino Sans', 'Yu Gothic', sans-serif;
  }

  .spelling-input:focus {
    outline: none;
    border-color: hsl(var(--p));
    box-shadow: 0 0 0 4px hsl(var(--p) / 0.2);
    transform: scale(1.02);
  }

  .spelling-input.correct {
    border-color: hsl(var(--su));
    background: hsl(var(--su) / 0.1);
    color: hsl(var(--suc));
  }

  .spelling-input.incorrect {
    border-color: hsl(var(--er));
    background: hsl(var(--er) / 0.1);
    color: hsl(var(--erc));
  }

  .hiragana-toggle {
    margin-top: 0.5rem;
  }

  .hiragana-display {
    font-size: 1.2rem;
    color: hsl(var(--s));
    font-weight: 500;
    padding: 0.75rem 1rem;
    background: hsl(var(--s) / 0.1);
    border-radius: 0.5rem;
    margin-top: 0.5rem;
  }

  .hints-section {
    background: hsl(var(--n) / 0.05);
    border-radius: 1rem;
    padding: 1.5rem;
  }

  .hints-section h4 {
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 1rem;
    text-align: center;
  }

  .hints-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .hint-item {
    display: flex;
    justify-content: center;
  }

  .hint-button {
    width: 100%;
    max-width: 180px;
  }

  .hint-content.revealed {
    padding: 0.75rem 1rem;
    background: hsl(var(--a) / 0.1);
    border: 1px solid hsl(var(--a) / 0.3);
    border-radius: 0.5rem;
    text-align: center;
    font-weight: 500;
    color: hsl(var(--a));
    width: 100%;
    max-width: 180px;
  }

  .result-section {
    background: hsl(var(--b2));
    border-radius: 1rem;
    padding: 2rem;
    text-align: center;
  }

  .result-header {
    margin-bottom: 1.5rem;
  }

  .success-message, .error-message {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    font-size: 1.2rem;
    font-weight: 600;
  }

  .success-message {
    color: hsl(var(--su));
  }

  .error-message {
    color: hsl(var(--er));
  }

  .answer-comparison {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    max-width: 400px;
    margin: 0 auto;
  }

  .answer-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1rem;
    background: hsl(var(--b1));
    border-radius: 0.5rem;
  }

  .label {
    font-weight: 600;
    color: hsl(var(--bc) / 0.7);
  }

  .correct-answer {
    font-size: 1.2rem;
    font-weight: bold;
    color: hsl(var(--p));
  }

  .reading {
    font-size: 0.9rem;
    color: hsl(var(--bc) / 0.6);
    font-style: italic;
  }

  .user-answer.correct {
    color: hsl(var(--su));
    font-weight: 600;
  }

  .user-answer.incorrect {
    color: hsl(var(--er));
    font-weight: 600;
  }

  .action-section {
    display: flex;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .timer-bar {
    width: 100%;
  }

  /* 모바일 반응형 */
  @media (max-width: 640px) {
    .spelling-container {
      padding: 1rem;
      gap: 1.5rem;
    }

    .word-meaning {
      font-size: 1.3rem;
    }

    .spelling-input {
      font-size: 1.3rem;
      padding: 0.875rem 1.25rem;
      max-width: 100%;
    }

    .spelling-input-section {
      padding: 1.5rem;
    }

    .hints-grid {
      grid-template-columns: 1fr;
    }

    .answer-comparison {
      max-width: none;
    }

    .answer-row {
      flex-direction: column;
      gap: 0.5rem;
      text-align: center;
    }

    .action-section {
      flex-direction: column;
      align-items: center;
    }
  }

  /* 접근성 */
  @media (prefers-reduced-motion: reduce) {
    .spelling-input {
      transition: none;
      transform: none;
    }

    .spelling-input:focus {
      transform: none;
    }
  }
</style> 