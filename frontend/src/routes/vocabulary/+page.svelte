<!--
  단어장 메인 페이지
  
  사용자의 단어장을 관리하고 새로운 단어를 검색/추가할 수 있는 통합 페이지입니다.
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { 
    vocabularyState, 
    vocabularyActions, 
    userWords, 
    searchResults, 
    isLoading, 
    error, 
    currentFilter, 
    currentPage, 
    totalPages, 
    totalWords,
    allTags 
  } from '$lib/stores/vocabularyStore';
  import { isLoggedIn } from '$lib/stores/authStore';
  import VocabularyList from '$lib/components/vocabulary/lists/VocabularyList.svelte';
  import WordSearchBar from '$lib/components/vocabulary/core/WordSearchBar.svelte';
  import WordDetailModal from '$lib/components/vocabulary/core/WordDetailModal.svelte';
  import type { UserWord, Word, UpdateWordRequest } from '$lib/types/vocabulary';
  
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
    await vocabularyActions.loadTags();
  });
  
  // 이벤트 핸들러들
  function handleFilterChange(event: CustomEvent<any>) {
    vocabularyActions.updateFilter(event.detail);
  }
  
  function handlePageChange(event: CustomEvent<number>) {
    vocabularyActions.loadUserWords(event.detail);
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
    vocabularyActions.clearFilters();
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
    vocabularyActions.clearSearchResults();
    searchError = null;
  }
  
  async function handleAddToVocabulary(event: CustomEvent<Word>) {
    try {
      await vocabularyActions.addWord({
        wordId: event.detail.id,
        masteryLevel: 1,
        tags: [],
        notes: ''
      });
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