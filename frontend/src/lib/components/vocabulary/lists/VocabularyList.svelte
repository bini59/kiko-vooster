<!--
  단어장 리스트 컨테이너
  
  사용자 단어장을 표시하고 필터링, 정렬, 페이지네이션 기능을 제공합니다.
-->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { fade, slide } from 'svelte/transition';
  import WordCard from '../core/WordCard.svelte';
  import type { UserWord, VocabularyFilter, VocabularySortBy, SortOrder } from '$lib/types/vocabulary';
  import { SearchType, VocabularySortBy as SortByEnum, SortOrder as SortOrderEnum, DifficultyLevel } from '$lib/types/vocabulary';
  
  export let words: UserWord[] = [];
  export let loading = false;
  export let error: string | null = null;
  export let filter: VocabularyFilter;
  export let totalWords = 0;
  export let currentPage = 1;
  export let totalPages = 1;
  export let pageSize = 20;
  export let allTags: string[] = [];
  export let compact = false;
  
  const dispatch = createEventDispatcher<{
    filterChange: VocabularyFilter;
    pageChange: number;
    wordClick: UserWord;
    wordEdit: UserWord;
    wordRemove: UserWord;
    wordUpdate: { word: UserWord; updates: any };
    clearFilters: void;
  }>();
  
  // 로컬 필터 상태
  let localFilter = { ...filter };
  let showFilters = false;
  let newTag = '';
  
  // 필터 변경 시 업데이트
  $: localFilter = { ...filter };
  
  // 필터 옵션들
  const sortOptions = [
    { value: SortByEnum.ADDED_DATE, label: '추가일' },
    { value: SortByEnum.LAST_REVIEWED, label: '복습일' },
    { value: SortByEnum.MASTERY_LEVEL, label: '숙련도' },
    { value: SortByEnum.ALPHABETICAL, label: '가나다순' },
    { value: SortByEnum.DIFFICULTY, label: '난이도' }
  ];
  
  const masteryLevels = [
    { value: 1, label: '초급 (1)', color: 'bg-red-500' },
    { value: 2, label: '기초 (2)', color: 'bg-orange-500' },
    { value: 3, label: '중급 (3)', color: 'bg-yellow-500' },
    { value: 4, label: '상급 (4)', color: 'bg-blue-500' },
    { value: 5, label: '마스터 (5)', color: 'bg-green-500' }
  ];
  
  const difficultyLevels = [
    { value: DifficultyLevel.BEGINNER, label: '초급', color: 'badge-success' },
    { value: DifficultyLevel.INTERMEDIATE, label: '중급', color: 'badge-warning' },
    { value: DifficultyLevel.ADVANCED, label: '고급', color: 'badge-error' }
  ];
  
  // 이벤트 핸들러들
  function applyFilters() {
    dispatch('filterChange', localFilter);
    showFilters = false;
  }
  
  function resetFilters() {
    localFilter = {
      searchQuery: '',
      searchType: SearchType.ALL,
      tags: [],
      masteryLevels: [],
      difficultyLevels: [],
      sortBy: SortByEnum.ADDED_DATE,
      sortOrder: SortOrderEnum.DESC
    };
    dispatch('clearFilters');
    showFilters = false;
  }
  
  function handleSearchInput(event: Event) {
    const target = event.target as HTMLInputElement;
    localFilter.searchQuery = target.value;
    
    // 실시간 검색 (디바운스 처리는 부모에서)
    if (target.value.length === 0 || target.value.length >= 2) {
      applyFilters();
    }
  }
  
  function toggleTag(tag: string) {
    if (localFilter.tags.includes(tag)) {
      localFilter.tags = localFilter.tags.filter(t => t !== tag);
    } else {
      localFilter.tags = [...localFilter.tags, tag];
    }
  }
  
  function toggleMasteryLevel(level: number) {
    if (localFilter.masteryLevels.includes(level)) {
      localFilter.masteryLevels = localFilter.masteryLevels.filter(l => l !== level);
    } else {
      localFilter.masteryLevels = [...localFilter.masteryLevels, level];
    }
  }
  
  function toggleDifficultyLevel(level: DifficultyLevel) {
    if (localFilter.difficultyLevels.includes(level)) {
      localFilter.difficultyLevels = localFilter.difficultyLevels.filter(l => l !== level);
    } else {
      localFilter.difficultyLevels = [...localFilter.difficultyLevels, level];
    }
  }
  
  function handlePageChange(page: number) {
    dispatch('pageChange', page);
  }
  
  function generatePageNumbers(): number[] {
    const pages: number[] = [];
    const maxVisible = 5;
    const half = Math.floor(maxVisible / 2);
    
    let start = Math.max(1, currentPage - half);
    let end = Math.min(totalPages, start + maxVisible - 1);
    
    if (end - start + 1 < maxVisible) {
      start = Math.max(1, end - maxVisible + 1);
    }
    
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    
    return pages;
  }
  
  $: hasActiveFilters = localFilter.searchQuery || 
                      localFilter.tags.length > 0 || 
                      localFilter.masteryLevels.length > 0 || 
                      localFilter.difficultyLevels.length > 0;
  
  $: pageNumbers = generatePageNumbers();
</script>

<div class="vocabulary-list">
  <!-- 헤더 & 필터 -->
  <div class="mb-6">
    <!-- 통계 및 필터 토글 -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-4">
        <h2 class="text-xl font-bold text-base-content">
          내 단어장
        </h2>
        
        <div class="stats bg-base-200 text-sm">
          <div class="stat py-2 px-4">
            <div class="stat-value text-sm">{totalWords}</div>
            <div class="stat-desc">개의 단어</div>
          </div>
        </div>
      </div>
      
      <div class="flex items-center gap-2">
        <!-- 정렬 선택 -->
        <select
          class="select select-bordered select-sm"
          bind:value={localFilter.sortBy}
          on:change={applyFilters}
          aria-label="정렬 방식"
        >
          {#each sortOptions as option}
            <option value={option.value}>{option.label}</option>
          {/each}
        </select>
        
        <!-- 정렬 순서 -->
        <button
          class="btn btn-ghost btn-sm btn-square"
          on:click={() => {
            localFilter.sortOrder = localFilter.sortOrder === SortOrderEnum.ASC ? SortOrderEnum.DESC : SortOrderEnum.ASC;
            applyFilters();
          }}
          aria-label="정렬 순서 변경"
        >
          {#if localFilter.sortOrder === SortOrderEnum.ASC}
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12"/>
            </svg>
          {:else}
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4"/>
            </svg>
          {/if}
        </button>
        
        <!-- 필터 토글 -->
        <button
          class="btn btn-ghost btn-sm gap-2"
          class:btn-active={showFilters}
          on:click={() => showFilters = !showFilters}
          aria-label="필터 옵션"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.207A1 1 0 013 6.5V4z"/>
          </svg>
          필터
          {#if hasActiveFilters}
            <span class="badge badge-primary badge-xs"></span>
          {/if}
        </button>
      </div>
    </div>
    
    <!-- 검색 바 -->
    <div class="mb-4">
      <div class="flex gap-2">
        <input
          type="text"
          class="input input-bordered flex-1"
          placeholder="단어, 의미, 노트에서 검색..."
          value={localFilter.searchQuery}
          on:input={handleSearchInput}
          aria-label="단어 검색"
        />
        
        <select
          class="select select-bordered w-32"
          bind:value={localFilter.searchType}
          on:change={applyFilters}
          aria-label="검색 타입"
        >
          <option value={SearchType.ALL}>전체</option>
          <option value={SearchType.KANJI}>한자</option>
          <option value={SearchType.HIRAGANA}>히라가나</option>
          <option value={SearchType.MEANING}>의미</option>
        </select>
      </div>
    </div>
    
    <!-- 확장 필터 -->
    {#if showFilters}
      <div class="card bg-base-100 border border-base-200 p-4" transition:slide>
        <!-- 태그 필터 -->
        {#if allTags.length > 0}
          <div class="mb-4">
            <h4 class="text-sm font-medium text-base-content mb-2">태그</h4>
            <div class="flex flex-wrap gap-2">
              {#each allTags as tag}
                <button
                  class="badge gap-1 cursor-pointer"
                  class:badge-primary={localFilter.tags.includes(tag)}
                  class:badge-ghost={!localFilter.tags.includes(tag)}
                  on:click={() => toggleTag(tag)}
                >
                  {tag}
                  {#if localFilter.tags.includes(tag)}
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                    </svg>
                  {/if}
                </button>
              {/each}
            </div>
          </div>
        {/if}
        
        <!-- 숙련도 필터 -->
        <div class="mb-4">
          <h4 class="text-sm font-medium text-base-content mb-2">숙련도</h4>
          <div class="flex flex-wrap gap-2">
            {#each masteryLevels as level}
              <button
                class="btn btn-sm gap-2"
                class:btn-primary={localFilter.masteryLevels.includes(level.value)}
                class:btn-ghost={!localFilter.masteryLevels.includes(level.value)}
                on:click={() => toggleMasteryLevel(level.value)}
              >
                <div class="w-3 h-3 rounded-full {level.color}"></div>
                {level.label}
              </button>
            {/each}
          </div>
        </div>
        
        <!-- 난이도 필터 -->
        <div class="mb-4">
          <h4 class="text-sm font-medium text-base-content mb-2">난이도</h4>
          <div class="flex flex-wrap gap-2">
            {#each difficultyLevels as level}
              <button
                class="badge cursor-pointer"
                class:badge-primary={localFilter.difficultyLevels.includes(level.value)}
                class:badge-ghost={!localFilter.difficultyLevels.includes(level.value)}
                on:click={() => toggleDifficultyLevel(level.value)}
              >
                {level.label}
              </button>
            {/each}
          </div>
        </div>
        
        <!-- 필터 액션 -->
        <div class="flex justify-end gap-2">
          <button
            class="btn btn-ghost btn-sm"
            on:click={resetFilters}
          >
            초기화
          </button>
          <button
            class="btn btn-primary btn-sm"
            on:click={applyFilters}
          >
            적용
          </button>
        </div>
      </div>
    {/if}
    
    <!-- 활성 필터 표시 -->
    {#if hasActiveFilters}
      <div class="flex flex-wrap gap-2 mt-2" transition:fade>
        {#if localFilter.searchQuery}
          <span class="badge badge-outline gap-1">
            검색: "{localFilter.searchQuery}"
            <button
              class="btn btn-ghost btn-xs btn-square p-0"
              on:click={() => {
                localFilter.searchQuery = '';
                applyFilters();
              }}
            >
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </span>
        {/if}
        
        {#each localFilter.tags as tag}
          <span class="badge badge-primary gap-1">
            {tag}
            <button
              class="btn btn-ghost btn-xs btn-square p-0"
              on:click={() => toggleTag(tag)}
            >
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </span>
        {/each}
      </div>
    {/if}
  </div>
  
  <!-- 단어 리스트 -->
  <div class="vocabulary-content">
    {#if loading}
      <!-- 로딩 상태 -->
      <div class="flex justify-center items-center py-12">
        <span class="loading loading-spinner loading-lg"></span>
      </div>
    {:else if error}
      <!-- 에러 상태 -->
      <div class="alert alert-error" transition:fade>
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
        </svg>
        <span>{error}</span>
      </div>
    {:else if words.length === 0}
      <!-- 빈 상태 -->
      <div class="flex flex-col items-center justify-center py-12 text-center">
        <svg class="w-24 h-24 text-base-content/20 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
        </svg>
        
        {#if hasActiveFilters}
          <h3 class="text-xl font-semibold text-base-content mb-2">
            검색 결과가 없습니다
          </h3>
          <p class="text-base-content/70 mb-4">
            다른 검색어나 필터를 시도해보세요.
          </p>
          <button
            class="btn btn-primary"
            on:click={resetFilters}
          >
            모든 필터 지우기
          </button>
        {:else}
          <h3 class="text-xl font-semibold text-base-content mb-2">
            아직 저장된 단어가 없습니다
          </h3>
          <p class="text-base-content/70 mb-4">
            새로운 단어를 검색하여 단어장에 추가해보세요.
          </p>
        {/if}
      </div>
    {:else}
      <!-- 단어 카드들 -->
      <div 
        class="grid gap-4"
        class:grid-cols-1={compact || words.length < 2}
        class:md:grid-cols-2={!compact && words.length >= 2}
        class:lg:grid-cols-3={!compact && words.length >= 3}
      >
        {#each words as userWord (userWord.id)}
          <div transition:fade={{ duration: 200 }}>
            <WordCard
              {userWord}
              {compact}
              on:click={(e) => dispatch('wordClick', e.detail)}
              on:edit={(e) => dispatch('wordEdit', e.detail)}
              on:remove={(e) => dispatch('wordRemove', e.detail)}
              on:updateMastery={(e) => dispatch('wordUpdate', {
                word: e.detail.word,
                updates: { masteryLevel: e.detail.level }
              })}
              on:addTag={(e) => dispatch('wordUpdate', {
                word: e.detail.word,
                updates: { tags: [...e.detail.word.tags, e.detail.tag] }
              })}
              on:removeTag={(e) => dispatch('wordUpdate', {
                word: e.detail.word,
                updates: { tags: e.detail.word.tags.filter(t => t !== e.detail.tag) }
              })}
            />
          </div>
        {/each}
      </div>
      
      <!-- 페이지네이션 -->
      {#if totalPages > 1}
        <div class="flex justify-center mt-8">
          <div class="join">
            <!-- 이전 페이지 -->
            <button
              class="join-item btn"
              class:btn-disabled={currentPage <= 1}
              on:click={() => handlePageChange(currentPage - 1)}
              disabled={currentPage <= 1}
              aria-label="이전 페이지"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
              </svg>
            </button>
            
            <!-- 페이지 번호들 -->
            {#each pageNumbers as page}
              <button
                class="join-item btn"
                class:btn-active={page === currentPage}
                on:click={() => handlePageChange(page)}
                aria-label="페이지 {page}"
              >
                {page}
              </button>
            {/each}
            
            <!-- 다음 페이지 -->
            <button
              class="join-item btn"
              class:btn-disabled={currentPage >= totalPages}
              on:click={() => handlePageChange(currentPage + 1)}
              disabled={currentPage >= totalPages}
              aria-label="다음 페이지"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
              </svg>
            </button>
          </div>
        </div>
        
        <!-- 페이지 정보 -->
        <div class="text-center text-sm text-base-content/60 mt-4">
          {((currentPage - 1) * pageSize) + 1}-{Math.min(currentPage * pageSize, totalWords)} / {totalWords}개
        </div>
      {/if}
    {/if}
  </div>
</div>

<style>
  .vocabulary-list {
    @apply w-full;
  }
  
  .vocabulary-content {
    @apply min-h-[400px];
  }
</style> 