<script lang="ts">
  import { onMount } from 'svelte';
  
  let mounted = false;
  
  onMount(() => {
    mounted = true;
  });
</script>

<svelte:head>
  <title>🎌 Kiko - 일본어 라디오 학습 플랫폼</title>
  <meta name="description" content="일본어 라디오를 들으며 스크립트를 한 줄씩 따라 읽고 단어장으로 학습하세요" />
</svelte:head>

<div class="hero min-h-screen bg-gradient-to-br from-primary/10 to-secondary/10">
  <div class="hero-content text-center">
    <div class="max-w-md animate-fade-in">
      <h1 class="text-5xl font-bold mb-6">
        🎌 <span class="text-primary">Kiko</span>
      </h1>
      
      <h2 class="text-2xl font-bold text-jp mb-4">
        一緒に日本語を学びましょう！
      </h2>
      
      <p class="text-lg mb-8 text-base-content/80">
        일본어 라디오를 들으며 스크립트를 한 줄씩 따라 읽고,<br>
        단어장을 통해 어휘를 학습할 수 있는 웹 서비스입니다.
      </p>
      
      <div class="flex flex-col sm:flex-row gap-4 justify-center">
        <button class="btn btn-primary btn-lg">
          🎵 시작하기
        </button>
        <button class="btn btn-outline btn-lg">
          📚 더 알아보기
        </button>
      </div>
      
      <div class="mt-12">
        <div class="stats shadow bg-base-100">
          <div class="stat place-items-center">
            <div class="stat-title">프로젝트 상태</div>
            <div class="stat-value text-primary">개발 중</div>
            <div class="stat-desc">MVP 단계</div>
          </div>
          
          <div class="stat place-items-center">
            <div class="stat-title">기술 스택</div>
            <div class="stat-value text-secondary">SvelteKit</div>
            <div class="stat-desc">+ FastAPI</div>
          </div>
        </div>
      </div>
      
      {#if mounted}
        <div class="mt-8">
          <div class="alert alert-info">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span>Tailwind CSS + DaisyUI가 성공적으로 적용되었습니다! 🎉</span>
          </div>
        </div>
      {/if}
      
      <div class="mt-8">
        <div class="mockup-browser border bg-base-300">
          <div class="mockup-browser-toolbar">
            <div class="input">http://localhost:5173</div>
          </div>
          <div class="flex justify-center px-4 py-16 bg-base-200">
            <div class="text-center">
              <h3 class="text-lg font-bold mb-2">🚧 개발 진행 중</h3>
              <p class="text-sm">라디오 플레이어와 스크립트 동기화 기능을 구현 중입니다.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
