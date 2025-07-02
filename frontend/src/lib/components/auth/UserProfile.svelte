<script lang="ts">
  import { 
    currentUser, 
    userProfile, 
    userStats, 
    learningProgress, 
    authActions,
    isLoading 
  } from '$lib/stores/authStore';
  import type { JapaneseLevel } from '$lib/types/auth';
  import { createEventDispatcher } from 'svelte';

  // Props
  export let editable = false;

  const dispatch = createEventDispatcher<{
    edit: void;
    save: void;
  }>();

  // 편집 상태
  let isEditing = false;
  let editForm = {
    name: '',
    japanese_level: 'beginner' as JapaneseLevel,
    bio: '',
    learning_goals: [] as string[],
    daily_goal_minutes: 30
  };

  // 새 목표 입력
  let newGoal = '';

  // 일본어 레벨 옵션
  const japaneseLevels: { value: JapaneseLevel; label: string }[] = [
    { value: 'beginner', label: '초급 (N5-N4)' },
    { value: 'elementary', label: '초중급 (N4-N3)' },
    { value: 'intermediate', label: '중급 (N3-N2)' },
    { value: 'advanced', label: '고급 (N2-N1)' },
    { value: 'proficient', label: '능숙 (N1+)' }
  ];

  // 편집 시작
  function startEdit() {
    isEditing = true;
    editForm = {
      name: $userProfile.name || '',
      japanese_level: $userProfile.japanese_level || 'beginner',
      bio: $userProfile.bio || '',
      learning_goals: [...($userProfile.learning_goals || [])],
      daily_goal_minutes: $userProfile.daily_goal_minutes || 30
    };
    dispatch('edit');
  }

  // 편집 취소
  function cancelEdit() {
    isEditing = false;
    newGoal = '';
  }

  // 프로필 저장
  async function saveProfile() {
    try {
      await authActions.updateProfile(editForm);
      isEditing = false;
      newGoal = '';
      dispatch('save');
    } catch (error) {
      console.error('프로필 저장 실패:', error);
    }
  }

  // 목표 추가
  function addGoal() {
    if (newGoal.trim() && !editForm.learning_goals.includes(newGoal.trim())) {
      editForm.learning_goals = [...editForm.learning_goals, newGoal.trim()];
      newGoal = '';
    }
  }

  // 목표 제거
  function removeGoal(index: number) {
    editForm.learning_goals = editForm.learning_goals.filter((_, i) => i !== index);
  }

  // Enter 키로 목표 추가
  function handleGoalKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      event.preventDefault();
      addGoal();
    }
  }

  // 분을 시간:분 형식으로 변환
  function formatMinutes(minutes: number): string {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours}시간 ${mins}분`;
    }
    return `${mins}분`;
  }
</script>

<div class="card bg-base-100 shadow-xl">
  <div class="card-body">
    <!-- 프로필 헤더 -->
    <div class="flex items-start justify-between mb-6">
      <div class="flex items-center space-x-4">
        <!-- 아바타 -->
        <div class="avatar">
          <div class="w-16 h-16 rounded-full">
            {#if $currentUser?.avatar_url}
              <img src={$currentUser.avatar_url} alt="프로필 사진" />
            {:else}
              <div class="bg-primary text-primary-content flex items-center justify-center text-2xl font-bold">
                {$userProfile.name ? $userProfile.name.charAt(0).toUpperCase() : '?'}
              </div>
            {/if}
          </div>
        </div>

        <!-- 기본 정보 -->
        <div>
          <h2 class="text-2xl font-bold text-base-content">
            {$userProfile.name || '이름 없음'}
          </h2>
          <p class="text-base-content/70">
            {japaneseLevels.find(level => level.value === $userProfile.japanese_level)?.label || '레벨 미설정'}
          </p>
          {#if $currentUser?.email}
            <p class="text-sm text-base-content/50">{$currentUser.email}</p>
          {/if}
        </div>
      </div>

      <!-- 편집/저장 버튼 -->
      {#if editable}
        <div class="flex space-x-2">
          {#if isEditing}
            <button 
              type="button" 
              class="btn btn-ghost btn-sm" 
              on:click={cancelEdit}
              disabled={$isLoading}
            >
              취소
            </button>
            <button 
              type="button" 
              class="btn btn-primary btn-sm" 
              class:loading={$isLoading}
              disabled={$isLoading}
              on:click={saveProfile}
            >
              저장
            </button>
          {:else}
            <button 
              type="button" 
              class="btn btn-ghost btn-sm" 
              on:click={startEdit}
            >
              <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              편집
            </button>
          {/if}
        </div>
      {/if}
    </div>

    {#if isEditing}
      <!-- 편집 폼 -->
      <div class="space-y-4">
        <!-- 이름 -->
        <div class="form-control">
          <label class="label" for="profile-name">
            <span class="label-text">이름</span>
          </label>
          <input
            id="profile-name"
            type="text"
            class="input input-bordered"
            bind:value={editForm.name}
            placeholder="이름을 입력하세요"
            required
          />
        </div>

        <!-- 일본어 레벨 -->
        <div class="form-control">
          <label class="label" for="profile-level">
            <span class="label-text">일본어 레벨</span>
          </label>
          <select
            id="profile-level"
            class="select select-bordered"
            bind:value={editForm.japanese_level}
          >
            {#each japaneseLevels as level}
              <option value={level.value}>{level.label}</option>
            {/each}
          </select>
        </div>

        <!-- 자기소개 -->
        <div class="form-control">
          <label class="label" for="profile-bio">
            <span class="label-text">자기소개</span>
          </label>
          <textarea
            id="profile-bio"
            class="textarea textarea-bordered h-24"
            bind:value={editForm.bio}
            placeholder="간단한 자기소개를 작성하세요"
          />
        </div>

        <!-- 학습 목표 -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">학습 목표</span>
          </label>
          <div class="space-y-2">
            <!-- 기존 목표들 -->
            {#each editForm.learning_goals as goal, index}
              <div class="flex items-center space-x-2">
                <span class="flex-1 px-3 py-2 bg-base-200 rounded">{goal}</span>
                <button
                  type="button"
                  class="btn btn-ghost btn-sm btn-circle"
                  on:click={() => removeGoal(index)}
                  aria-label="목표 삭제"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            {/each}
            
            <!-- 새 목표 추가 -->
            <div class="flex space-x-2">
              <input
                type="text"
                class="input input-bordered flex-1"
                bind:value={newGoal}
                placeholder="새로운 학습 목표를 입력하세요"
                on:keydown={handleGoalKeydown}
              />
              <button
                type="button"
                class="btn btn-ghost"
                on:click={addGoal}
                disabled={!newGoal.trim()}
              >
                추가
              </button>
            </div>
          </div>
        </div>

        <!-- 일일 목표 시간 -->
        <div class="form-control">
          <label class="label" for="profile-daily-goal">
            <span class="label-text">일일 학습 목표</span>
          </label>
          <div class="flex items-center space-x-2">
            <input
              id="profile-daily-goal"
              type="number"
              class="input input-bordered w-24"
              bind:value={editForm.daily_goal_minutes}
              min="5"
              max="480"
              step="5"
            />
            <span class="text-base-content/70">분</span>
          </div>
        </div>
      </div>
    {:else}
      <!-- 프로필 표시 -->
      <div class="space-y-4">
        <!-- 자기소개 -->
        {#if $userProfile.bio}
          <div>
            <h3 class="font-semibold text-base-content mb-2">자기소개</h3>
            <p class="text-base-content/80 leading-relaxed">{$userProfile.bio}</p>
          </div>
        {/if}

        <!-- 학습 목표 -->
        {#if $userProfile.learning_goals && $userProfile.learning_goals.length > 0}
          <div>
            <h3 class="font-semibold text-base-content mb-2">학습 목표</h3>
            <div class="flex flex-wrap gap-2">
              {#each $userProfile.learning_goals as goal}
                <span class="badge badge-primary badge-outline">{goal}</span>
              {/each}
            </div>
          </div>
        {/if}

        <!-- 일일 목표 -->
        <div>
          <h3 class="font-semibold text-base-content mb-2">일일 학습 목표</h3>
          <p class="text-base-content/80">
            {formatMinutes($userProfile.daily_goal_minutes || 30)}
          </p>
        </div>
      </div>
    {/if}

    <!-- 학습 통계 -->
    <div class="divider">학습 통계</div>
    
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="stat bg-base-200 rounded-lg p-4">
        <div class="stat-title text-xs">총 청취 시간</div>
        <div class="stat-value text-lg">{formatMinutes($userStats.total_listening_minutes)}</div>
      </div>
      
      <div class="stat bg-base-200 rounded-lg p-4">
        <div class="stat-title text-xs">저장 단어</div>
        <div class="stat-value text-lg">{$userStats.total_words_saved}개</div>
      </div>
      
      <div class="stat bg-base-200 rounded-lg p-4">
        <div class="stat-title text-xs">연속 학습</div>
        <div class="stat-value text-lg">{$userStats.current_streak_days}일</div>
      </div>
      
      <div class="stat bg-base-200 rounded-lg p-4">
        <div class="stat-title text-xs">레벨 진행도</div>
        <div class="stat-value text-lg">{$userStats.level_progress_percentage}%</div>
      </div>
    </div>

    <!-- 오늘의 진행도 -->
    <div class="mt-4">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium">오늘의 학습 진행도</span>
        <span class="text-sm text-base-content/70">
          {Math.floor($learningProgress.dailyProgress)}%
        </span>
      </div>
      <progress 
        class="progress progress-primary w-full" 
        value={$learningProgress.dailyProgress} 
        max="100"
      ></progress>
    </div>
  </div>
</div> 