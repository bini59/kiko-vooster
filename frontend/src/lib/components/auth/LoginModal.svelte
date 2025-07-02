<script lang="ts">
  import { authActions, isLoading, authError } from '$lib/stores/authStore';
  import { createEventDispatcher } from 'svelte';

  // Props
  export let isOpen = false;

  const dispatch = createEventDispatcher<{
    close: void;
    loginSuccess: void;
  }>();

  // 모달 닫기
  function closeModal() {
    isOpen = false;
    dispatch('close');
  }

  // 배경 클릭으로 모달 닫기
  function handleBackgroundClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      closeModal();
    }
  }

  // ESC 키로 모달 닫기
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      closeModal();
    }
  }

  // Google 로그인 핸들러
  async function handleGoogleLogin() {
    try {
      await authActions.loginWithGoogle();
      dispatch('loginSuccess');
      closeModal();
    } catch (error) {
      // 에러는 스토어에서 처리됨
    }
  }

  // Apple 로그인 핸들러
  async function handleAppleLogin() {
    try {
      await authActions.loginWithApple();
      dispatch('loginSuccess');
      closeModal();
    } catch (error) {
      // 에러는 스토어에서 처리됨
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

{#if isOpen}
  <!-- 모달 오버레이 -->
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div 
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
    on:click={handleBackgroundClick}
  >
    <!-- 모달 컨테이너 -->
    <div 
      class="bg-base-100 rounded-lg shadow-xl w-full max-w-md p-6 relative"
      role="dialog"
      aria-labelledby="login-modal-title"
      aria-describedby="login-modal-description"
    >
      <!-- 닫기 버튼 -->
      <button
        type="button"
        class="btn btn-ghost btn-sm btn-circle absolute right-2 top-2"
        on:click={closeModal}
        aria-label="모달 닫기"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <!-- 모달 헤더 -->
      <div class="text-center mb-6">
        <h2 id="login-modal-title" class="text-2xl font-bold text-base-content mb-2">
          일본어 학습을 시작하세요
        </h2>
        <p id="login-modal-description" class="text-base-content/70">
          소셜 계정으로 간편하게 로그인하고<br>개인 맞춤 학습 경험을 시작하세요
        </p>
      </div>

      <!-- 에러 메시지 -->
      {#if $authError}
        <div class="alert alert-error mb-4">
          <svg class="w-6 h-6 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
          <span>{$authError}</span>
        </div>
      {/if}

      <!-- 로그인 버튼들 -->
      <div class="space-y-3">
        <!-- Google 로그인 -->
        <button
          type="button"
          class="btn btn-outline w-full h-12 text-base"
          class:loading={$isLoading}
          disabled={$isLoading}
          on:click={handleGoogleLogin}
        >
          {#if !$isLoading}
            <svg class="w-5 h-5 mr-2" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Google로 로그인
          {:else}
            로그인 중...
          {/if}
        </button>

        <!-- Apple 로그인 -->
        <button
          type="button"
          class="btn btn-outline w-full h-12 text-base"
          class:loading={$isLoading}
          disabled={$isLoading}
          on:click={handleAppleLogin}
        >
          {#if !$isLoading}
            <svg class="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
            </svg>
            Apple로 로그인
          {:else}
            로그인 중...
          {/if}
        </button>
      </div>

      <!-- 약관 동의 -->
      <div class="mt-6 text-center">
        <p class="text-sm text-base-content/60">
          로그인하면 
          <a href="/terms" class="link link-primary">이용약관</a>과 
          <a href="/privacy" class="link link-primary">개인정보처리방침</a>에 
          동의하는 것으로 간주됩니다.
        </p>
      </div>
    </div>
  </div>
{/if}

<style>
  /* 모달 애니메이션 */
  .modal-enter {
    opacity: 0;
  }
  
  .modal-enter-active {
    opacity: 1;
    transition: opacity 0.3s ease;
  }
  
  .modal-leave {
    opacity: 1;
  }
  
  .modal-leave-active {
    opacity: 0;
    transition: opacity 0.3s ease;
  }
</style> 