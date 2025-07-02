<!--
  단어 카드 컴포넌트
  
  단어장에서 각 단어를 표시하는 기본 단위입니다.
  단어 정보, 숙련도, 태그를 표시하고 클릭/편집 기능을 제공합니다.
-->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { UserWord } from '$lib/types/vocabulary';
  
  export let userWord: UserWord;
  export let compact = false;
  export let showActions = true;
  export let showProgress = true;
  export let clickable = true;
  
  const dispatch = createEventDispatcher<{
    click: UserWord;
    edit: UserWord;
    remove: UserWord;
    updateMastery: { word: UserWord; level: number };
    addTag: { word: UserWord; tag: string };
    removeTag: { word: UserWord; tag: string };
  }>();
  
  $: word = userWord.word;
  $: difficultyColor = getDifficultyColor(word?.difficultyLevel || 'beginner');
  $: masteryPercentage = (userWord.masteryLevel / 5) * 100;
  $: masteryColor = getMasteryColor(userWord.masteryLevel);
  
  function getDifficultyColor(difficulty: string): string {
    switch (difficulty) {
      case 'beginner': return 'bg-green-100 text-green-800 border-green-200';
      case 'intermediate': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'advanced': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  }
  
  function getMasteryColor(level: number): string {
    if (level <= 1) return 'bg-red-500';
    if (level <= 2) return 'bg-orange-500';
    if (level <= 3) return 'bg-yellow-500';
    if (level <= 4) return 'bg-blue-500';
    return 'bg-green-500';
  }
  
  function handleCardClick() {
    if (clickable) {
      dispatch('click', userWord);
    }
  }
  
  function handleEditClick(event: Event) {
    event.stopPropagation();
    dispatch('edit', userWord);
  }
  
  function handleRemoveClick(event: Event) {
    event.stopPropagation();
    dispatch('remove', userWord);
  }
  
  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }
  
  function getTimeSinceAdded(dateString: string): string {
    const now = new Date();
    const added = new Date(dateString);
    const diffMs = now.getTime() - added.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return '오늘';
    if (diffDays === 1) return '어제';
    if (diffDays < 7) return `${diffDays}일 전`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)}주 전`;
    return `${Math.floor(diffDays / 30)}개월 전`;
  }
  
  let showTagInput = false;
  let newTag = '';
  
  function handleAddTag() {
    if (newTag.trim()) {
      dispatch('addTag', { word: userWord, tag: newTag.trim() });
      newTag = '';
      showTagInput = false;
    }
  }
  
  function handleRemoveTag(tag: string, event: Event) {
    event.stopPropagation();
    dispatch('removeTag', { word: userWord, tag });
  }
</script>

<article 
  class="card bg-base-100 shadow-sm border border-base-200 hover:shadow-md transition-all duration-200"
  class:card-compact={compact}
  class:cursor-pointer={clickable}
  class:hover:border-primary={clickable}
  role={clickable ? "button" : "article"}
  tabindex={clickable ? 0 : -1}
  on:click={handleCardClick}
  on:keydown={(e) => e.key === 'Enter' && handleCardClick()}
  aria-label={word ? `${word.text} 단어 카드` : '단어 카드'}
>
  <div class="card-body" class:p-4={compact} class:p-6={!compact}>
    <!-- 카드 헤더 -->
    <div class="flex items-start justify-between">
      <!-- 단어 정보 -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-2">
          <!-- 일본어 텍스트 -->
          <h3 class="text-lg font-bold text-base-content truncate">
            {word?.text || '단어 없음'}
          </h3>
          
          <!-- 난이도 뱃지 -->
          {#if word?.difficultyLevel}
            <span class="badge badge-sm {difficultyColor}">
              {word.difficultyLevel}
            </span>
          {/if}
        </div>
        
        <!-- 읽기 (후리가나) -->
        {#if word?.reading && word.reading !== word.text}
          <p class="text-sm text-base-content/70 mb-1">
            {word.reading}
          </p>
        {/if}
        
        <!-- 의미 -->
        <p class="text-base text-base-content mb-3 line-clamp-2">
          {word?.meaning || '의미 없음'}
        </p>
      </div>
      
      <!-- 액션 버튼들 -->
      {#if showActions}
        <div class="flex items-center gap-1 ml-4">
          <button
            class="btn btn-ghost btn-sm btn-square"
            on:click={handleEditClick}
            aria-label="단어 편집"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
            </svg>
          </button>
          
          <button
            class="btn btn-ghost btn-sm btn-square text-error hover:bg-error/10"
            on:click={handleRemoveClick}
            aria-label="단어 삭제"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
          </button>
        </div>
      {/if}
    </div>
    
    <!-- 숙련도 표시 -->
    {#if showProgress && !compact}
      <div class="mb-3">
        <div class="flex items-center justify-between text-xs text-base-content/60 mb-1">
          <span>숙련도</span>
          <span>{userWord.masteryLevel}/5</span>
        </div>
        
        <div class="w-full bg-base-200 rounded-full h-2">
          <div 
            class="h-2 rounded-full transition-all duration-300 {masteryColor}"
            style="width: {masteryPercentage}%"
          ></div>
        </div>
      </div>
    {/if}
    
    <!-- 태그들 -->
    {#if userWord.tags.length > 0 || showTagInput}
      <div class="flex flex-wrap gap-1 mb-3">
        {#each userWord.tags as tag}
          <span class="badge badge-primary badge-sm gap-1">
            {tag}
            {#if showActions}
              <button
                class="btn btn-ghost btn-xs btn-square p-0"
                on:click={(e) => handleRemoveTag(tag, e)}
                aria-label="태그 제거"
              >
                <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            {/if}
          </span>
        {/each}
        
        {#if showTagInput && showActions}
          <div class="flex items-center gap-1">
            <input
              bind:value={newTag}
              class="input input-xs input-bordered w-20"
              placeholder="태그"
              on:keydown={(e) => e.key === 'Enter' && handleAddTag()}
              on:blur={() => { showTagInput = false; newTag = ''; }}
            />
            <button
              class="btn btn-ghost btn-xs"
              on:click={handleAddTag}
              aria-label="태그 추가"
            >
              ✓
            </button>
          </div>
        {:else if showActions}
          <button
            class="badge badge-outline badge-sm hover:badge-primary"
            on:click={() => showTagInput = true}
            aria-label="새 태그 추가"
          >
            +
          </button>
        {/if}
      </div>
    {/if}
    
    <!-- 메타 정보 -->
    {#if !compact}
      <div class="flex items-center justify-between text-xs text-base-content/60">
        <div class="flex items-center gap-3">
          <span>추가: {getTimeSinceAdded(userWord.addedAt)}</span>
          
          {#if userWord.lastReviewed}
            <span>복습: {getTimeSinceAdded(userWord.lastReviewed)}</span>
          {/if}
          
          {#if userWord.reviewCount > 0}
            <span>복습 {userWord.reviewCount}회</span>
          {/if}
        </div>
        
        <!-- 품사 정보 -->
        {#if word?.partOfSpeech}
          <span class="badge badge-ghost badge-xs">
            {word.partOfSpeech}
          </span>
        {/if}
      </div>
    {/if}
    
    <!-- 노트 (있는 경우만) -->
    {#if userWord.notes && !compact}
      <div class="mt-3 p-3 bg-base-200/50 rounded-lg">
        <p class="text-sm text-base-content/80 italic">
          "{userWord.notes}"
        </p>
      </div>
    {/if}
  </div>
</article>

<style>
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style> 