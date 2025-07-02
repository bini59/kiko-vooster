<!-- Settings Page -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { authActions, userPreferences, preferencesActions } from '$lib/stores/authStore';
  import UserPreferences from '$lib/components/auth/UserPreferences.svelte';
  import { showNotification } from '$lib/stores/notificationStore';
  
  let isLoading = true;
  
  onMount(async () => {
    try {
      await preferencesActions.loadPreferences();
    } catch (error) {
      console.error('Failed to load preferences:', error);
      showNotification('설정을 불러오는데 실패했습니다.', 'error');
    } finally {
      isLoading = false;
    }
  });
</script>

<svelte:head>
  <title>설정 - Kiko</title>
  <meta name="description" content="접근성, 테마, 언어 등 개인 설정을 관리하세요." />
</svelte:head>

<main class="container mx-auto px-4 py-8 max-w-4xl">
  <header class="mb-8">
    <h1 class="text-3xl font-bold text-base-content mb-2">설정</h1>
    <p class="text-base-content/70">
      접근성, 테마, 언어 등 개인 설정을 관리하세요.
    </p>
  </header>

  {#if isLoading}
    <div class="flex justify-center items-center min-h-[50vh]">
      <div class="loading loading-spinner loading-lg text-primary"></div>
    </div>
  {:else}
    <div class="grid gap-8">
      <!-- User Preferences Component -->
      <section class="card bg-base-100 shadow-lg">
        <div class="card-body">
          <h2 class="card-title text-xl mb-4">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
            </svg>
            개인 설정
          </h2>
          <UserPreferences />
        </div>
      </section>

      <!-- Additional Settings -->
      <section class="card bg-base-100 shadow-lg">
        <div class="card-body">
          <h2 class="card-title text-xl mb-4">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            추가 정보
          </h2>
          
          <div class="space-y-4">
            <div class="flex justify-between items-center">
              <span class="text-base-content">버전</span>
              <span class="text-base-content/70">1.0.0-beta</span>
            </div>
            
            <div class="divider"></div>
            
            <div class="flex flex-wrap gap-2">
              <a href="/privacy" class="btn btn-ghost btn-sm">개인정보 처리방침</a>
              <a href="/terms" class="btn btn-ghost btn-sm">이용약관</a>
              <a href="/help" class="btn btn-ghost btn-sm">도움말</a>
            </div>
          </div>
        </div>
      </section>
    </div>
  {/if}
</main>

<style>
  main {
    min-height: calc(100vh - 4rem);
  }
</style> 