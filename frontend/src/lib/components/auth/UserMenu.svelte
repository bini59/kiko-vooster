<script lang="ts">
  import { 
    isLoggedIn, 
    currentUser, 
    userProfile, 
    learningProgress,
    authActions 
  } from '$lib/stores/authStore';
  import { createEventDispatcher } from 'svelte';
  import { goto } from '$app/navigation';

  const dispatch = createEventDispatcher<{
    profileClick: void;
    settingsClick: void;
    logout: void;
    loginRequired: void;
  }>();

  // 드롭다운 상태
  let isMenuOpen = false;

  // 메뉴 토글
  function toggleMenu() {
    isMenuOpen = !isMenuOpen;
  }

  // 메뉴 닫기
  function closeMenu() {
    isMenuOpen = false;
  }

  // 바깥 클릭 시 메뉴 닫기
  function handleOutsideClick() {
    closeMenu();
  }

  // 키보드 네비게이션
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      closeMenu();
    }
  }

  // 프로필 페이지로 이동
  function goToProfile() {
    dispatch('profileClick');
    closeMenu();
    goto('/profile');
  }

  // 설정 페이지로 이동
  function goToSettings() {
    dispatch('settingsClick');
    closeMenu();
    goto('/settings');
  }

  // 로그아웃
  async function handleLogout() {
    closeMenu();
    await authActions.logout();
    dispatch('logout');
    goto('/');
  }

  // 아바타 문자 생성
  function getAvatarText(name: string): string {
    return name ? name.charAt(0).toUpperCase() : '?';
  }
</script>

<svelte:window on:keydown={handleKeydown} />

{#if $isLoggedIn}
  <div class="dropdown dropdown-end">
    <!-- 사용자 아바타 버튼 -->
    <div
      role="button"
      tabindex="0"
      class="btn btn-ghost btn-circle avatar"
      on:click={toggleMenu}
      on:keydown={(e) => e.key === 'Enter' && toggleMenu()}
      aria-label="사용자 메뉴"
      aria-expanded={isMenuOpen}
      aria-haspopup="true"
    >
      <div class="w-10 rounded-full">
        {#if $currentUser?.avatar_url}
          <img src={$currentUser.avatar_url} alt="프로필 사진" />
        {:else}
          <div class="bg-primary text-primary-content flex items-center justify-center text-sm font-bold w-full h-full rounded-full">
            {getAvatarText($userProfile.name)}
          </div>
        {/if}
      </div>
    </div>

    <!-- 드롭다운 메뉴 -->
    {#if isMenuOpen}
      <!-- svelte-ignore a11y-click-events-have-key-events -->
      <!-- svelte-ignore a11y-no-static-element-interactions -->
      <div class="fixed inset-0 z-40" on:click={handleOutsideClick}></div>
      
      <div 
        class="dropdown-content z-50 menu p-2 shadow bg-base-100 rounded-box w-80 border border-base-300"
        role="menu"
      >
        <!-- 사용자 정보 헤더 -->
        <div class="px-4 py-3 border-b border-base-300">
          <div class="flex items-center space-x-3">
            <!-- 아바타 -->
            <div class="avatar">
              <div class="w-12 h-12 rounded-full">
                {#if $currentUser?.avatar_url}
                  <img src={$currentUser.avatar_url} alt="프로필 사진" />
                {:else}
                  <div class="bg-primary text-primary-content flex items-center justify-center text-lg font-bold">
                    {getAvatarText($userProfile.name)}
                  </div>
                {/if}
              </div>
            </div>

            <!-- 사용자 정보 -->
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-base-content truncate">
                {$userProfile.name || '이름 없음'}
              </p>
              {#if $currentUser?.email}
                <p class="text-xs text-base-content/70 truncate">
                  {$currentUser.email}
                </p>
              {/if}
            </div>
          </div>

          <!-- 오늘의 학습 진행도 -->
          <div class="mt-3">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-base-content/70">오늘의 학습</span>
              <span class="text-xs text-base-content/70">
                {Math.floor($learningProgress.dailyProgress)}%
              </span>
            </div>
            <progress 
              class="progress progress-primary w-full h-1" 
              value={$learningProgress.dailyProgress} 
              max="100"
            ></progress>
          </div>
        </div>

        <!-- 메뉴 아이템들 -->
        <div class="py-1">
          <!-- 프로필 -->
          <button
            type="button"
            class="flex items-center w-full px-4 py-2 text-sm text-left hover:bg-base-200 rounded-lg"
            on:click={goToProfile}
            role="menuitem"
          >
            <svg class="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            프로필
          </button>

          <!-- 학습 통계 -->
          <button
            type="button"
            class="flex items-center w-full px-4 py-2 text-sm text-left hover:bg-base-200 rounded-lg"
            on:click={() => goto('/stats')}
            role="menuitem"
          >
            <svg class="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            학습 통계
          </button>

          <!-- 단어장 -->
          <button
            type="button"
            class="flex items-center w-full px-4 py-2 text-sm text-left hover:bg-base-200 rounded-lg"
            on:click={() => goto('/vocabulary')}
            role="menuitem"
          >
            <svg class="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            단어장
            {#if $learningProgress.totalWords > 0}
              <span class="ml-auto badge badge-primary badge-sm">
                {$learningProgress.totalWords}
              </span>
            {/if}
          </button>

          <!-- 구분선 -->
          <div class="divider my-1"></div>

          <!-- 설정 -->
          <button
            type="button"
            class="flex items-center w-full px-4 py-2 text-sm text-left hover:bg-base-200 rounded-lg"
            on:click={goToSettings}
            role="menuitem"
          >
            <svg class="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            설정
          </button>

          <!-- 도움말 -->
          <button
            type="button"
            class="flex items-center w-full px-4 py-2 text-sm text-left hover:bg-base-200 rounded-lg"
            on:click={() => goto('/help')}
            role="menuitem"
          >
            <svg class="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            도움말
          </button>

          <!-- 구분선 -->
          <div class="divider my-1"></div>

          <!-- 로그아웃 -->
          <button
            type="button"
            class="flex items-center w-full px-4 py-2 text-sm text-left hover:bg-base-200 rounded-lg text-error"
            on:click={handleLogout}
            role="menuitem"
          >
            <svg class="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            로그아웃
          </button>
        </div>
      </div>
    {/if}
  </div>
{:else}
  <!-- 로그인되지 않은 상태 - 로그인 버튼만 표시 -->
  <div class="flex items-center space-x-2">
    <button
      type="button"
      class="btn btn-ghost btn-sm"
      on:click={() => dispatch('loginRequired')}
    >
      로그인
    </button>
  </div>
{/if}

<style>
  .dropdown-content {
    transform-origin: top right;
    animation: scale-in 0.15s ease;
  }

  @keyframes scale-in {
    from {
      opacity: 0;
      transform: scale(0.95) translateY(-5px);
    }
    to {
      opacity: 1;
      transform: scale(1) translateY(0);
    }
  }
</style> 