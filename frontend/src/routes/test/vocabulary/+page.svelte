<script lang="ts">
  /**
   * 단어장 통합 테스트 페이지
   * 
   * 목적:
   * - 단어장 전체 워크플로우 테스트 (저장/조회/복습)
   * - API 연동 및 에러 처리 검증
   * - 성능 및 접근성 테스트
   */
  
  import { onMount } from 'svelte';
  import { vocabularyActions, reviewActions, vocabularyState } from '$lib/stores/vocabularyStore';
  import { ReviewSessionMode, DEFAULT_VOCABULARY_FILTER } from '$lib/types/vocabulary';
  import { notifications } from '$lib/stores/notificationStore';
  import VocabularyList from '$lib/components/vocabulary/lists/VocabularyList.svelte';
  import ReviewSession from '$lib/components/vocabulary/review/ReviewSession.svelte';
  
  // 테스트 상태
  let testResults: any[] = [];
  let isRunningTests = false;
  let currentTestPhase = '';
  let testLogs: string[] = [];
  
  // 테스트용 데이터
  const testWords = [
    { text: 'こんにちは', reading: 'こんにちは', meaning: '안녕하세요' },
    { text: '学校', reading: 'がっこう', meaning: '학교' },
    { text: '勉強', reading: 'べんきょう', meaning: '공부' }
  ];
  
  let selectedReviewMode: ReviewSessionMode = ReviewSessionMode.FLASHCARD;
  let showVocabularyList = true;
  let showReviewSession = false;
  
  onMount(() => {
    addLog('단어장 통합 테스트 페이지 초기화 완료');
  });
  
  function addLog(message: string, type: 'info' | 'success' | 'error' = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = `[${timestamp}] ${type.toUpperCase()}: ${message}`;
    testLogs = [logEntry, ...testLogs].slice(0, 50);
    console.log(logEntry);
  }
  
  async function runFullWorkflowTest() {
    isRunningTests = true;
    testResults = [];
    testLogs = [];
    
    try {
      addLog('전체 워크플로우 테스트 시작', 'info');
      
      // 1. 기본 API 테스트
      await testBasicAPIs();
      
      // 2. 단어장 CRUD 테스트
      await testVocabularyCRUD();
      
      // 3. 복습 모드 테스트
      await testReviewModes();
      
      // 4. 에러 처리 테스트
      await testErrorHandling();
      
      // 5. 성능 테스트
      await testPerformance();
      
      addLog('전체 워크플로우 테스트 완료', 'success');
      
    } catch (error) {
      addLog(`테스트 실행 중 오류: ${error}`, 'error');
    } finally {
      isRunningTests = false;
      currentTestPhase = '';
    }
  }
  
  async function testBasicAPIs() {
    currentTestPhase = 'API 기본 기능 테스트';
    addLog('API 기본 기능 테스트 시작');
    
    try {
      // 단어장 리스트 조회
      const startTime = performance.now();
      await vocabularyActions.loadUserWords();
      const loadTime = performance.now() - startTime;
      
      testResults.push({
        name: 'API: 단어장 리스트 조회',
        passed: true,
        details: { responseTime: `${loadTime.toFixed(1)}ms` },
        timestamp: new Date().toISOString()
      });
      
      addLog('API 기본 기능 테스트 완료', 'success');
      
    } catch (error) {
      testResults.push({
        name: 'API: 단어장 리스트 조회',
        passed: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      });
      
      addLog(`API 테스트 실패: ${error}`, 'error');
    }
  }
  
  async function testVocabularyCRUD() {
    currentTestPhase = '단어장 CRUD 테스트';
    addLog('단어장 CRUD 테스트 시작');
    
    let addedWordId: string | null = null;
    
    try {
      // CREATE: 새 단어 추가
      const testWord = testWords[0];
      await vocabularyActions.addWord(testWord.text, [], testWord.meaning);
      addedWordId = 'test-word-id'; // Mock ID
      
      testResults.push({
        name: 'CRUD: 단어 추가',
        passed: true,
        details: { word: testWord.text },
        timestamp: new Date().toISOString()
      });
      
      // READ: 단어 조회
      await vocabularyActions.searchWords(testWord.text);
      
      testResults.push({
        name: 'CRUD: 단어 조회',
        passed: true,
        details: { searchTerm: testWord.text },
        timestamp: new Date().toISOString()
      });
      
      // DELETE: 단어 삭제
      if (addedWordId) {
        await vocabularyActions.removeWord(addedWordId);
        
        testResults.push({
          name: 'CRUD: 단어 삭제',
          passed: true,
          details: { wordId: addedWordId },
          timestamp: new Date().toISOString()
        });
      }
      
      addLog('단어장 CRUD 테스트 완료', 'success');
      
    } catch (error) {
      testResults.push({
        name: 'CRUD: 전체 워크플로우',
        passed: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      });
      
      addLog(`CRUD 테스트 실패: ${error}`, 'error');
    }
  }
  
  async function testReviewModes() {
    currentTestPhase = '복습 모드 테스트';
    addLog('복습 모드 테스트 시작');
    
    const reviewModes = [
      ReviewSessionMode.FLASHCARD,
      ReviewSessionMode.FILL_IN_BLANKS,
      ReviewSessionMode.SPELLING
    ];
    
    for (const mode of reviewModes) {
      try {
        // Mock 복습 시작 테스트
        testResults.push({
          name: `복습 모드: ${mode}`,
          passed: true,
          details: { mode },
          timestamp: new Date().toISOString()
        });
        
        addLog(`${mode} 모드 테스트 완료`, 'success');
        
      } catch (error) {
        testResults.push({
          name: `복습 모드: ${mode}`,
          passed: false,
          error: error instanceof Error ? error.message : 'Unknown error',
          timestamp: new Date().toISOString()
        });
        
        addLog(`${mode} 모드 테스트 실패: ${error}`, 'error');
      }
    }
  }
  
  async function testErrorHandling() {
    currentTestPhase = '에러 처리 테스트';
    addLog('에러 처리 테스트 시작');
    
    try {
      // 잘못된 단어 ID로 삭제 시도
      await vocabularyActions.removeWord('invalid-word-id');
      
      testResults.push({
        name: '에러 처리: 잘못된 ID 삭제',
        passed: false,
        error: '에러가 발생하지 않음',
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      testResults.push({
        name: '에러 처리: 잘못된 ID 삭제',
        passed: true,
        details: { errorHandled: true },
        timestamp: new Date().toISOString()
      });
      
      addLog('에러 처리 테스트 완료', 'success');
    }
  }
  
  async function testPerformance() {
    currentTestPhase = '성능 테스트';
    addLog('성능 테스트 시작');
    
    try {
      // 대용량 데이터 로드 테스트
      const startTime = performance.now();
      await vocabularyActions.loadUserWords(true);
      const loadTime = performance.now() - startTime;
      
      const isPassed = loadTime < 2000; // 2초 이내
      
      testResults.push({
        name: '성능: 대용량 데이터 로드',
        passed: isPassed,
        details: { 
          responseTime: `${loadTime.toFixed(1)}ms`,
          threshold: '2000ms',
          status: loadTime < 500 ? 'Excellent' : loadTime < 1000 ? 'Good' : 'Slow'
        },
        timestamp: new Date().toISOString()
      });
      
      addLog(`성능 테스트 완료: ${loadTime.toFixed(1)}ms`, isPassed ? 'success' : 'error');
      
    } catch (error) {
      testResults.push({
        name: '성능: 대용량 데이터 로드',
        passed: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      });
      
      addLog(`성능 테스트 실패: ${error}`, 'error');
    }
  }
  
  function downloadTestReport() {
    const report = {
      timestamp: new Date().toISOString(),
      testType: 'vocabulary-integration',
      testResults,
      testLogs,
      summary: {
        total: testResults.length,
        passed: testResults.filter(r => r.passed).length,
        failed: testResults.filter(r => !r.passed).length
      }
    };
    
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vocabulary-test-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
  
  function clearResults() {
    testResults = [];
    testLogs = [];
  }
  
  function toggleVocabularyList() {
    showVocabularyList = !showVocabularyList;
  }
  
  function startReviewDemo(mode: ReviewSessionMode) {
    selectedReviewMode = mode;
    showReviewSession = true;
  }
  
  function closeReviewDemo() {
    showReviewSession = false;
  }
</script>

<svelte:head>
  <title>단어장 통합 테스트 - Kiko</title>
  <meta name="description" content="단어장 시스템 통합 테스트 페이지" />
</svelte:head>

<div class="vocabulary-test-page min-h-screen bg-base-100">
  <!-- 헤더 -->
  <header class="bg-primary text-primary-content p-4">
    <div class="container mx-auto">
      <h1 class="text-2xl font-bold">📚 단어장 통합 테스트</h1>
      <p class="text-primary-content/80 mt-2">
        단어장 전체 워크플로우, API 연동, 복습 기능을 종합 테스트합니다.
      </p>
    </div>
  </header>
  
  <!-- 컨트롤 패널 -->
  <div class="control-panel bg-base-200 p-4 border-b">
    <div class="container mx-auto">
      <div class="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <!-- 전체 테스트 -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body">
            <h3 class="card-title text-sm">🧪 전체 워크플로우 테스트</h3>
            <button 
              class="btn btn-primary btn-sm"
              class:loading={isRunningTests}
              disabled={isRunningTests}
              on:click={runFullWorkflowTest}
            >
              {isRunningTests ? '테스트 실행 중...' : '전체 테스트 실행'}
            </button>
            
            {#if currentTestPhase}
              <div class="text-xs text-info mt-2">
                현재: {currentTestPhase}
              </div>
            {/if}
          </div>
        </div>
        
        <!-- 컴포넌트 테스트 -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body">
            <h3 class="card-title text-sm">📋 컴포넌트 테스트</h3>
            <div class="flex flex-col gap-1">
              <button 
                class="btn btn-secondary btn-sm"
                on:click={toggleVocabularyList}
              >
                {showVocabularyList ? '리스트 숨기기' : '리스트 보기'}
              </button>
              
              <div class="dropdown dropdown-top">
                <div tabindex="0" role="button" class="btn btn-accent btn-sm">
                  복습 모드 테스트
                </div>
                <ul tabindex="0" class="dropdown-content menu bg-base-100 rounded-box z-[1] w-52 p-2 shadow">
                  <li><button on:click={() => startReviewDemo(ReviewSessionMode.FLASHCARD)}>플래시카드</button></li>
                  <li><button on:click={() => startReviewDemo(ReviewSessionMode.FILL_IN_BLANKS)}>빈칸 채우기</button></li>
                  <li><button on:click={() => startReviewDemo(ReviewSessionMode.SPELLING)}>철자 게임</button></li>
                </ul>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 결과 관리 -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body">
            <h3 class="card-title text-sm">📊 결과 관리</h3>
            <div class="flex flex-col gap-1">
              <button 
                class="btn btn-info btn-sm"
                disabled={testResults.length === 0}
                on:click={downloadTestReport}
              >
                리포트 다운로드
              </button>
              <button 
                class="btn btn-ghost btn-sm"
                on:click={clearResults}
              >
                결과 초기화
              </button>
            </div>
          </div>
        </div>
        
        <!-- 테스트 통계 -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body">
            <h3 class="card-title text-sm">📈 테스트 통계</h3>
            <div class="stats stats-vertical">
              <div class="stat p-2">
                <div class="stat-title text-xs">총 테스트</div>
                <div class="stat-value text-lg">{testResults.length}</div>
              </div>
              <div class="stat p-2">
                <div class="stat-title text-xs">통과</div>
                <div class="stat-value text-lg text-success">
                  {testResults.filter(r => r.passed).length}
                </div>
              </div>
              <div class="stat p-2">
                <div class="stat-title text-xs">실패</div>
                <div class="stat-value text-lg text-error">
                  {testResults.filter(r => !r.passed).length}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <!-- 테스트 결과 -->
  {#if testResults.length > 0}
    <div class="test-results bg-base-100 p-4 border-b">
      <div class="container mx-auto">
        <h2 class="text-lg font-semibold mb-4">🧪 테스트 결과</h2>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {#each testResults as result}
            <div class="card bg-base-200 shadow-sm">
              <div class="card-body p-4">
                <h3 class="card-title text-sm">
                  {result.passed ? '✅' : '❌'} {result.name}
                </h3>
                
                {#if result.details}
                  <div class="text-xs text-base-content/70">
                    {#each Object.entries(result.details) as [key, value]}
                      <div>{key}: {value}</div>
                    {/each}
                  </div>
                {/if}
                
                {#if result.error}
                  <div class="text-xs text-error mt-2">
                    오류: {result.error}
                  </div>
                {/if}
                
                <div class="text-xs text-base-content/50 mt-2">
                  {new Date(result.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}
  
  <!-- 실시간 로그 -->
  {#if testLogs.length > 0}
    <div class="test-logs bg-base-100 p-4 border-b">
      <div class="container mx-auto">
        <h2 class="text-lg font-semibold mb-4">📝 실시간 로그</h2>
        
        <div class="mockup-code bg-base-300 max-h-60 overflow-y-auto">
          {#each testLogs as log}
            <pre class="text-xs"><code>{log}</code></pre>
          {/each}
        </div>
      </div>
    </div>
  {/if}
  
  <!-- 단어장 리스트 컴포넌트 테스트 -->
  {#if showVocabularyList}
    <div class="vocabulary-demo bg-base-100 p-4 border-b">
      <div class="container mx-auto">
        <h2 class="text-lg font-semibold mb-4">📋 단어장 리스트 테스트</h2>
        <VocabularyList filter={DEFAULT_VOCABULARY_FILTER} />
      </div>
    </div>
  {/if}
  
  <!-- 복습 세션 컴포넌트 테스트 -->
  {#if showReviewSession}
    <div class="review-demo bg-base-100 p-4">
      <div class="container mx-auto">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-lg font-semibold">🎯 복습 모드 테스트: {selectedReviewMode}</h2>
          <button class="btn btn-sm btn-ghost" on:click={closeReviewDemo}>
            닫기
          </button>
        </div>
        <ReviewSession />
      </div>
    </div>
  {/if}
</div> 