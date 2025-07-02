<!--
  단어 검색 바 컴포넌트
  
  JMdict 사전에서 단어를 검색하고 결과를 표시하는 컴포넌트입니다.
  검색 결과에서 단어를 선택하여 단어장에 추가할 수 있습니다.
-->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { debounce } from '$lib/utils/debounce';
  import { SearchType } from '$lib/types/vocabulary';
  import type { Word } from '$lib/types/vocabulary';
  
  export let searchResults: Word[] = [];
  export let loading = false;
  export let error: string | null = null;
  export let placeholder = "단어를 검색하세요...";
  export let showTypeSelector = true;
  export let showResultsInline = true;
  export let maxResults = 10;
  
  const dispatch = createEventDispatcher<{
    search: { query: string; searchType: SearchType };
    select: Word;
    addToVocabulary: Word;
    clear: void;
  }>();
  
  // 상태 변수들
  let searchQuery = '';
  let searchType: SearchType = SearchType.ALL;
  let showResults = false;
  let selectedIndex = -1;
  let searchInput: HTMLInputElement;
  
  // 디바운스된 검색 함수
  const debouncedSearch = debounce((query: string) => {
    if (query.trim().length >= 2) {
      dispatch('search', { query: query.trim(), searchType });
      showResults = true;
    } else {
      dispatch('clear');
      showResults = false;
    }
  }, 300);
  
  // 리액티브 변수들
  $: filteredResults = searchResults.slice(0, maxResults);
  $: hasResults = filteredResults.length > 0;
  
  // 이벤트 핸들러들
  function handleInput(event: Event) {
    const target = event.target as HTMLInputElement;
    searchQuery = target.value;
    selectedIndex = -1;
    debouncedSearch(searchQuery);
  }
  
  function handleSearchTypeChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    searchType = target.value as SearchType;
    
    if (searchQuery.trim().length >= 2) {
      dispatch('search', { query: searchQuery.trim(), searchType });
    }
  }
  
  function handleKeydown(event: KeyboardEvent) {
    if (!showResults || !hasResults) return;
    
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        selectedIndex = Math.min(selectedIndex + 1, filteredResults.length - 1);
        break;
        
      case 'ArrowUp':
        event.preventDefault();
        selectedIndex = Math.max(selectedIndex - 1, -1);
        break;
        
      case 'Enter':
        event.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < filteredResults.length) {
          handleWordSelect(filteredResults[selectedIndex]);
        }
        break;
        
      case 'Escape':
        event.preventDefault();
        hideResults();
        break;
    }
  }
  
  function handleWordSelect(word: Word) {
    dispatch('select', word);
    hideResults();
  }
  
  function handleAddToVocabulary(word: Word, event?: Event) {
    if (event) {
      event.stopPropagation();
    }
    dispatch('addToVocabulary', word);
  }
  
  function hideResults() {
    showResults = false;
    selectedIndex = -1;
  }
  
  function clearSearch() {
    searchQuery = '';
    dispatch('clear');
    hideResults();
    searchInput?.focus();
  }
  
  function getDifficultyColor(difficulty: string): string {
    switch (difficulty) {
      case 'beginner': return 'badge-success';
      case 'intermediate': return 'badge-warning';
      case 'advanced': return 'badge-error';
      default: return 'badge-ghost';
    }
  }
  
  // 외부 클릭으로 결과 숨기기
  function handleClickOutside(event: Event) {
    const target = event.target as Element;
    if (!target.closest('.search-container')) {
      hideResults();
    }
  }
</script>

<svelte:window on:click={handleClickOutside} />

<div class="search-container relative">
  <!-- 검색 입력 영역 -->
  <div class="flex gap-2">
    <!-- 검색 입력 -->
    <div class="flex-1 relative">
      <input
        bind:this={searchInput}
        type="text"
        class="input input-bordered w-full pr-10"
        {placeholder}
        bind:value={searchQuery}
        on:input={handleInput}
        on:keydown={handleKeydown}
        on:focus={() => {
          if (hasResults && searchQuery.trim()) {
            showResults = true;
          }
        }}
        aria-label="단어 검색"
        autocomplete="off"
      />
      
      <!-- 검색 아이콘 / 로딩 / 클리어 버튼 -->
      <div class="absolute inset-y-0 right-0 flex items-center pr-3">
        {#if loading}
          <span class="loading loading-spinner loading-sm"></span>
        {:else if searchQuery}
          <button
            class="btn btn-ghost btn-xs btn-square"
            on:click={clearSearch}
            aria-label="검색어 지우기"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        {:else}
          <svg class="w-5 h-5 text-base-content/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
        {/if}
      </div>
    </div>
    
    <!-- 검색 타입 선택 -->
    {#if showTypeSelector}
      <select
        class="select select-bordered w-32"
        bind:value={searchType}
        on:change={handleSearchTypeChange}
        aria-label="검색 타입"
      >
        <option value={SearchType.ALL}>전체</option>
        <option value={SearchType.KANJI}>한자</option>
        <option value={SearchType.HIRAGANA}>히라가나</option>
        <option value={SearchType.MEANING}>의미</option>
      </select>
    {/if}
  </div>
  
  <!-- 에러 메시지 -->
  {#if error}
    <div class="alert alert-error mt-2">
      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
      <span>{error}</span>
    </div>
  {/if}
  
  <!-- 검색 결과 드롭다운 -->
  {#if showResults && showResultsInline}
    <div class="absolute top-full left-0 right-0 z-50 mt-1">
      <div class="card bg-base-100 shadow-xl border border-base-300 max-h-96 overflow-y-auto">
        <div class="card-body p-2">
          {#if loading}
            <!-- 로딩 상태 -->
            <div class="flex items-center justify-center py-8">
              <span class="loading loading-spinner loading-md"></span>
              <span class="ml-2 text-base-content/60">검색 중...</span>
            </div>
          {:else if hasResults}
            <!-- 검색 결과 -->
            <div class="space-y-1">
              {#each filteredResults as word, index (word.id)}
                <button
                  class="w-full text-left p-3 rounded-lg transition-colors"
                  class:bg-primary/10={index === selectedIndex}
                  class:hover:bg-base-200={index !== selectedIndex}
                  on:click={() => handleWordSelect(word)}
                  aria-label="단어 선택: {word.text}"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex-1 min-w-0">
                      <!-- 단어 정보 -->
                      <div class="flex items-center gap-2 mb-1">
                        <span class="font-medium text-base">{word.text}</span>
                        
                        {#if word.reading && word.reading !== word.text}
                          <span class="text-sm text-base-content/60">({word.reading})</span>
                        {/if}
                        
                        <span class="badge badge-xs {getDifficultyColor(word.difficultyLevel)}">
                          {word.difficultyLevel}
                        </span>
                      </div>
                      
                      <!-- 의미 -->
                      <p class="text-sm text-base-content/80 line-clamp-1">
                        {word.meaning}
                      </p>
                      
                      <!-- 품사 -->
                      {#if word.partOfSpeech}
                        <span class="text-xs text-base-content/60 mt-1">
                          {word.partOfSpeech}
                        </span>
                      {/if}
                    </div>
                    
                    <!-- 추가 버튼 -->
                    <button
                      class="btn btn-primary btn-xs ml-2"
                      on:click={(e) => handleAddToVocabulary(word, e)}
                      aria-label="단어장에 추가"
                    >
                      추가
                    </button>
                  </div>
                </button>
              {/each}
            </div>
            
            <!-- 더 많은 결과 표시 -->
            {#if searchResults.length > maxResults}
              <div class="text-center py-2 text-sm text-base-content/60 border-t border-base-300">
                {searchResults.length - maxResults}개의 추가 결과가 있습니다
              </div>
            {/if}
          {:else if searchQuery.trim().length >= 2}
            <!-- 결과 없음 -->
            <div class="flex flex-col items-center justify-center py-8 text-center">
              <svg class="w-16 h-16 text-base-content/20 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
              </svg>
              <h3 class="font-medium text-base-content/60 mb-1">결과가 없습니다</h3>
              <p class="text-sm text-base-content/40">
                다른 검색어를 시도해보세요
              </p>
            </div>
          {:else if searchQuery.trim().length === 1}
            <!-- 최소 검색 길이 안내 -->
            <div class="flex items-center justify-center py-4 text-sm text-base-content/60">
              최소 2글자 이상 입력해주세요
            </div>
          {/if}
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .line-clamp-1 {
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style> 