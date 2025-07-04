<!--
  단어장 메인 페이지
  
  사용자의 단어장을 관리하고 새로운 단어를 검색/추가할 수 있는 통합 페이지입니다.
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { goto } from '$app/navigation';
  import { 
    vocabularyState, 
    vocabularyActions, 
    filteredWords, 
    paginatedWords
  } from '$lib/stores/vocabularyStore';
  import { isLoggedIn } from '$lib/stores/authStore';
  import VocabularyList from '$lib/components/vocabulary/lists/VocabularyList.svelte';
  import WordSearchBar from '$lib/components/vocabulary/core/WordSearchBar.svelte';
  import WordDetailModal from '$lib/components/vocabulary/core/WordDetailModal.svelte';
  import type { UserWord, Word, UpdateWordRequest } from '$lib/types/vocabulary';
  
  // 복습 관련 타입 import 추가
  import { ReviewSessionMode } from '$lib/types/vocabulary';
  
  // Store에서 필요한 데이터 구독
  $: userWords = $vocabularyState.userWords;
  $: searchResults = $vocabularyState.searchResults;
  $: isLoading = $vocabularyState.loading;
  $: error = $vocabularyState.error;
  $: currentFilter = $vocabularyState.currentFilter;
  $: currentPage = $vocabularyState.currentPage;
  $: totalPages = $vocabularyState.totalPages;
  $: totalWords = userWords.length;
  $: allTags = $vocabularyState.allTags;
  
  // 모달 상태
  let selectedWord: UserWord | null = null;
  let isDetailModalOpen = false;
  
  // 검색 상태
  let searchLoading = false;
  let searchError: string | null = null;
  
  // 탭 상태
  let activeTab: 'my-words' | 'search' = 'my-words';
  
  onMount(async () => {
    // 로그인 상태 확인
    if (!get(isLoggedIn)) {
      // 로그인 페이지로 리다이렉트 또는 로그인 모달 표시
      return;
    }
    
    // 초기 데이터 로드
    await vocabularyActions.loadUserWords();
  });
  
  // 이벤트 핸들러들
  function handleFilterChange(event: CustomEvent<any>) {
    vocabularyActions.setFilter(event.detail);
  }
  
  function handlePageChange(event: CustomEvent<number>) {
    vocabularyActions.setPage(event.detail);
  }
  
  function handleWordClick(event: CustomEvent<UserWord>) {
    selectedWord = event.detail;
    isDetailModalOpen = true;
  }
  
  function handleWordEdit(event: CustomEvent<UserWord>) {
    selectedWord = event.detail;
    isDetailModalOpen = true;
  }
  
  async function handleWordRemove(event: CustomEvent<UserWord>) {
    try {
      await vocabularyActions.removeWord(event.detail.id);
    } catch (err) {
      console.error('단어 삭제 실패:', err);
    }
  }
  
  async function handleWordUpdate(event: CustomEvent<{ word: UserWord; updates: any }>) {
    try {
      await vocabularyActions.updateWord(event.detail.word.id, event.detail.updates);
    } catch (err) {
      console.error('단어 업데이트 실패:', err);
    }
  }
  
  function handleClearFilters() {
    vocabularyActions.setFilter({ 
      tags: [], 
      masteryLevels: [], 
      difficultyLevels: [], 
      searchQuery: '',
      searchType: currentFilter.searchType,
      sortBy: currentFilter.sortBy,
      sortOrder: currentFilter.sortOrder
    });
  }
  
  // 검색 관련 이벤트 핸들러들
  async function handleSearch(event: CustomEvent<{ query: string; searchType: any }>) {
    try {
      searchLoading = true;
      searchError = null;
      await vocabularyActions.searchWords(event.detail.query, event.detail.searchType);
    } catch (err: any) {
      searchError = err.message || '검색 중 오류가 발생했습니다';
    } finally {
      searchLoading = false;
    }
  }
  
  function handleSearchClear() {
    vocabularyActions.setFilter({ searchQuery: '' });
    searchError = null;
  }
  
  async function handleAddToVocabulary(event: CustomEvent<Word>) {
    try {
      await vocabularyActions.addWord(event.detail.text, [], '');
    } catch (err) {
      console.error('단어 추가 실패:', err);
    }
  }
  
  // 모달 이벤트 핸들러들
  function handleModalClose() {
    isDetailModalOpen = false;
    selectedWord = null;
  }
  
  async function handleModalUpdate(event: CustomEvent<{ wordId: string; updates: UpdateWordRequest }>) {
    try {
      await vocabularyActions.updateWord(event.detail.wordId, event.detail.updates);
      // 모달의 데이터 업데이트
      if (selectedWord) {
        selectedWord = { ...selectedWord, ...event.detail.updates };
      }
    } catch (err) {
      console.error('단어 업데이트 실패:', err);
    }
  }
  
  async function handleModalRemove(event: CustomEvent<string>) {
    try {
      await vocabularyActions.removeWord(event.detail);
      handleModalClose();
    } catch (err) {
      console.error('단어 삭제 실패:', err);
    }
  }
  
  function handleStartReview(event: CustomEvent<UserWord>) {
    // 복습 페이지로 이동 (추후 구현)
    console.log('복습 시작:', event.detail);
  }
  
  // 복습 관련 핸들러 함수들 추가
  function handleStartQuickReview() {
    // 기본 플래시카드 모드로 빠른 복습 시작
    const reviewWords = $vocabularyState.userWords.filter((w: UserWord) => w.masteryLevel < 3);
    const wordIds = reviewWords.slice(0, 10).map((w: UserWord) => w.id);
    
    goto(`/vocabulary/review?words=${wordIds.join(',')}&mode=FLASHCARD&shuffleWords=true`);
  }
  
  function handleStartReviewMode(mode: string) {
    // 선택된 모드로 복습 시작
    const reviewWords = $vocabularyState.userWords.filter((w: UserWord) => w.masteryLevel < 3);
    const wordIds = reviewWords.slice(0, 15).map((w: UserWord) => w.id);
    
    goto(`/vocabulary/review?words=${wordIds.join(',')}&mode=${mode}&shuffleWords=true`);
  }
  
  function handleShowReviewSettings() {
    // 복습 설정 모달 표시 (추후 구현)
    console.log('복습 설정 표시');
  }
</script>

<svelte:head>
  <title>단어장 - Kiko Vooster</title>
  <meta name="description" content="일본어 학습을 위한 개인 단어장을 관리하세요." />
</svelte:head>

{#if !$isLoggedIn}
  <!-- 로그인 필요 안내 -->
  <div class="container mx-auto px-4 py-8">
    <div class="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <svg class="w-24 h-24 text-base-content/20 mb-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" 
              d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
      </svg>
      
      <h1 class="text-3xl font-bold text-base-content mb-4">단어장</h1>
      <p class="text-xl text-base-content/70 mb-8">
        개인 단어장을 사용하려면 로그인이 필요합니다.
      </p>
      
      <button 
        class="btn btn-primary btn-lg"
        on:click={() => {/* 로그인 모달 표시 */}}
      >
        로그인하기
      </button>
    </div>
  </div>
{:else}
  <!-- 메인 컨텐츠 -->
  <div class="container mx-auto px-4 py-6">
    <!-- 페이지 헤더 -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
      <div>
        <h1 class="text-3xl font-bold text-base-content mb-2">단어장</h1>
        <div class="flex items-center gap-4 text-sm text-base-content/70">
          <span>총 {$totalWords}개 단어</span>
          {#if $userWords.filter(w => w.masteryLevel < 3).length > 0}
            <span class="badge badge-warning badge-sm">
              복습 대상: {$userWords.filter(w => w.masteryLevel < 3).length}개
            </span>
          {/if}
        </div>
      </div>
      
      <!-- 복습 버튼 -->
      <div class="flex gap-2">
        <button 
          class="btn btn-primary btn-sm"
          disabled={$userWords.length === 0}
          on:click={handleStartQuickReview}
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
          </svg>
          빠른 복습
        </button>
        
        <div class="dropdown dropdown-end">
          <button 
            tabindex="0" 
            class="btn btn-ghost btn-sm"
            disabled={$userWords.length === 0}
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"/>
            </svg>
          </button>
          
          <ul tabindex="0" class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52 z-10">
            <li>
              <button on:click={() => handleStartReviewMode('flashcard')}>
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                        d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2M7 4h10M7 4l-2 16h14L17 4M9 9v6m4-6v6"/>
                </svg>
                플래시카드 복습
              </button>
            </li>
            <li>
              <button on:click={() => handleStartReviewMode('fillInBlanks')}>
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                        d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5M18 2l3 3m-6 0l6 6M9 7h6m-6 4h6m-2 4h4"/>
                </svg>
                빈칸채우기 복습
              </button>
            </li>
            <li>
              <button on:click={() => handleStartReviewMode('spelling')}>
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                        d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                </svg>
                철자게임 복습
              </button>
            </li>
            <li><hr /></li>
            <li>
              <button on:click={handleShowReviewSettings}>
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                        d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                </svg>
                복습 설정
              </button>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- 탭 네비게이션 -->
    <div class="tabs tabs-boxed mb-6">
      <button
        class="tab"
        class:tab-active={activeTab === 'my-words'}
        on:click={() => activeTab = 'my-words'}
      >
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
        </svg>
        내 단어장
      </button>
      
      <button
        class="tab"
        class:tab-active={activeTab === 'search'}
        on:click={() => activeTab = 'search'}
      >
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        </svg>
        단어 검색
      </button>
    </div>
    
    <!-- 탭 컨텐츠 -->
    {#if activeTab === 'my-words'}
      <!-- 내 단어장 탭 -->
      <VocabularyList
        words={$userWords}
        loading={$isLoading}
        error={$error}
        filter={$currentFilter}
        currentPage={$currentPage}
        totalPages={$totalPages}
        totalWords={$totalWords}
        allTags={$allTags}
        on:filterChange={handleFilterChange}
        on:pageChange={handlePageChange}
        on:wordClick={handleWordClick}
        on:wordEdit={handleWordEdit}
        on:wordRemove={handleWordRemove}
        on:wordUpdate={handleWordUpdate}
        on:clearFilters={handleClearFilters}
      />
    {:else if activeTab === 'search'}
      <!-- 단어 검색 탭 -->
      <div class="space-y-6">
        <div class="card bg-base-100 shadow-sm border border-base-200">
          <div class="card-body">
            <h2 class="card-title text-xl mb-4">단어 검색</h2>
            <p class="text-base-content/70 mb-6">
              JMdict 사전에서 단어를 검색하고 내 단어장에 추가하세요.
            </p>
            
            <WordSearchBar
              searchResults={$searchResults}
              loading={searchLoading}
              error={searchError}
              placeholder="찾고 싶은 단어를 입력하세요..."
              maxResults={20}
              on:search={handleSearch}
              on:clear={handleSearchClear}
              on:addToVocabulary={handleAddToVocabulary}
            />
          </div>
        </div>
        
        <!-- 검색 결과 (인라인이 아닌 경우) -->
        {#if $searchResults.length > 0}
          <div class="card bg-base-100 shadow-sm border border-base-200">
            <div class="card-body">
              <h3 class="card-title text-lg mb-4">검색 결과</h3>
              
              <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {#each $searchResults as word (word.id)}
                  <div class="card bg-base-100 border border-base-300 hover:shadow-md transition-shadow">
                    <div class="card-body p-4">
                      <div class="flex items-center justify-between mb-2">
                        <h4 class="font-medium text-lg">{word.text}</h4>
                        <span class="badge badge-sm badge-outline">
                          {word.difficultyLevel}
                        </span>
                      </div>
                      
                      {#if word.reading && word.reading !== word.text}
                        <p class="text-sm text-base-content/60 mb-2">
                          {word.reading}
                        </p>
                      {/if}
                      
                      <p class="text-base-content/80 mb-3 line-clamp-2">
                        {word.meaning}
                      </p>
                      
                      {#if word.partOfSpeech}
                        <p class="text-xs text-base-content/60 mb-3">
                          {word.partOfSpeech}
                        </p>
                      {/if}
                      
                      <button
                        class="btn btn-primary btn-sm w-full"
                        on:click={() => handleAddToVocabulary(new CustomEvent('addToVocabulary', { detail: word }))}
                      >
                        단어장에 추가
                      </button>
                    </div>
                  </div>
                {/each}
              </div>
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>
{/if}

<!-- 단어 상세 모달 -->
<WordDetailModal
  userWord={selectedWord}
  isOpen={isDetailModalOpen}
  on:close={handleModalClose}
  on:update={handleModalUpdate}
  on:remove={handleModalRemove}
  on:startReview={handleStartReview}
/>

<style>
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style> 