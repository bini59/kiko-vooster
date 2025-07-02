<!--
  단어 상세 정보 모달
  
  선택된 단어의 상세 정보를 표시하고 편집 기능을 제공합니다.
  사전 정보, 예문, 관련 단어 등을 포함합니다.
-->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { UserWord, UpdateWordRequest } from '$lib/types/vocabulary';
  
  export let userWord: UserWord | null = null;
  export let isOpen = false;
  
  const dispatch = createEventDispatcher<{
    close: void;
    update: { wordId: string; updates: UpdateWordRequest };
    remove: string;
    startReview: UserWord;
  }>();
  
  // 편집 모드 상태
  let isEditing = false;
  let editForm = {
    masteryLevel: 0,
    tags: [] as string[],
    notes: ''
  };
  
  // 태그 입력
  let newTag = '';
  
  $: if (userWord && isOpen) {
    resetEditForm();
  }
  
  $: word = userWord?.word;
  $: difficultyColor = getDifficultyColor(word?.difficultyLevel || 'beginner');
  $: masteryPercentage = editForm.masteryLevel * 20; // 0-5 레벨을 0-100%로
  
  function resetEditForm() {
    if (!userWord) return;
    
    editForm = {
      masteryLevel: userWord.masteryLevel,
      tags: [...userWord.tags],
      notes: userWord.notes || ''
    };
  }
  
  function getDifficultyColor(difficulty: string): string {
    switch (difficulty) {
      case 'beginner': return 'badge-success';
      case 'intermediate': return 'badge-warning';
      case 'advanced': return 'badge-error';
      default: return 'badge-ghost';
    }
  }
  
  function handleClose() {
    isEditing = false;
    dispatch('close');
  }
  
  function handleStartEdit() {
    isEditing = true;
    resetEditForm();
  }
  
  function handleCancelEdit() {
    isEditing = false;
    resetEditForm();
  }
  
  function handleSave() {
    if (!userWord) return;
    
    const updates: UpdateWordRequest = {};
    
    if (editForm.masteryLevel !== userWord.masteryLevel) {
      updates.masteryLevel = editForm.masteryLevel;
    }
    
    if (JSON.stringify(editForm.tags) !== JSON.stringify(userWord.tags)) {
      updates.tags = editForm.tags;
    }
    
    if (editForm.notes !== (userWord.notes || '')) {
      updates.notes = editForm.notes;
    }
    
    if (Object.keys(updates).length > 0) {
      dispatch('update', { wordId: userWord.id, updates });
    }
    
    isEditing = false;
  }
  
  function handleRemove() {
    if (!userWord) return;
    
    if (confirm(`"${word?.text}"을(를) 단어장에서 제거하시겠습니까?`)) {
      dispatch('remove', userWord.id);
      handleClose();
    }
  }
  
  function handleStartReview() {
    if (!userWord) return;
    dispatch('startReview', userWord);
    handleClose();
  }
  
  function addTag() {
    if (newTag.trim() && !editForm.tags.includes(newTag.trim())) {
      editForm.tags = [...editForm.tags, newTag.trim()];
      newTag = '';
    }
  }
  
  function removeTag(tag: string) {
    editForm.tags = editForm.tags.filter(t => t !== tag);
  }
  
  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'short'
    });
  }
  
  function formatDateTime(dateString: string): string {
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
</script>

<!-- 모달 -->
{#if isOpen}
  <div class="modal modal-open" role="dialog" aria-modal="true" aria-labelledby="modal-title">
    <div class="modal-box max-w-4xl max-h-[90vh] p-0">
      {#if userWord && word}
        <!-- 모달 헤더 -->
        <div class="flex items-center justify-between p-6 border-b border-base-200">
          <div class="flex items-center gap-3">
            <h2 id="modal-title" class="text-2xl font-bold text-base-content">
              {word.text}
            </h2>
            <span class="badge {difficultyColor}">
              {word.difficultyLevel}
            </span>
          </div>
          
          <div class="flex items-center gap-2">
            {#if !isEditing}
              <button
                class="btn btn-primary btn-sm"
                on:click={handleStartReview}
                aria-label="이 단어로 복습 시작"
              >
                복습하기
              </button>
              
              <button
                class="btn btn-ghost btn-sm"
                on:click={handleStartEdit}
                aria-label="단어 편집"
              >
                편집
              </button>
            {:else}
              <button
                class="btn btn-success btn-sm"
                on:click={handleSave}
                aria-label="변경사항 저장"
              >
                저장
              </button>
              
              <button
                class="btn btn-ghost btn-sm"
                on:click={handleCancelEdit}
                aria-label="편집 취소"
              >
                취소
              </button>
            {/if}
            
            <button
              class="btn btn-ghost btn-sm btn-square"
              on:click={handleClose}
              aria-label="모달 닫기"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>
        
        <!-- 모달 내용 -->
        <div class="p-6 overflow-y-auto max-h-[calc(90vh-100px)]">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <!-- 왼쪽: 단어 정보 -->
            <div class="space-y-6">
              <!-- 기본 정보 -->
              <div class="card bg-base-100 border border-base-200">
                <div class="card-body">
                  <h3 class="card-title text-lg">기본 정보</h3>
                  
                  <div class="space-y-4">
                    <!-- 읽기 -->
                    {#if word.reading && word.reading !== word.text}
                      <div>
                        <label class="text-sm font-medium text-base-content/70">읽기</label>
                        <p class="text-lg">{word.reading}</p>
                      </div>
                    {/if}
                    
                    <!-- 의미 -->
                    <div>
                      <label class="text-sm font-medium text-base-content/70">의미</label>
                      <p class="text-base">{word.meaning}</p>
                    </div>
                    
                    <!-- 품사 -->
                    {#if word.partOfSpeech}
                      <div>
                        <label class="text-sm font-medium text-base-content/70">품사</label>
                        <p class="text-base">{word.partOfSpeech}</p>
                      </div>
                    {/if}
                    
                    <!-- 예문 (추후 구현) -->
                    {#if (word as any).examples && (word as any).examples.length > 0}
                      <div>
                        <label class="text-sm font-medium text-base-content/70">예문</label>
                        <div class="space-y-2">
                          {#each (word as any).examples as example}
                            <div class="p-3 bg-base-200/50 rounded-lg">
                              <p class="text-base mb-1">{example.sentence}</p>
                              <p class="text-sm text-base-content/70">{example.translation}</p>
                            </div>
                          {/each}
                        </div>
                      </div>
                    {/if}
                  </div>
                </div>
              </div>
              
              <!-- 학습 통계 -->
              <div class="card bg-base-100 border border-base-200">
                <div class="card-body">
                  <h3 class="card-title text-lg">학습 통계</h3>
                  
                  <div class="grid grid-cols-2 gap-4">
                    <div class="stat">
                      <div class="stat-title">복습 횟수</div>
                      <div class="stat-value text-primary">{userWord.reviewCount}</div>
                    </div>
                    
                                         <div class="stat">
                       <div class="stat-title">정답률</div>
                       <div class="stat-value text-success">
                         {userWord.reviewCount > 0 ? Math.round(((userWord as any).correctCount || 0) / userWord.reviewCount * 100) : 0}%
                       </div>
                     </div>
                  </div>
                  
                  <div class="space-y-2">
                    <div>
                      <span class="text-sm font-medium text-base-content/70">추가일</span>
                      <p class="text-base">{formatDate(userWord.addedAt)}</p>
                    </div>
                    
                    {#if userWord.lastReviewed}
                      <div>
                        <span class="text-sm font-medium text-base-content/70">마지막 복습</span>
                        <p class="text-base">{formatDateTime(userWord.lastReviewed)}</p>
                      </div>
                    {/if}
                    
                    {#if userWord.nextReview}
                      <div>
                        <span class="text-sm font-medium text-base-content/70">다음 복습</span>
                        <p class="text-base">{formatDate(userWord.nextReview)}</p>
                      </div>
                    {/if}
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 오른쪽: 편집 가능한 정보 -->
            <div class="space-y-6">
              <!-- 숙련도 -->
              <div class="card bg-base-100 border border-base-200">
                <div class="card-body">
                  <h3 class="card-title text-lg">숙련도</h3>
                  
                  {#if isEditing}
                    <div class="space-y-4">
                      <div>
                        <div class="flex items-center justify-between mb-2">
                          <span class="text-sm font-medium">레벨: {editForm.masteryLevel}/5</span>
                          <span class="text-xs text-base-content/60">{masteryPercentage}%</span>
                        </div>
                        
                        <input
                          type="range"
                          min="0"
                          max="5"
                          step="1"
                          bind:value={editForm.masteryLevel}
                          class="range range-primary"
                          aria-label="숙련도 레벨"
                        />
                        
                        <div class="flex justify-between text-xs px-2 mt-1">
                          <span>0</span>
                          <span>1</span>
                          <span>2</span>
                          <span>3</span>
                          <span>4</span>
                          <span>5</span>
                        </div>
                      </div>
                    </div>
                  {:else}
                    <div class="space-y-4">
                      <div>
                        <div class="flex items-center justify-between mb-2">
                          <span class="text-sm font-medium">레벨: {userWord.masteryLevel}/5</span>
                          <span class="text-xs text-base-content/60">{userWord.masteryLevel * 20}%</span>
                        </div>
                        
                        <progress 
                          class="progress progress-primary w-full" 
                          value={userWord.masteryLevel * 20} 
                          max="100"
                        ></progress>
                      </div>
                    </div>
                  {/if}
                </div>
              </div>
              
              <!-- 태그 -->
              <div class="card bg-base-100 border border-base-200">
                <div class="card-body">
                  <h3 class="card-title text-lg">태그</h3>
                  
                  {#if isEditing}
                    <div class="space-y-4">
                      <!-- 태그 목록 -->
                      <div class="flex flex-wrap gap-2">
                        {#each editForm.tags as tag}
                          <span class="badge badge-primary gap-2">
                            {tag}
                            <button
                              class="btn btn-ghost btn-xs btn-square p-0"
                              on:click={() => removeTag(tag)}
                              aria-label="태그 제거"
                            >
                              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                              </svg>
                            </button>
                          </span>
                        {/each}
                      </div>
                      
                      <!-- 새 태그 추가 -->
                      <div class="flex gap-2">
                        <input
                          bind:value={newTag}
                          class="input input-bordered flex-1"
                          placeholder="새 태그 입력"
                          on:keydown={(e) => e.key === 'Enter' && addTag()}
                        />
                        <button
                          class="btn btn-primary"
                          on:click={addTag}
                          disabled={!newTag.trim()}
                          aria-label="태그 추가"
                        >
                          추가
                        </button>
                      </div>
                    </div>
                  {:else}
                    <div class="flex flex-wrap gap-2">
                      {#each userWord.tags as tag}
                        <span class="badge badge-primary">{tag}</span>
                      {:else}
                        <span class="text-base-content/60">태그가 없습니다</span>
                      {/each}
                    </div>
                  {/if}
                </div>
              </div>
              
              <!-- 노트 -->
              <div class="card bg-base-100 border border-base-200">
                <div class="card-body">
                  <h3 class="card-title text-lg">개인 노트</h3>
                  
                  {#if isEditing}
                    <textarea
                      bind:value={editForm.notes}
                      class="textarea textarea-bordered h-32"
                      placeholder="이 단어에 대한 개인적인 메모를 작성하세요..."
                      aria-label="개인 노트"
                    ></textarea>
                  {:else}
                    <div class="min-h-[8rem]">
                      {#if userWord.notes}
                        <p class="text-base whitespace-pre-wrap">{userWord.notes}</p>
                      {:else}
                        <p class="text-base-content/60">노트가 없습니다</p>
                      {/if}
                    </div>
                  {/if}
                </div>
              </div>
              
              <!-- 위험 구역 -->
              {#if !isEditing}
                <div class="card bg-error/5 border border-error/20">
                  <div class="card-body">
                    <h3 class="card-title text-lg text-error">위험 구역</h3>
                    <p class="text-sm text-base-content/70 mb-4">
                      이 작업은 되돌릴 수 없습니다.
                    </p>
                    
                    <button
                      class="btn btn-error btn-sm"
                      on:click={handleRemove}
                      aria-label="단어 삭제"
                    >
                      단어장에서 제거
                    </button>
                  </div>
                </div>
              {/if}
            </div>
          </div>
        </div>
      {/if}
    </div>
    
    <!-- 모달 배경 (클릭시 닫기) -->
    <div class="modal-backdrop" on:click={handleClose}></div>
  </div>
{/if} 