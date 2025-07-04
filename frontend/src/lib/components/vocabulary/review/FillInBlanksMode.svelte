<!--
  빈칸 채우기 복습 모드
  예문에서 단어를 빈칸으로 만들어 맞추는 모드
-->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { UserWord, FillInBlanksState, BlankInfo } from '$lib/types/vocabulary';

  export let word: UserWord;
  export let autoAdvance = false;
  export let timeLimit: number | undefined = undefined;
  export let showHint = true;

  const dispatch = createEventDispatcher<{
    answer: { correct: boolean; responseTime: number; userAnswer: string };
    next: void;
  }>();

  let state: FillInBlanksState = {
    sentence: '',
    blanks: [],
    userAnswers: [],
    isSubmitted: false
  };

  let startTime = Date.now();
  let timeRemaining = timeLimit || 0;
  let timerInterval: number;
  let inputElements: HTMLInputElement[] = [];

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

  function initializeBlanks() {
    if (!word.word?.exampleSentence || !word.word?.text) {
      // 예문이 없는 경우 기본 문장 생성
      const wordText = word.word?.text || '';
      const meaning = word.word?.meaning || '';
      state.sentence = `___는 "${meaning}"라는 뜻입니다.`;
      state.blanks = [{
        index: 0,
        correctAnswer: wordText,
        hint: `${wordText.length}글자`,
        position: { start: 0, end: 3 }
      }];
    } else {
      // 예문에서 학습 단어를 찾아 빈칸으로 만들기
      const sentence = word.word.exampleSentence;
      const targetWord = word.word.text;
      
      // 단어의 모든 출현 위치 찾기
      const positions: { start: number; end: number }[] = [];
      let index = sentence.indexOf(targetWord);
      
      while (index !== -1) {
        positions.push({
          start: index,
          end: index + targetWord.length
        });
        index = sentence.indexOf(targetWord, index + 1);
      }

      if (positions.length === 0) {
        // 단어가 예문에 없는 경우 기본 문장 사용
        state.sentence = `___는 "${word.word.meaning}"라는 뜻입니다.`;
        state.blanks = [{
          index: 0,
          correctAnswer: targetWord,
          hint: `${targetWord.length}글자`,
          position: { start: 0, end: 3 }
        }];
      } else {
        // 빈칸으로 만들 위치들을 뒤에서부터 처리 (인덱스 변화 방지)
        let modifiedSentence = sentence;
        const blanks: BlankInfo[] = [];
        
        positions.reverse().forEach((pos, i) => {
          const blankPlaceholder = `___${positions.length - 1 - i}___`;
          modifiedSentence = modifiedSentence.substring(0, pos.start) + 
                           blankPlaceholder + 
                           modifiedSentence.substring(pos.end);
          
          blanks.unshift({
            index: positions.length - 1 - i,
            correctAnswer: targetWord,
            hint: showHint ? getHint(targetWord) : undefined,
            position: pos
          });
        });

        state.sentence = modifiedSentence;
        state.blanks = blanks;
      }
    }

    state.userAnswers = new Array(state.blanks.length).fill('');
    state.isSubmitted = false;
  }

  function getHint(word: string): string {
    if (word.length <= 2) {
      return `${word.length}글자`;
    } else if (word.length <= 4) {
      return `${word[0]}..${word[word.length - 1]} (${word.length}글자)`;
    } else {
      return `${word[0]}...${word[word.length - 1]} (${word.length}글자)`;
    }
  }

  function updateAnswer(index: number, value: string) {
    state.userAnswers[index] = value;
  }

  function submitAnswer() {
    if (state.isSubmitted) return;
    
    state.isSubmitted = true;
    clearInterval(timerInterval);
    
    const responseTime = Date.now() - startTime;
    const allCorrect = state.blanks.every((blank, i) => {
      return state.userAnswers[i].trim() === blank.correctAnswer;
    });
    
    const userAnswer = state.userAnswers.join(', ');
    
    dispatch('answer', {
      correct: allCorrect,
      responseTime,
      userAnswer
    });

    if (autoAdvance && allCorrect) {
      setTimeout(() => {
        dispatch('next');
      }, 2000);
    }
  }

  function nextWord() {
    dispatch('next');
  }

  function checkAnswer(index: number): boolean {
    if (!state.isSubmitted) return false;
    return state.userAnswers[index].trim() === state.blanks[index].correctAnswer;
  }

  function reset() {
    state = {
      sentence: '',
      blanks: [],
      userAnswers: [],
      isSubmitted: false
    };
    startTime = Date.now();
    if (timeLimit) {
      timeRemaining = timeLimit;
    }
    initializeBlanks();
  }

  function focusNextInput(currentIndex: number) {
    const nextIndex = currentIndex + 1;
    if (nextIndex < inputElements.length && inputElements[nextIndex]) {
      inputElements[nextIndex].focus();
    } else if (currentIndex === inputElements.length - 1) {
      // 마지막 입력칸에서 Enter 시 제출
      submitAnswer();
    }
  }

  // 컴포넌트가 새 단어를 받으면 리셋
  $: if (word) {
    reset();
  }

  // 렌더링된 문장을 반환하는 함수
  function renderSentence(): string {
    let rendered = state.sentence;
    state.blanks.forEach((blank, i) => {
      const placeholder = `___${blank.index}___`;
      const inputHtml = `<span class="blank-input-container" data-index="${i}"></span>`;
      rendered = rendered.replace(placeholder, inputHtml);
    });
    return rendered;
  }
</script>

<div class="fill-blanks-container">
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

  <!-- 학습 단어 표시 -->
  <div class="word-info">
    <div class="study-word">
      <span class="text-sm text-base-content/70">학습 단어</span>
      <div class="word-display">
        <span class="word-text">{word.word?.text || ''}</span>
        {#if word.word?.reading}
          <span class="word-reading">({word.word.reading})</span>
        {/if}
      </div>
      <div class="word-meaning">{word.word?.meaning || ''}</div>
    </div>
  </div>

  <!-- 빈칸 채우기 문제 -->
  <div class="sentence-container">
    <h3 class="instruction">다음 문장의 빈칸을 채워주세요</h3>
    
    <div class="sentence-display">
      {#each state.sentence.split(/___\d+___/) as part, i}
        {part}
        {#if i < state.blanks.length}
          <span class="blank-wrapper">
            <input
              bind:this={inputElements[i]}
              type="text"
              class="blank-input"
              class:correct={state.isSubmitted && checkAnswer(i)}
              class:incorrect={state.isSubmitted && !checkAnswer(i)}
              bind:value={state.userAnswers[i]}
              on:input={(e) => updateAnswer(i, (e.target as HTMLInputElement).value)}
              on:keydown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  focusNextInput(i);
                }
              }}
              disabled={state.isSubmitted}
              placeholder="____"
              aria-label={`빈칸 ${i + 1}`}
            />
            {#if showHint && state.blanks[i].hint}
              <div class="hint">💡 {state.blanks[i].hint}</div>
            {/if}
          </span>
        {/if}
      {/each}
    </div>

    <!-- 정답 표시 (제출 후) -->
    {#if state.isSubmitted}
      <div class="answer-section">
        <h4>정답</h4>
        <div class="correct-answers">
          {#each state.blanks as blank, i}
            <div class="answer-item">
              <span class="answer-number">{i + 1}.</span>
              <span class="answer-text">{blank.correctAnswer}</span>
              <span class="user-answer" class:correct={checkAnswer(i)} class:incorrect={!checkAnswer(i)}>
                → {state.userAnswers[i] || '(미입력)'}
                {#if checkAnswer(i)}
                  <svg class="w-4 h-4 text-success inline ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                  </svg>
                {:else}
                  <svg class="w-4 h-4 text-error inline ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                {/if}
              </span>
            </div>
          {/each}
        </div>

        <!-- 예문 번역 (있는 경우) -->
        {#if word.word?.exampleTranslation}
          <div class="translation">
            <strong>번역:</strong> {word.word.exampleTranslation}
          </div>
        {/if}
      </div>
    {/if}
  </div>

  <!-- 제출/다음 버튼 -->
  <div class="action-section">
    {#if !state.isSubmitted}
      <button 
        class="btn btn-primary" 
        on:click={submitAnswer}
        disabled={state.userAnswers.every(answer => !answer.trim())}
      >
        정답 확인
      </button>
    {:else if !autoAdvance}
      <button 
        class="btn btn-primary" 
        on:click={nextWord}
      >
        다음 문제
        <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
        </svg>
      </button>
    {/if}
  </div>
</div>

<style>
  .fill-blanks-container {
    max-width: 700px;
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
    text-align: center;
  }

  .study-word {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    align-items: center;
  }

  .word-display {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    justify-content: center;
  }

  .word-text {
    font-size: 1.8rem;
    font-weight: bold;
    color: hsl(var(--p));
  }

  .word-reading {
    font-size: 1rem;
    color: hsl(var(--bc) / 0.7);
    font-style: italic;
  }

  .word-meaning {
    font-size: 1.1rem;
    color: hsl(var(--s));
    font-weight: 500;
  }

  .sentence-container {
    background: hsl(var(--b1));
    border: 2px solid hsl(var(--b3));
    border-radius: 1rem;
    padding: 2rem;
  }

  .instruction {
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 1.5rem;
    text-align: center;
    color: hsl(var(--bc));
  }

  .sentence-display {
    font-size: 1.3rem;
    line-height: 2;
    text-align: center;
    margin-bottom: 1.5rem;
  }

  .blank-wrapper {
    position: relative;
    display: inline-block;
    margin: 0 0.25rem;
  }

  .blank-input {
    display: inline-block;
    width: auto;
    min-width: 80px;
    max-width: 150px;
    padding: 0.5rem 0.75rem;
    border: 2px solid hsl(var(--b3));
    border-radius: 0.5rem;
    font-size: 1.2rem;
    text-align: center;
    background: hsl(var(--b1));
    transition: all 0.2s ease;
  }

  .blank-input:focus {
    outline: none;
    border-color: hsl(var(--p));
    box-shadow: 0 0 0 3px hsl(var(--p) / 0.2);
  }

  .blank-input.correct {
    border-color: hsl(var(--su));
    background: hsl(var(--su) / 0.1);
    color: hsl(var(--suc));
  }

  .blank-input.incorrect {
    border-color: hsl(var(--er));
    background: hsl(var(--er) / 0.1);
    color: hsl(var(--erc));
  }

  .hint {
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    background: hsl(var(--n));
    color: hsl(var(--nc));
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.75rem;
    white-space: nowrap;
    margin-top: 0.25rem;
    opacity: 0.8;
  }

  .answer-section {
    margin-top: 2rem;
    padding: 1.5rem;
    background: hsl(var(--b2));
    border-radius: 0.75rem;
  }

  .answer-section h4 {
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 1rem;
    text-align: center;
  }

  .correct-answers {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .answer-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: hsl(var(--b1));
    border-radius: 0.5rem;
  }

  .answer-number {
    font-weight: 600;
    color: hsl(var(--p));
    min-width: 1.5rem;
  }

  .answer-text {
    font-weight: 600;
    color: hsl(var(--bc));
  }

  .user-answer {
    margin-left: auto;
    display: flex;
    align-items: center;
  }

  .user-answer.correct {
    color: hsl(var(--su));
  }

  .user-answer.incorrect {
    color: hsl(var(--er));
  }

  .translation {
    margin-top: 1rem;
    padding: 1rem;
    background: hsl(var(--b3));
    border-radius: 0.5rem;
    font-style: italic;
  }

  .action-section {
    text-align: center;
  }

  .timer-bar {
    width: 100%;
  }

  /* 모바일 반응형 */
  @media (max-width: 640px) {
    .fill-blanks-container {
      padding: 1rem;
      gap: 1.5rem;
    }

    .word-text {
      font-size: 1.5rem;
    }

    .sentence-display {
      font-size: 1.1rem;
      line-height: 1.8;
    }

    .blank-input {
      min-width: 60px;
      font-size: 1rem;
      padding: 0.4rem 0.6rem;
    }

    .word-info {
      padding: 1rem;
    }

    .sentence-container {
      padding: 1.5rem;
    }

    .answer-item {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }

    .user-answer {
      margin-left: 0;
    }
  }

  /* 접근성 */
  @media (prefers-reduced-motion: reduce) {
    .blank-input {
      transition: none;
    }
  }
</style> 