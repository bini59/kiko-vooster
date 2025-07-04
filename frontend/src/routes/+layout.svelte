<script lang="ts">
  import '../styles/app.css';
  import UserMenu from '$lib/components/auth/UserMenu.svelte';
  import LoginModal from '$lib/components/auth/LoginModal.svelte';
  import NotificationContainer from '$lib/components/common/NotificationContainer.svelte';
  import GlobalNotification from '$lib/components/common/GlobalNotification.svelte';
  import { isLoggedIn, authActions } from '$lib/stores/authStore';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';

  // 로그인 모달 상태
  let showLoginModal = false;

  // 페이지 로드 시 인증 상태 복원 및 이벤트 리스너 등록
  onMount(() => {
    // 이미 authStore에서 처리됨
    
    // 전역 로그인 요청 이벤트 리스너
    const handleLoginRequest = () => {
      openLoginModal();
    };
    
    window.addEventListener('requestLogin', handleLoginRequest);
    
    return () => {
      window.removeEventListener('requestLogin', handleLoginRequest);
    };
  });

  // 로그인 모달 열기
  function openLoginModal() {
    showLoginModal = true;
  }

  // 로그인 모달 닫기
  function closeLoginModal() {
    showLoginModal = false;
  }

  // 로그인 성공 처리
  function handleLoginSuccess() {
    showLoginModal = false;
    // 추가 처리 필요시 여기에
  }

  // 로그아웃 처리
  function handleLogout() {
    goto('/');
  }
</script>

<!-- 접근성: 스킵 링크 -->
<a href="#main-content" class="skip-link">메인 콘텐츠로 바로가기</a>

<!-- 네비게이션 바 -->
<nav class="navbar bg-base-100 shadow-lg sticky top-0 z-40">
  <div class="container mx-auto">
    <!-- 네비게이션 시작 -->
    <div class="navbar-start">
      <!-- 로고/홈 링크 -->
      <a href="/" class="btn btn-ghost text-xl font-bold">
        🎌 일본어 학습
      </a>
    </div>

    <!-- 네비게이션 중앙 (데스크톱) -->
    <div class="navbar-center hidden lg:flex">
      <ul class="menu menu-horizontal px-1">
        <li><a href="/scripts" class="hover:bg-base-200">스크립트</a></li>
        <li><a href="/vocabulary" class="hover:bg-base-200">단어장</a></li>
        <li><a href="/practice" class="hover:bg-base-200">연습</a></li>
      </ul>
    </div>

    <!-- 네비게이션 끝 -->
    <div class="navbar-end">
      <!-- 모바일 메뉴 (햄버거) -->
      <div class="dropdown dropdown-end lg:hidden">
        <div tabindex="0" role="button" class="btn btn-ghost" aria-label="메뉴 열기">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </div>
        <ul role="menu" class="menu menu-sm dropdown-content mt-3 z-[1] p-2 shadow bg-base-100 rounded-box w-52">
          <li><a href="/scripts" role="menuitem">스크립트</a></li>
          <li><a href="/vocabulary" role="menuitem">단어장</a></li>
          <li><a href="/practice" role="menuitem">연습</a></li>
          {#if !$isLoggedIn}
            <div class="divider"></div>
            <li><button type="button" role="menuitem" on:click={openLoginModal}>로그인</button></li>
          {/if}
        </ul>
      </div>

      <!-- 사용자 메뉴 또는 로그인 버튼 -->
      <UserMenu 
        on:loginRequired={openLoginModal}
        on:logout={handleLogout}
      />
    </div>
  </div>
</nav>

<!-- 메인 콘텐츠 -->
<main id="main-content" class="min-h-screen bg-base-200">
  <slot />
</main>

<!-- 로그인 모달 -->
<LoginModal 
  bind:isOpen={showLoginModal}
  on:close={closeLoginModal}
  on:loginSuccess={handleLoginSuccess}
/>

<!-- 푸터 -->
<footer class="footer footer-center p-10 bg-base-100 text-base-content">
  <aside>
    <svg class="w-12 h-12 text-primary" fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 2L13.09 8.26L20 9L13.09 9.74L12 16L10.91 9.74L4 9L10.91 8.26L12 2Z"/>
    </svg>
    <p class="font-bold">
      일본어 학습 플랫폼
      <br />
      라디오와 함께하는 즐거운 일본어 공부
    </p>
    <p>Copyright © 2024 - All rights reserved</p>
  </aside>
  <nav>
    <div class="grid grid-flow-col gap-4">
      <a href="/about" class="link link-hover">소개</a>
      <a href="/terms" class="link link-hover">이용약관</a>
      <a href="/privacy" class="link link-hover">개인정보처리방침</a>
      <a href="/contact" class="link link-hover">문의</a>
    </div>
  </nav>
</footer>

<!-- 글로벌 알림 시스템 -->
<NotificationContainer /> 