<script lang="ts">
  /**
   * 백엔드 통합 테스트 페이지
   * 
   * 목적:
   * - playerIntegrationService를 통한 완전한 백엔드 통합 테스트
   * - API 연동, WebSocket 연결, 실시간 동기화 검증
   * - 실제 시나리오 기반 E2E 테스트
   */
  
  import { onMount, onDestroy } from 'svelte';
  import { get } from 'svelte/store';
  
  // 통합 서비스 및 API
  import { playerIntegrationService } from '$lib/services/playerIntegrationService.js';
  import { websocketService, wsConnectionState } from '$lib/services/websocketService.js';
  import { scriptsApi, audioApi, syncApi } from '$lib/api/index.js';
  
  // Mock API
  import { enableMockMode, disableMockMode, mockApiServer } from '$lib/api/mockServer.js';
  
  // Stores
  import { audioState } from '$lib/stores/audioStore.js';
  import { currentScript } from '$lib/stores/scriptStore.js';
  
  // UI Components
  import ScriptAudioSyncUI from '$lib/components/sync/ScriptAudioSyncUI.svelte';
  
  // 테스트 상태
  let isInitialized = false;
  let isLoading = false;
  let testResults: any[] = [];
  let currentError: string | null = null;
  let integrationState: any = null;
  
  // Mock API 모드
  let isMockMode = false;
  let mockModeChangeCount = 0;
  
  // 테스트용 스크립트 ID (실제 백엔드에 존재해야 함)
  let testScriptId = 'demo-news-001';
  let customScriptId = '';
  
  // 실시간 상태 모니터링
  let wsState: any = {};
  let audioStoreState: any = {};
  let scriptStoreState: any = {};
  
  // 상태 업데이트 인터벌
  let stateUpdateInterval: number;
  
  // 실시간 로그
  let testLogs: string[] = [];
  let maxLogCount = 50;
  
  onMount(async () => {
    // 통합 서비스 초기화
    try {
      await playerIntegrationService.initialize();
      isInitialized = true;
      
      // 실시간 상태 모니터링 시작
      startStateMonitoring();
      
    } catch (error) {
      currentError = error instanceof Error ? error.message : 'Initialization failed';
      console.error('Failed to initialize integration service:', error);
    }
  });
  
  onDestroy(() => {
    // 정리
    stopStateMonitoring();
    playerIntegrationService.cleanup();
  });
  
  function startStateMonitoring() {
    stateUpdateInterval = setInterval(() => {
      wsState = get(wsConnectionState);
      audioStoreState = get(audioState);
      scriptStoreState = get(currentScript);
      integrationState = playerIntegrationService.getState();
    }, 1000);
  }
  
  function stopStateMonitoring() {
    if (stateUpdateInterval) {
      clearInterval(stateUpdateInterval);
    }
  }
  
  function addLog(message: string, type: 'info' | 'error' | 'success' = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = `[${timestamp}] ${type.toUpperCase()}: ${message}`;
    testLogs = [logEntry, ...testLogs].slice(0, maxLogCount);
    console.log(logEntry);
  }
  
  function clearLogs() {
    testLogs = [];
  }
  
  async function loadTestScript() {
    const scriptId = customScriptId || testScriptId;
    
    if (!scriptId) {
      currentError = 'Script ID is required';
      addLog('스크립트 ID가 필요합니다', 'error');
      return;
    }
    
    try {
      isLoading = true;
      currentError = null;
      
      addLog(`통합 테스트 시작: ${scriptId}`, 'info');
      addLog(`Mock 모드: ${isMockMode ? 'ON' : 'OFF'}`, 'info');
      
      // 통합 서비스를 통해 스크립트 로드
      await playerIntegrationService.loadScript(scriptId);
      
      addLog('스크립트 로드 완료', 'success');
      addLog('WebSocket 연결 확인 중...', 'info');
      
      // WebSocket 연결 상태 확인
      setTimeout(() => {
        if (websocketService.isConnected()) {
          addLog('WebSocket 연결 성공', 'success');
        } else {
          addLog('WebSocket 연결 실패 또는 지연', 'error');
        }
      }, 2000);
      
    } catch (error) {
      currentError = error instanceof Error ? error.message : 'Script loading failed';
      addLog(`스크립트 로드 실패: ${currentError}`, 'error');
    } finally {
      isLoading = false;
    }
  }
  
  async function runAPITests() {
    const results: any[] = [];
    
    try {
      // 1. Scripts API 테스트
      console.log('Testing Scripts API...');
      const scriptsResult = await testScriptsAPI();
      results.push(scriptsResult);
      
      // 2. Audio API 테스트
      console.log('Testing Audio API...');
      const audioResult = await testAudioAPI();
      results.push(audioResult);
      
      // 3. Sync API 테스트
      console.log('Testing Sync API...');
      const syncResult = await testSyncAPI();
      results.push(syncResult);
      
      // 4. WebSocket 테스트
      console.log('Testing WebSocket...');
      const wsResult = await testWebSocket();
      results.push(wsResult);
      
    } catch (error) {
      results.push({
        name: 'API Tests',
        passed: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      });
    }
    
    testResults = results;
  }
  
  async function testScriptsAPI() {
    try {
      // 스크립트 목록 조회
      const scripts = await scriptsApi.getScripts({ limit: 5 });
      
      // 카테고리 조회
      const categories = await scriptsApi.getCategories();
      
      return {
        name: 'Scripts API',
        passed: scripts.length > 0 && categories.length > 0,
        details: {
          scriptsCount: scripts.length,
          categoriesCount: categories.length,
          firstScript: scripts[0]?.title || 'N/A'
        },
        timestamp: new Date().toISOString()
      };
      
    } catch (error) {
      return {
        name: 'Scripts API',
        passed: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      };
    }
  }
  
  async function testAudioAPI() {
    if (!testScriptId) {
      return {
        name: 'Audio API',
        passed: false,
        error: 'No test script ID',
        timestamp: new Date().toISOString()
      };
    }
    
    try {
      // 스트림 정보 조회
      const streamInfo = await audioApi.getStreamInfo(testScriptId);
      
      // 준비 상태 확인
      const prepareInfo = await audioApi.prepareAudio(testScriptId);
      
      return {
        name: 'Audio API',
        passed: !!streamInfo.stream_url,
        details: {
          streamUrl: streamInfo.stream_url ? 'Available' : 'Not available',
          duration: streamInfo.duration,
          format: streamInfo.format,
          prepareStatus: prepareInfo.status
        },
        timestamp: new Date().toISOString()
      };
      
    } catch (error) {
      return {
        name: 'Audio API',
        passed: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      };
    }
  }
  
  async function testSyncAPI() {
    if (!testScriptId) {
      return {
        name: 'Sync API',
        passed: false,
        error: 'No test script ID',
        timestamp: new Date().toISOString()
      };
    }
    
    try {
      // 매핑 조회
      const mappings = await syncApi.getScriptMappings(testScriptId);
      
      // 헬스 체크
      const health = await syncApi.getHealthStatus();
      
      return {
        name: 'Sync API',
        passed: mappings.length >= 0 && health.status === 'healthy',
        details: {
          mappingsCount: mappings.length,
          healthStatus: health.status,
          syncVersion: health.version
        },
        timestamp: new Date().toISOString()
      };
      
    } catch (error) {
      return {
        name: 'Sync API',
        passed: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      };
    }
  }
  
  async function testWebSocket() {
    try {
      const connectionInfo = websocketService.getConnectionInfo();
      const isConnected = websocketService.isConnected();
      
      return {
        name: 'WebSocket',
        passed: isConnected,
        details: {
          isConnected,
          connectionId: connectionInfo.connectionId,
          roomId: connectionInfo.roomId,
          reconnectAttempts: connectionInfo.reconnectAttempts
        },
        timestamp: new Date().toISOString()
      };
      
    } catch (error) {
      return {
        name: 'WebSocket',
        passed: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      };
    }
  }
  
  function clearResults() {
    testResults = [];
    currentError = null;
  }
  
  function toggleMockMode() {
    if (isMockMode) {
      disableMockMode();
      console.log('🔄 Mock API 비활성화');
    } else {
      enableMockMode();
      console.log('🎭 Mock API 활성화');
    }
    isMockMode = !isMockMode;
    mockModeChangeCount++;
    
    // 모드 변경 후 테스트 결과 초기화
    testResults = [];
    currentError = null;
  }
  
  async function runComprehensiveTest() {
    console.log('🚀 포괄적 통합 테스트 시작');
    isLoading = true;
    currentError = null;
    
    try {
      // 1. API 테스트
      await runAPITests();
      
      // 2. 스크립트 로드 테스트
      const scriptId = customScriptId || testScriptId;
      await playerIntegrationService.loadScript(scriptId);
      
      // 3. 성능 테스트 (응답 시간 측정)
      await runPerformanceTests();
      
      // 4. 에러 처리 테스트
      await runErrorHandlingTests();
      
      console.log('✅ 포괄적 통합 테스트 완료');
      
    } catch (error) {
      currentError = error instanceof Error ? error.message : 'Comprehensive test failed';
      console.error('❌ 포괄적 통합 테스트 실패:', error);
    } finally {
      isLoading = false;
    }
  }
  
  async function runPerformanceTests() {
    console.log('⚡ 성능 테스트 실행 중...');
    
    const performanceResults: any[] = [];
    
    // API 응답 시간 테스트
    const apiEndpoints = [
      { name: 'Scripts API', test: () => scriptsApi.getScripts({ limit: 1 }) },
      { name: 'Audio API', test: () => audioApi.getStreamInfo(testScriptId) },
      { name: 'Sync API', test: () => syncApi.getScriptMappings(testScriptId) }
    ];
    
    for (const endpoint of apiEndpoints) {
      const startTime = performance.now();
      try {
        await endpoint.test();
        const responseTime = performance.now() - startTime;
        
        performanceResults.push({
          name: `Performance: ${endpoint.name}`,
          passed: responseTime < 1000, // 1초 이내
          details: {
            responseTime: `${responseTime.toFixed(1)}ms`,
            threshold: '1000ms',
            status: responseTime < 300 ? 'Excellent' : responseTime < 1000 ? 'Good' : 'Slow'
          },
          timestamp: new Date().toISOString()
        });
        
      } catch (error) {
        performanceResults.push({
          name: `Performance: ${endpoint.name}`,
          passed: false,
          error: error instanceof Error ? error.message : 'Performance test failed',
          timestamp: new Date().toISOString()
        });
      }
    }
    
    testResults = [...testResults, ...performanceResults];
  }
  
  async function runErrorHandlingTests() {
    console.log('🚨 에러 처리 테스트 실행 중...');
    
    const errorTests: any[] = [];
    
    // 존재하지 않는 스크립트 요청
    try {
      await scriptsApi.getScript('non-existent-script-id');
      errorTests.push({
        name: 'Error Handling: Invalid Script',
        passed: false,
        error: 'Should have thrown error for invalid script',
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      errorTests.push({
        name: 'Error Handling: Invalid Script',
        passed: true,
        details: {
          errorType: error instanceof Error ? error.constructor.name : 'Unknown',
          errorMessage: error instanceof Error ? error.message : 'Unknown error'
        },
        timestamp: new Date().toISOString()
      });
    }
    
    testResults = [...testResults, ...errorTests];
  }
  
  function downloadIntegrationReport() {
    const report = {
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      testScriptId,
      mockMode: isMockMode,
      mockModeChanges: mockModeChangeCount,
      states: {
        integration: integrationState,
        websocket: wsState,
        audio: audioStoreState,
        script: scriptStoreState
      },
      testResults,
      performance: {
        ttfb: (performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming)?.responseStart || 0,
        domContentLoaded: (performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming)?.domContentLoadedEventEnd || 0
      }
    };
    
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `integration-test-report-${isMockMode ? 'mock' : 'real'}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
</script>

<svelte:head>
  <title>백엔드 통합 테스트 - Kiko</title>
  <meta name="description" content="플레이어 백엔드 통합 시스템 테스트 페이지" />
</svelte:head>

<div class="integration-test-page min-h-screen bg-base-100">
  <!-- 헤더 -->
  <header class="bg-primary text-primary-content p-4">
    <div class="container mx-auto">
      <h1 class="text-2xl font-bold">🔗 백엔드 통합 테스트</h1>
      <p class="text-primary-content/80 mt-2">
        플레이어 통합 서비스를 통한 완전한 API 연동 및 실시간 동기화 테스트
      </p>
    </div>
  </header>
  
  <!-- 컨트롤 패널 -->
  <div class="control-panel bg-base-200 p-4 border-b">
    <div class="container mx-auto">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <!-- 스크립트 로드 -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body">
            <h3 class="card-title text-sm">📄 스크립트 로드</h3>
            <div class="form-control">
              <label class="label">
                <span class="label-text">스크립트 ID</span>
              </label>
              <input 
                type="text" 
                class="input input-sm input-bordered" 
                bind:value={customScriptId}
                placeholder={testScriptId}
              />
            </div>
            <button 
              class="btn btn-primary btn-sm mt-2"
              class:loading={isLoading}
              disabled={!isInitialized || isLoading}
              on:click={loadTestScript}
            >
              {isLoading ? '로딩 중...' : '스크립트 로드'}
            </button>
          </div>
        </div>
        
        <!-- API 테스트 -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body">
            <h3 class="card-title text-sm">🧪 API 테스트</h3>
            
            <!-- Mock Mode Toggle -->
            <div class="form-control mb-2">
              <label class="label cursor-pointer">
                <span class="label-text text-xs">Mock API 모드</span>
                <input 
                  type="checkbox" 
                  class="toggle toggle-sm toggle-primary" 
                  bind:checked={isMockMode}
                  on:change={toggleMockMode}
                />
              </label>
            </div>
            
            <div class="flex flex-col gap-1">
              <button 
                class="btn btn-secondary btn-sm"
                disabled={!isInitialized}
                on:click={runAPITests}
              >
                기본 API 테스트
              </button>
              <button 
                class="btn btn-accent btn-sm"
                disabled={!isInitialized}
                class:loading={isLoading}
                on:click={runComprehensiveTest}
              >
                {isLoading ? '테스트 중...' : '포괄적 테스트'}
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
        
        <!-- 상태 정보 -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body">
            <h3 class="card-title text-sm">📊 상태 정보</h3>
            <div class="text-xs space-y-1">
              <div class="badge badge-sm {isInitialized ? 'badge-success' : 'badge-error'}">
                {isInitialized ? '초기화 완료' : '초기화 필요'}
              </div>
              <div class="badge badge-sm {integrationState?.syncStatus === 'connected' ? 'badge-success' : 'badge-error'}">
                {integrationState?.syncStatus || 'disconnected'}
              </div>
              <div class="badge badge-sm {audioStoreState?.isLoaded ? 'badge-success' : 'badge-warning'}">
                {audioStoreState?.isLoaded ? '오디오 로드됨' : '오디오 대기 중'}
              </div>
              <div class="badge badge-sm {isMockMode ? 'badge-info' : 'badge-accent'}">
                {isMockMode ? 'Mock API' : 'Real API'}
              </div>
            </div>
            <div class="flex flex-col gap-1 mt-2">
              <button 
                class="btn btn-accent btn-sm"
                on:click={downloadIntegrationReport}
              >
                📋 리포트 다운로드
              </button>
              <button 
                class="btn btn-ghost btn-sm"
                on:click={clearLogs}
              >
                🗑️ 로그 초기화
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <!-- 에러 표시 -->
  {#if currentError}
    <div class="alert alert-error m-4">
      <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
      <span>{currentError}</span>
    </div>
  {/if}
  
  <!-- 테스트 결과 -->
  {#if testResults.length > 0}
    <div class="test-results p-4">
      <div class="container mx-auto">
        <h2 class="text-lg font-semibold mb-4">🧪 API 테스트 결과</h2>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {#each testResults as result}
            <div class="card bg-base-100 shadow-sm border {result.passed ? 'border-success' : 'border-error'}">
              <div class="card-body p-4">
                <h3 class="card-title text-sm">
                  {result.passed ? '✅' : '❌'} {result.name}
                </h3>
                
                {#if result.details}
                  <div class="text-xs text-base-content/70 mt-2">
                    {#each Object.entries(result.details) as [key, value]}
                      <div><strong>{key}:</strong> {value}</div>
                    {/each}
                  </div>
                {/if}
                
                {#if result.error}
                  <div class="text-xs text-error mt-2">
                    <strong>Error:</strong> {result.error}
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
  
  <!-- 실시간 상태 모니터링 -->
  <div class="status-monitor p-4 bg-base-50">
    <div class="container mx-auto">
      <h2 class="text-lg font-semibold mb-4">📡 실시간 상태 모니터링</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- WebSocket 상태 -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body p-4">
            <h3 class="card-title text-sm">🔌 WebSocket</h3>
            <div class="text-xs space-y-1">
              <div>연결: {wsState.isConnected ? '✅' : '❌'}</div>
              <div>재연결 시도: {wsState.reconnectAttempts || 0}</div>
              <div>에러: {wsState.error || 'None'}</div>
            </div>
          </div>
        </div>
        
        <!-- 오디오 상태 -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body p-4">
            <h3 class="card-title text-sm">🎵 오디오</h3>
            <div class="text-xs space-y-1">
              <div>로드됨: {audioStoreState.isLoaded ? '✅' : '❌'}</div>
              <div>재생 중: {audioStoreState.isPlaying ? '✅' : '❌'}</div>
              <div>시간: {audioStoreState.currentTime?.toFixed(1) || 0}s</div>
              <div>속도: {audioStoreState.playbackRate || 1}x</div>
            </div>
          </div>
        </div>
        
        <!-- 스크립트 상태 -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body p-4">
            <h3 class="card-title text-sm">📝 스크립트</h3>
            <div class="text-xs space-y-1">
              <div>ID: {scriptStoreState?.id || 'None'}</div>
              <div>제목: {scriptStoreState?.title || 'None'}</div>
              <div>문장: {scriptStoreState?.sentences?.length || 0}개</div>
              <div>매핑: {scriptStoreState?.mappings?.length || 0}개</div>
            </div>
          </div>
        </div>
        
        <!-- 통합 상태 -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body p-4">
            <h3 class="card-title text-sm">🔗 통합</h3>
            <div class="text-xs space-y-1">
              <div>초기화: {integrationState?.isInitialized ? '✅' : '❌'}</div>
              <div>로딩: {integrationState?.isLoading ? '⏳' : '✅'}</div>
              <div>세션: {integrationState?.currentSessionId ? '✅' : '❌'}</div>
              <div>동기화: {integrationState?.syncStatus || 'N/A'}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <!-- 실시간 로그 -->
  {#if testLogs.length > 0}
    <div class="logs-section p-4 bg-base-300">
      <div class="container mx-auto">
        <h2 class="text-lg font-semibold mb-4">📋 실시간 테스트 로그</h2>
        
        <div class="bg-base-100 rounded-lg shadow-sm border max-h-64 overflow-y-auto">
          <div class="p-4">
            {#each testLogs as log}
              <div class="text-xs font-mono py-1 {
                log.includes('ERROR') ? 'text-error' : 
                log.includes('SUCCESS') ? 'text-success' : 
                'text-base-content/70'
              }">
                {log}
              </div>
            {/each}
          </div>
        </div>
      </div>
    </div>
  {/if}
  
  <!-- 메인 UI (스크립트가 로드되면 표시) -->
  {#if scriptStoreState?.id && integrationState?.isInitialized}
    <div class="main-ui p-4">
      <div class="container mx-auto">
        <h2 class="text-lg font-semibold mb-4">🎯 통합 플레이어</h2>
        
        <div class="bg-base-100 rounded-lg shadow-sm border">
          <ScriptAudioSyncUI 
            scriptId={scriptStoreState?.id || testScriptId}
            audioUrl={audioStoreState?.currentAudioUrl || ''}
            className="h-96"
          />
        </div>
      </div>
    </div>
  {:else}
    <div class="placeholder-ui p-4">
      <div class="container mx-auto text-center">
        <div class="hero min-h-64">
          <div class="hero-content text-center">
            <div class="max-w-md">
              <h1 class="text-2xl font-bold">🎭 통합 플레이어 대기 중</h1>
              <p class="py-6">
                위에서 스크립트를 로드하면 완전한 통합 플레이어가 나타납니다.
              </p>
              <p class="text-sm text-base-content/70">
                백엔드 API, WebSocket 연결, 실시간 동기화가 모두 포함됩니다.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  {/if}
</div> 