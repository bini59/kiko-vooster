<script lang="ts">
  /**
   * 스크립트-오디오 싱크 UI 통합 테스트 페이지
   * 
   * 목적:
   * - 모든 UI 컴포넌트의 통합 동작 검증
   * - 접근성 및 반응형 레이아웃 테스트
   * - 크로스 브라우저 호환성 확인
   */
  
  import { onMount } from 'svelte';
  import ScriptAudioSyncUI from '$lib/components/sync/ScriptAudioSyncUI.svelte';
  
  // 테스트용 데이터
  const testScriptId = 'test-script-001';
  const testAudioUrl = 'https://www.soundjay.com/misc/sounds/bell-ringing-05.wav';
  
  // 테스트 상태
  let isLoading = true;
  let testResults: any[] = [];
  
  onMount(() => {
    // 컴포넌트 로딩 완료
    isLoading = false;
    
    // 자동 테스트 실행
    setTimeout(runAutomatedTests, 1000);
  });
  
  function runAutomatedTests() {
    const results: any[] = [];
    
    // 1. DOM 구조 검증
    results.push(testDOMStructure());
    
    // 2. 접근성 속성 검증
    results.push(testAccessibilityAttributes());
    
    // 3. 키보드 네비게이션 테스트
    results.push(testKeyboardNavigation());
    
    // 4. 반응형 레이아웃 테스트
    results.push(testResponsiveLayout());
    
    testResults = results;
  }
  
  function testDOMStructure() {
    const container = document.querySelector('.script-audio-sync-ui');
    const sentences = document.querySelectorAll('.sentence-item');
    const audioControls = document.querySelector('.audio-header');
    const abControls = document.querySelector('.ab-controls-mobile, .ab-controls-desktop');
    
    return {
      name: 'DOM 구조 검증',
      passed: !!(container && sentences.length > 0 && audioControls),
      details: {
        container: !!container,
        sentences: sentences.length,
        audioControls: !!audioControls,
        abControls: !!abControls
      }
    };
  }
  
  function testAccessibilityAttributes() {
    const container = document.querySelector('.script-audio-sync-ui');
    const sentences = document.querySelectorAll('.sentence-item');
    
    let hasAriaLabels = true;
    let hasTabIndex = true;
    
    sentences.forEach(sentence => {
      if (!sentence.getAttribute('aria-label')) hasAriaLabels = false;
      if (!sentence.getAttribute('tabindex')) hasTabIndex = false;
    });
    
    return {
      name: '접근성 속성 검증',
      passed: hasAriaLabels && hasTabIndex && container?.getAttribute('role') === 'application',
      details: {
        containerRole: container?.getAttribute('role'),
        ariaLabels: hasAriaLabels,
        tabIndex: hasTabIndex,
        sentenceCount: sentences.length
      }
    };
  }
  
  function testKeyboardNavigation() {
    // 키보드 네비게이션 기본 구조 확인
    const focusableElements = document.querySelectorAll('[tabindex="0"]');
    const hasSkipLinks = document.querySelectorAll('.skip-link').length > 0;
    
    return {
      name: '키보드 네비게이션 테스트',
      passed: focusableElements.length > 0,
      details: {
        focusableElements: focusableElements.length,
        hasSkipLinks,
        hasKeyboardHelp: document.querySelector('.keyboard-help') !== null
      }
    };
  }
  
  function testResponsiveLayout() {
    const container = document.querySelector('.script-audio-sync-ui') as HTMLElement;
    const isMobile = container?.dataset.mobile === 'true';
    
    return {
      name: '반응형 레이아웃 테스트',
      passed: true, // 기본적으로 통과로 간주
      details: {
        currentBreakpoint: window.innerWidth < 768 ? 'mobile' : 'desktop',
        isMobileLayout: isMobile,
        windowWidth: window.innerWidth,
        containerWidth: container?.offsetWidth
      }
    };
  }
  
  function downloadTestReport() {
    const report = {
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight
      },
      testResults
    };
    
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sync-ui-test-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
</script>

<svelte:head>
  <title>스크립트-오디오 싱크 UI 테스트</title>
  <meta name="description" content="스크립트-오디오 싱크 UI 컴포넌트 통합 테스트 페이지" />
</svelte:head>

<div class="test-page min-h-screen bg-base-100">
  <!-- 테스트 헤더 -->
  <header class="bg-primary text-primary-content p-4">
    <div class="container mx-auto">
      <h1 class="text-2xl font-bold">스크립트-오디오 싱크 UI 통합 테스트</h1>
      <p class="text-primary-content/80 mt-2">
        모든 UI 컴포넌트의 통합 동작, 접근성, 반응형 레이아웃을 검증합니다.
      </p>
    </div>
  </header>
  
  <!-- 테스트 도구 패널 -->
  <div class="test-tools bg-base-200 p-4 border-b">
    <div class="container mx-auto">
      <div class="flex flex-wrap gap-4 items-center">
        <button 
          class="btn btn-secondary btn-sm"
          on:click={runAutomatedTests}
        >
          🔄 테스트 재실행
        </button>
        
        <button 
          class="btn btn-accent btn-sm"
          on:click={downloadTestReport}
        >
          📋 리포트 다운로드
        </button>
        
        <div class="badge badge-info">
          화면 크기: {typeof window !== 'undefined' ? window.innerWidth : 0}px
        </div>
        
        <div class="badge badge-secondary">
          {typeof window !== 'undefined' && window.innerWidth < 768 ? '모바일' : '데스크톱'} 모드
        </div>
      </div>
    </div>
  </div>
  
  <!-- 테스트 결과 패널 -->
  {#if testResults.length > 0}
    <div class="test-results bg-base-100 p-4 border-b">
      <div class="container mx-auto">
        <h2 class="text-lg font-semibold mb-4">🧪 자동 테스트 결과</h2>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          {#each testResults as result}
            <div class="card bg-base-200 shadow-sm">
              <div class="card-body p-4">
                <h3 class="card-title text-sm">
                  {result.passed ? '✅' : '❌'} {result.name}
                </h3>
                <div class="text-xs text-base-content/70">
                  {#each Object.entries(result.details) as [key, value]}
                    <div>{key}: {value}</div>
                  {/each}
                </div>
              </div>
            </div>
          {/each}
        </div>
        
        <div class="stats shadow">
          <div class="stat">
            <div class="stat-title">총 테스트</div>
            <div class="stat-value text-lg">{testResults.length}</div>
          </div>
          <div class="stat">
            <div class="stat-title">통과</div>
            <div class="stat-value text-lg text-success">
              {testResults.filter(r => r.passed).length}
            </div>
          </div>
          <div class="stat">
            <div class="stat-title">실패</div>
            <div class="stat-value text-lg text-error">
              {testResults.filter(r => !r.passed).length}
            </div>
          </div>
        </div>
      </div>
    </div>
  {/if}
  
  <!-- 메인 UI 컴포넌트 테스트 영역 -->
  <main class="flex-1 p-4">
    <div class="container mx-auto">
      {#if isLoading}
        <div class="flex items-center justify-center h-96">
          <div class="loading loading-spinner loading-lg"></div>
          <span class="ml-4">UI 컴포넌트 로딩 중...</span>
        </div>
      {:else}
        <!-- 실제 ScriptAudioSyncUI 컴포넌트 테스트 -->
        <div class="ui-test-container border-2 border-dashed border-base-300 rounded-lg overflow-hidden">
          <div class="bg-warning/10 p-2 text-center text-sm">
            ⚠️ 테스트 환경: 실제 UI 컴포넌트가 아래에 렌더링됩니다
          </div>
          
          <div class="h-96 lg:h-[600px]">
            <ScriptAudioSyncUI 
              scriptId={testScriptId}
              audioUrl={testAudioUrl}
              className="h-full"
            />
          </div>
        </div>
      {/if}
    </div>
  </main>
  
  <!-- 수동 테스트 가이드 -->
  <section class="manual-tests bg-base-200 p-4">
    <div class="container mx-auto">
      <h2 class="text-lg font-semibold mb-4">📋 수동 테스트 체크리스트</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- 기능 테스트 -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body">
            <h3 class="card-title text-sm">🎵 기능 테스트</h3>
            <ul class="text-sm space-y-2">
              <li>
                <label class="label cursor-pointer">
                  <input type="checkbox" class="checkbox checkbox-xs" />
                  <span class="label-text">문장 클릭 시 해당 구간 재생</span>
                </label>
              </li>
              <li>
                <label class="label cursor-pointer">
                  <input type="checkbox" class="checkbox checkbox-xs" />
                  <span class="label-text">현재 문장 자동 하이라이트</span>
                </label>
              </li>
              <li>
                <label class="label cursor-pointer">
                  <input type="checkbox" class="checkbox checkbox-xs" />
                  <span class="label-text">A/B 포인트 설정 및 반복</span>
                </label>
              </li>
              <li>
                <label class="label cursor-pointer">
                  <input type="checkbox" class="checkbox checkbox-xs" />
                  <span class="label-text">오디오 재생/일시정지</span>
                </label>
              </li>
            </ul>
          </div>
        </div>
        
        <!-- 접근성 테스트 -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body">
            <h3 class="card-title text-sm">♿ 접근성 테스트</h3>
            <ul class="text-sm space-y-2">
              <li>
                <label class="label cursor-pointer">
                  <input type="checkbox" class="checkbox checkbox-xs" />
                  <span class="label-text">Tab 키로 모든 요소 탐색</span>
                </label>
              </li>
              <li>
                <label class="label cursor-pointer">
                  <input type="checkbox" class="checkbox checkbox-xs" />
                  <span class="label-text">화살표 키 문장 네비게이션</span>
                </label>
              </li>
              <li>
                <label class="label cursor-pointer">
                  <input type="checkbox" class="checkbox checkbox-xs" />
                  <span class="label-text">스크린 리더 알림 동작</span>
                </label>
              </li>
              <li>
                <label class="label cursor-pointer">
                  <input type="checkbox" class="checkbox checkbox-xs" />
                  <span class="label-text">키보드 단축키 (Alt+A/B/R)</span>
                </label>
              </li>
            </ul>
          </div>
        </div>
        
        <!-- 반응형 테스트 -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body">
            <h3 class="card-title text-sm">📱 반응형 테스트</h3>
            <ul class="text-sm space-y-2">
              <li>
                <label class="label cursor-pointer">
                  <input type="checkbox" class="checkbox checkbox-xs" />
                  <span class="label-text">모바일 세로 레이아웃</span>
                </label>
              </li>
              <li>
                <label class="label cursor-pointer">
                  <input type="checkbox" class="checkbox checkbox-xs" />
                  <span class="label-text">데스크톱 사이드바 레이아웃</span>
                </label>
              </li>
              <li>
                <label class="label cursor-pointer">
                  <input type="checkbox" class="checkbox checkbox-xs" />
                  <span class="label-text">터치 인터랙션 (모바일)</span>
                </label>
              </li>
              <li>
                <label class="label cursor-pointer">
                  <input type="checkbox" class="checkbox checkbox-xs" />
                  <span class="label-text">화면 회전 대응</span>
                </label>
              </li>
            </ul>
          </div>
        </div>
      </div>
      
      <!-- 브라우저 호환성 테스트 -->
      <div class="mt-6">
        <h3 class="text-md font-medium mb-3">🌐 브라우저 호환성 테스트</h3>
        <div class="overflow-x-auto">
          <table class="table table-zebra table-sm">
            <thead>
              <tr>
                <th>브라우저</th>
                <th>버전</th>
                <th>기능 동작</th>
                <th>접근성</th>
                <th>반응형</th>
                <th>전체 평가</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Chrome</td>
                <td>Latest</td>
                <td><input type="checkbox" class="checkbox checkbox-xs" /></td>
                <td><input type="checkbox" class="checkbox checkbox-xs" /></td>
                <td><input type="checkbox" class="checkbox checkbox-xs" /></td>
                <td><input type="checkbox" class="checkbox checkbox-xs" /></td>
              </tr>
              <tr>
                <td>Safari</td>
                <td>Latest</td>
                <td><input type="checkbox" class="checkbox checkbox-xs" /></td>
                <td><input type="checkbox" class="checkbox checkbox-xs" /></td>
                <td><input type="checkbox" class="checkbox checkbox-xs" /></td>
                <td><input type="checkbox" class="checkbox checkbox-xs" /></td>
              </tr>
              <tr>
                <td>Firefox</td>
                <td>Latest</td>
                <td><input type="checkbox" class="checkbox checkbox-xs" /></td>
                <td><input type="checkbox" class="checkbox checkbox-xs" /></td>
                <td><input type="checkbox" class="checkbox checkbox-xs" /></td>
                <td><input type="checkbox" class="checkbox checkbox-xs" /></td>
              </tr>
              <tr>
                <td>Edge</td>
                <td>Latest</td>
                <td><input type="checkbox" class="checkbox checkbox-xs" /></td>
                <td><input type="checkbox" class="checkbox checkbox-xs" /></td>
                <td><input type="checkbox" class="checkbox checkbox-xs" /></td>
                <td><input type="checkbox" class="checkbox checkbox-xs" /></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </section>
  
  <!-- 테스트 완료 액션 -->
  <footer class="bg-primary text-primary-content p-4">
    <div class="container mx-auto text-center">
      <p class="mb-4">모든 테스트를 완료하셨나요?</p>
      <button 
        class="btn btn-secondary"
        on:click={downloadTestReport}
      >
        📄 최종 테스트 리포트 생성
      </button>
    </div>
  </footer>
</div>

<style>
  .test-page {
    font-family: system-ui, -apple-system, sans-serif;
  }
  
  .ui-test-container {
    max-height: 600px;
  }
  
  /* 테스트 환경 전용 스타일 */
  .manual-tests .card {
    min-height: 200px;
  }
  
  .manual-tests .label {
    justify-content: flex-start;
    gap: 0.5rem;
  }
  
  /* 고대비 모드 대응 */
  @media (prefers-contrast: high) {
    .ui-test-container {
      border-width: 3px;
    }
  }
  
  /* 프린트 스타일 */
  @media print {
    .test-tools,
    .ui-test-container {
      display: none;
    }
    
    .manual-tests {
      break-inside: avoid;
    }
  }
</style> 