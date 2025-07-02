<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import { goto } from '$app/navigation';
  import { isLoggedIn, currentUser, userProfile } from '$lib/stores/authStore';
  
  let mounted = false;
  
  const dispatch = createEventDispatcher();
  
  onMount(() => {
    mounted = true;
  });

  // 시작하기 버튼 클릭 처리
  function handleStartLearning() {
    if ($isLoggedIn) {
      // 로그인된 사용자는 스크립트 페이지로 이동
      goto('/scripts');
    } else {
      // 로그인이 필요한 경우 로그인 이벤트 발생
      window.dispatchEvent(new CustomEvent('requestLogin'));
    }
  }

  // 더 알아보기 버튼 클릭 처리
  function handleLearnMore() {
    document.querySelector('#features')?.scrollIntoView({ 
      behavior: 'smooth' 
    });
  }
</script>

<svelte:head>
  <title>🎌 Kiko - 일본어 라디오 학습 플랫폼</title>
  <meta name="description" content="일본어 라디오를 들으며 스크립트를 한 줄씩 따라 읽고 단어장으로 학습하세요" />
</svelte:head>

<!-- 히어로 섹션 -->
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
      
      <!-- 사용자 상태에 따른 다른 버튼 -->
      {#if $isLoggedIn}
        <div class="mb-6">
          <div class="alert alert-success">
            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>환영합니다, {$currentUser?.name || '학습자'}님!</span>
          </div>
        </div>
        
        <div class="flex flex-col sm:flex-row gap-4 justify-center">
          <button class="btn btn-primary btn-lg" on:click={handleStartLearning}>
            🎵 학습 계속하기
          </button>
          <a href="/profile" class="btn btn-outline btn-lg">
            👤 프로필 보기
          </a>
        </div>
        
        <!-- 학습 진행 상황 -->
        {#if $userProfile}
          <div class="mt-8">
            <div class="stats shadow bg-base-100">
                             <div class="stat place-items-center">
                 <div class="stat-title">학습 목표</div>
                 <div class="stat-value text-sm">{$userProfile.japanese_level}</div>
                 <div class="stat-desc">{$userProfile.learning_goals?.join(', ') || '목표 설정하기'}</div>
               </div>
              
              <div class="stat place-items-center">
                <div class="stat-title">학습 언어</div>
                <div class="stat-value text-primary">🇯🇵</div>
                <div class="stat-desc">일본어</div>
              </div>
            </div>
          </div>
        {/if}
      {:else}
        <div class="flex flex-col sm:flex-row gap-4 justify-center">
          <button class="btn btn-primary btn-lg" on:click={handleStartLearning}>
            🎵 시작하기
          </button>
          <button class="btn btn-outline btn-lg" on:click={handleLearnMore}>
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
      {/if}
    </div>
  </div>
</div>

<!-- 기능 소개 섹션 -->
<section id="features" class="py-20 bg-base-100">
  <div class="container mx-auto px-4">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-bold mb-4">주요 기능</h2>
      <p class="text-lg text-base-content/70">일본어 학습을 위한 다양한 기능을 제공합니다</p>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <!-- 라디오 & 스크립트 싱크 -->
      <div class="card bg-base-200 shadow-xl">
        <div class="card-body text-center">
          <div class="text-4xl mb-4">🎵</div>
          <h3 class="card-title justify-center">라디오 & 스크립트 싱크</h3>
          <p class="text-base-content/70">
            일본어 라디오를 들으며 실시간으로 스크립트를 확인하고, 
            문장을 클릭하면 해당 구간으로 바로 이동합니다.
          </p>
          <div class="card-actions justify-center mt-4">
            <div class="badge badge-primary">실시간 동기화</div>
            <div class="badge badge-secondary">구간 반복</div>
          </div>
        </div>
      </div>
      
      <!-- 단어장 & 복습 -->
      <div class="card bg-base-200 shadow-xl">
        <div class="card-body text-center">
          <div class="text-4xl mb-4">📚</div>
          <h3 class="card-title justify-center">단어장 & 복습</h3>
          <p class="text-base-content/70">
            모르는 단어를 클릭하여 의미를 확인하고 개인 단어장에 저장하여 
            플래시카드로 복습할 수 있습니다.
          </p>
          <div class="card-actions justify-center mt-4">
            <div class="badge badge-accent">개인 단어장</div>
            <div class="badge badge-info">플래시카드</div>
          </div>
        </div>
      </div>
      
      <!-- 학습 진행도 -->
      <div class="card bg-base-200 shadow-xl">
        <div class="card-body text-center">
          <div class="text-4xl mb-4">📊</div>
          <h3 class="card-title justify-center">학습 진행도</h3>
          <p class="text-base-content/70">
            학습 시간, 저장된 단어 수, 연속 학습일을 추적하여 
            꾸준한 학습 습관을 만들어보세요.
          </p>
          <div class="card-actions justify-center mt-4">
            <div class="badge badge-success">학습 통계</div>
            <div class="badge badge-warning">목표 설정</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- 개발 진행 상황 -->
<section class="py-20 bg-base-200">
  <div class="container mx-auto px-4">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-bold mb-4">개발 진행 상황</h2>
      <p class="text-lg text-base-content/70">현재 MVP 단계를 개발 중입니다</p>
    </div>
    
    <div class="max-w-4xl mx-auto">
      <div class="timeline timeline-snap-icon max-md:timeline-compact timeline-vertical">
        <!-- Phase 1 -->
        <div class="timeline-item">
          <div class="timeline-middle">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-5 w-5 text-success">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.236 4.53L8.53 10.96a.75.75 0 00-1.06 1.061l2.03 2.03a.75.75 0 001.137-.089l3.857-5.481z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="timeline-start md:text-end mb-10">
            <time class="font-mono italic">Phase 1</time>
            <div class="text-lg font-black">Foundation (MVP) ✓</div>
            <div class="text-sm">계정 시스템, 기본 UI, 인프라 구축 완료</div>
          </div>
          <hr class="bg-success" />
        </div>
        
        <!-- Phase 2 -->
        <div class="timeline-item">
          <hr class="bg-warning" />
          <div class="timeline-middle">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-5 w-5 text-warning">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm.75-13a.75.75 0 00-1.5 0v5c0 .414.336.75.75.75h4a.75.75 0 000-1.5h-3.25V5z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="timeline-end mb-10">
            <time class="font-mono italic">Phase 2</time>
            <div class="text-lg font-black">Feature Enhancement 🚧</div>
            <div class="text-sm">라디오 플레이어, 스크립트 싱크, 단어장 기능 개발 중</div>
          </div>
          <hr />
        </div>
        
        <!-- Phase 3 -->
        <div class="timeline-item">
          <hr />
          <div class="timeline-middle">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-5 w-5">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.236 4.53L8.53 10.96a.75.75 0 00-1.06 1.061l2.03 2.03a.75.75 0 001.137-.089l3.857-5.481z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="timeline-start md:text-end mb-10">
            <time class="font-mono italic">Phase 3</time>
            <div class="text-lg font-black">Scaling & Optimization</div>
            <div class="text-sm">성능 최적화, 고급 기능, 커뮤니티 기능</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
