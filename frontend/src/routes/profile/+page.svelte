<script lang="ts">
  import { isLoggedIn, authActions } from '$lib/stores/authStore';
  import UserProfile from '$lib/components/auth/UserProfile.svelte';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';

  // 페이지 로드 시 인증 확인
  onMount(() => {
    if (!$isLoggedIn) {
      goto('/');
      return;
    }

    // 사용자 데이터 새로고침
    authActions.loadUserData().catch((error) => {
      console.error('사용자 데이터 로드 실패:', error);
    });
  });

  // 프로필 저장 성공 시 처리
  function handleProfileSaved() {
    // 통계 새로고침
    authActions.refreshStats();
  }
</script>

<svelte:head>
  <title>프로필 - 일본어 학습</title>
  <meta name="description" content="사용자 프로필 관리 및 학습 통계" />
</svelte:head>

{#if $isLoggedIn}
  <div class="container mx-auto px-4 py-8 max-w-4xl">
    <!-- 페이지 헤더 -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold text-base-content">프로필</h1>
        <p class="text-base-content/70 mt-1">
          학습 진행 상황과 개인 정보를 확인하고 관리하세요
        </p>
      </div>

      <!-- 뒤로 가기 버튼 -->
      <button
        type="button"
        class="btn btn-ghost"
        on:click={() => goto('/')}
        aria-label="홈으로 돌아가기"
      >
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        홈으로
      </button>
    </div>

    <!-- 프로필 컴포넌트 -->
    <UserProfile 
      editable={true} 
      on:save={handleProfileSaved}
    />

    <!-- 추가 설정 링크 -->
    <div class="mt-8 card bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title">더 많은 설정</h2>
        <p class="text-base-content/70 mb-4">
          알림, 테마, 언어 등 세부 설정을 관리하세요
        </p>
        
        <div class="card-actions">
          <button
            type="button"
            class="btn btn-primary"
            on:click={() => goto('/settings')}
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            설정 페이지
          </button>
          
          <button
            type="button"
            class="btn btn-outline"
            on:click={() => goto('/stats')}
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            상세 통계
          </button>
        </div>
      </div>
    </div>
  </div>
{:else}
  <!-- 로그인 필요 안내 -->
  <div class="container mx-auto px-4 py-16 text-center">
    <div class="max-w-md mx-auto">
      <svg class="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
      
      <h1 class="text-2xl font-bold text-base-content mb-2">
        로그인이 필요합니다
      </h1>
      
      <p class="text-base-content/70 mb-6">
        프로필을 확인하려면 먼저 로그인해 주세요
      </p>
      
      <button
        type="button"
        class="btn btn-primary"
        on:click={() => goto('/')}
      >
        홈으로 돌아가기
      </button>
    </div>
  </div>
{/if} 