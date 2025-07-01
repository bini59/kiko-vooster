/**
 * Mock API 서버
 *
 * 통합 테스트를 위한 가짜 백엔드 API 시뮬레이션
 * 실제 백엔드 API의 응답 형식과 동일하게 구현
 */

import type { Script, Sentence, SentenceMapping } from "$lib/types/script.js";

// Mock 데이터
const mockScript: Script = {
  id: "demo-news-001",
  title: "일본어 뉴스 - 테크 동향",
  description:
    "최신 기술 동향에 대한 일본어 뉴스입니다. AI와 로봇 기술의 발전에 대해 다룹니다.",
  language: "ja",
  sentences: [
    {
      id: "sent-001",
      content: "人工知能技術の発展により、私たちの生活は大きく変わっています。",
      orderIndex: 0,
      metadata: {
        reading:
          "じんこうちのうぎじゅつのはってんにより、わたしたちのせいかつはおおきくかわっています。",
        translation:
          "인공지능 기술의 발전으로 우리의 생활이 크게 변하고 있습니다.",
        startTime: 2.5,
        endTime: 8.2,
        difficultyLevel: "intermediate",
      },
    },
    {
      id: "sent-002",
      content: "ロボットは工場だけでなく、家庭でも活用されるようになりました。",
      orderIndex: 1,
      metadata: {
        reading:
          "ロボットはこうじょうだけでなく、かていでもかつようされるようになりました。",
        translation: "로봇은 공장뿐만 아니라 가정에서도 활용되게 되었습니다.",
        startTime: 8.5,
        endTime: 14.1,
        difficultyLevel: "intermediate",
      },
    },
    {
      id: "sent-003",
      content: "今後もこの技術革新は続き、社会に大きな影響を与えるでしょう。",
      orderIndex: 2,
      metadata: {
        reading:
          "こんごもこのぎじゅつかくしんはつづき、しゃかいにおおきなえいきょうをあたえるでしょう。",
        translation:
          "앞으로도 이 기술 혁신은 계속되어 사회에 큰 영향을 줄 것입니다.",
        startTime: 14.5,
        endTime: 20.8,
        difficultyLevel: "advanced",
      },
    },
  ],
  mappings: [
    {
      id: "map-001",
      sentenceId: "sent-001",
      startTime: 2.5,
      endTime: 8.2,
      mappingType: "ai_generated",
      confidence: 0.92,
      isActive: true,
      createdAt: "2024-12-24T10:00:00Z",
      updatedAt: "2024-12-24T10:00:00Z",
    },
    {
      id: "map-002",
      sentenceId: "sent-002",
      startTime: 8.5,
      endTime: 14.1,
      mappingType: "ai_generated",
      confidence: 0.88,
      isActive: true,
      createdAt: "2024-12-24T10:00:00Z",
      updatedAt: "2024-12-24T10:00:00Z",
    },
    {
      id: "map-003",
      sentenceId: "sent-003",
      startTime: 14.5,
      endTime: 20.8,
      mappingType: "ai_generated",
      confidence: 0.85,
      isActive: true,
      createdAt: "2024-12-24T10:00:00Z",
      updatedAt: "2024-12-24T10:00:00Z",
    },
  ],
  metadata: {
    audioUrl:
      "https://file-examples.com/storage/fe86b2ba9ae7b0cd6e6bb7f/2017/11/file_example_MP3_700KB.mp3",
    thumbnailUrl:
      "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=400&h=300&fit=crop",
    duration: 22.0,
    difficultyLevel: "intermediate",
    category: "news",
  },
  createdAt: "2024-12-24T10:00:00Z",
  updatedAt: "2024-12-24T10:00:00Z",
};

const mockScriptList: Script[] = [
  mockScript,
  {
    ...mockScript,
    id: "demo-anime-001",
    title: "アニメ会話 - 日常シーン",
    description: "日常生活での자연스러운 일본어 회화입니다.",
    metadata: {
      ...mockScript.metadata,
      category: "anime",
      difficultyLevel: "beginner",
    },
  },
];

interface MockResponse<T = any> {
  data?: T;
  error?: string;
  status: number;
}

// API 응답 지연 시뮬레이션
function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// 랜덤 에러 시뮬레이션 (10% 확률)
function shouldSimulateError(): boolean {
  return Math.random() < 0.1;
}

export class MockApiServer {
  private baseDelay = 200; // 기본 지연 시간 (ms)
  private errorRate = 0.1; // 에러 발생률 (10%)

  constructor(options: { baseDelay?: number; errorRate?: number } = {}) {
    this.baseDelay = options.baseDelay ?? 200;
    this.errorRate = options.errorRate ?? 0.1;
  }

  /**
   * API 응답 시뮬레이션
   */
  private async simulateResponse<T>(
    data: T,
    options: { delay?: number; errorMessage?: string } = {}
  ): Promise<MockResponse<T>> {
    const responseDelay = options.delay ?? this.baseDelay + Math.random() * 300;
    await delay(responseDelay);

    // 에러 시뮬레이션
    if (shouldSimulateError() && options.errorMessage) {
      return {
        error: options.errorMessage,
        status: 500,
      };
    }

    return {
      data,
      status: 200,
    };
  }

  /**
   * Scripts API Mock
   */
  async getScripts(params: any = {}): Promise<MockResponse<Script[]>> {
    console.log("Mock API: getScripts called with params:", params);

    return this.simulateResponse(mockScriptList, {
      errorMessage: "Failed to fetch scripts",
    });
  }

  async getScript(scriptId: string): Promise<MockResponse<Script>> {
    console.log("Mock API: getScript called with ID:", scriptId);

    const script = mockScriptList.find((s) => s.id === scriptId);

    if (!script) {
      return {
        error: "Script not found",
        status: 404,
      };
    }

    return this.simulateResponse(script, {
      errorMessage: "Failed to fetch script details",
    });
  }

  async getCategories(): Promise<MockResponse<string[]>> {
    console.log("Mock API: getCategories called");

    return this.simulateResponse(["news", "anime", "podcast", "drama"], {
      errorMessage: "Failed to fetch categories",
    });
  }

  async updatePlaybackProgress(
    scriptId: string,
    progress: any
  ): Promise<MockResponse<void>> {
    console.log("Mock API: updatePlaybackProgress called", {
      scriptId,
      progress,
    });

    return this.simulateResponse(undefined, {
      delay: 100,
      errorMessage: "Failed to update progress",
    });
  }

  /**
   * Audio API Mock
   */
  async getStreamInfo(
    scriptId: string,
    options: any = {}
  ): Promise<MockResponse<any>> {
    console.log("Mock API: getStreamInfo called", { scriptId, options });

    const streamInfo = {
      stream_url:
        "https://file-examples.com/storage/fe86b2ba9ae7b0cd6e6bb7f/2017/11/file_example_MP3_700KB.mp3",
      duration: 22.0,
      format: "mp3",
      quality: "medium",
      expires_at: new Date(Date.now() + 3600000).toISOString(), // 1시간 후
    };

    return this.simulateResponse(streamInfo, {
      errorMessage: "Failed to get stream info",
    });
  }

  async createPlaySession(request: any): Promise<MockResponse<any>> {
    console.log("Mock API: createPlaySession called", request);

    const session = {
      session_id: `session-${Date.now()}`,
      stream_url:
        "https://file-examples.com/storage/fe86b2ba9ae7b0cd6e6bb7f/2017/11/file_example_MP3_700KB.mp3",
      duration: 22.0,
      start_position: request.position || 0,
      expires_at: new Date(Date.now() + 3600000).toISOString(),
    };

    return this.simulateResponse(session, {
      errorMessage: "Failed to create play session",
    });
  }

  async updateProgress(update: any): Promise<MockResponse<any>> {
    console.log("Mock API: updateProgress called", update);

    const response = {
      session_id: update.session_id,
      position: update.position,
      sentence_id: update.sentence_id,
      last_updated: new Date().toISOString(),
      sync_status: "synced",
    };

    return this.simulateResponse(response, {
      delay: 50,
      errorMessage: "Failed to update progress",
    });
  }

  /**
   * Sync API Mock
   */
  async getScriptMappings(
    scriptId: string
  ): Promise<MockResponse<SentenceMapping[]>> {
    console.log("Mock API: getScriptMappings called with ID:", scriptId);

    const script = mockScriptList.find((s) => s.id === scriptId);
    const mappings = script?.mappings || [];

    return this.simulateResponse(mappings, {
      errorMessage: "Failed to fetch mappings",
    });
  }

  async updateSentenceMapping(
    sentenceId: string,
    update: any
  ): Promise<MockResponse<SentenceMapping>> {
    console.log("Mock API: updateSentenceMapping called", {
      sentenceId,
      update,
    });

    const existingMapping = mockScript.mappings.find(
      (m) => m.sentenceId === sentenceId
    );

    if (!existingMapping) {
      return {
        error: "Mapping not found",
        status: 404,
      };
    }

    const updatedMapping: SentenceMapping = {
      ...existingMapping,
      startTime: update.startTime ?? existingMapping.startTime,
      endTime: update.endTime ?? existingMapping.endTime,
      mappingType: update.mappingType ?? existingMapping.mappingType,
      updatedAt: new Date().toISOString(),
    };

    return this.simulateResponse(updatedMapping, {
      errorMessage: "Failed to update mapping",
    });
  }

  async getHealthStatus(): Promise<MockResponse<any>> {
    console.log("Mock API: getHealthStatus called");

    const health = {
      status: "healthy",
      version: "1.0.0-mock",
      uptime: Math.floor(Math.random() * 10000),
    };

    return this.simulateResponse(health, {
      delay: 50,
    });
  }

  /**
   * WebSocket Mock (간단한 로그만)
   */
  simulateWebSocketConnection(scriptId: string): void {
    console.log("Mock WebSocket: Connecting to script", scriptId);

    // 가짜 연결 성공 이벤트
    setTimeout(() => {
      console.log("Mock WebSocket: Connected successfully");

      // 주기적으로 가짜 이벤트 발생
      setInterval(() => {
        console.log("Mock WebSocket: Position sync event");
      }, 5000);
    }, 1000);
  }
}

// 글로벌 Mock API 인스턴스
export const mockApiServer = new MockApiServer({
  baseDelay: 150,
  errorRate: 0.05, // 5% 에러율로 낮춤
});

// Mock API를 실제 API로 교체하는 함수들
export function enableMockMode() {
  console.log("🎭 Mock API 모드 활성화");

  // scriptsApi 교체
  const mockScriptsApi = {
    getScripts: async (params: any) => {
      const response = await mockApiServer.getScripts(params);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    getScript: async (scriptId: string) => {
      const response = await mockApiServer.getScript(scriptId);
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    getCategories: async () => {
      const response = await mockApiServer.getCategories();
      if (response.error) throw new Error(response.error);
      return response.data!;
    },
    updatePlaybackProgress: async (scriptId: string, progress: any) => {
      const response = await mockApiServer.updatePlaybackProgress(
        scriptId,
        progress
      );
      if (response.error) throw new Error(response.error);
    },
    getPlaybackProgress: async (scriptId: string) => {
      // 가짜 진행률 반환
      return {
        script_id: scriptId,
        current_time: Math.random() * 10,
        completed_sentences: [],
        last_played: new Date().toISOString(),
      };
    },
  };

  // 전역 API 객체에 Mock 설정
  if (typeof window !== "undefined") {
    (window as any).__MOCK_APIS__ = {
      scripts: mockScriptsApi,
      audio: mockApiServer,
      sync: mockApiServer,
    };
  }
}

export function disableMockMode() {
  console.log("🔄 Mock API 모드 비활성화");

  if (typeof window !== "undefined") {
    delete (window as any).__MOCK_APIS__;
  }
}
