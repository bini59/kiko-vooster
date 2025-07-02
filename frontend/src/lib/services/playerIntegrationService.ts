/**
 * 플레이어 통합 서비스
 *
 * 모든 API 서비스와 스토어를 연결하여 완전한 통합 시스템 구축
 * 오디오 재생, 스크립트 동기화, 실시간 상태 동기화를 담당
 */

import { get } from "svelte/store";
import { browser } from "$app/environment";

// API Services
import { scriptsApi } from "$lib/api/scripts.js";
import { audioApi } from "$lib/api/audio.js";
import { syncApi } from "$lib/api/sync.js";
import { websocketService } from "./websocketService.js";
import { audioService } from "./audioService.js";
import { logger, logError } from "$lib/utils/logger";

// Stores
import {
  audioState,
  audioActions,
  abRepeatState,
} from "$lib/stores/audioStore.js";
import {
  currentScript,
  scriptActions,
  highlightState,
} from "$lib/stores/scriptStore.js";

// Types
import type { Script, SentenceMapping } from "$lib/types/script.js";

interface PlaybackSession {
  sessionId: string;
  scriptId: string;
  startPosition: number;
  streamUrl: string;
  expiresAt: string;
}

interface IntegrationState {
  isInitialized: boolean;
  currentSessionId: string | null;
  isLoading: boolean;
  lastError: string | null;
  syncStatus: "disconnected" | "connecting" | "connected" | "error";
}

class PlayerIntegrationService {
  private integrationState: IntegrationState = {
    isInitialized: false,
    currentSessionId: null,
    isLoading: false,
    lastError: null,
    syncStatus: "disconnected",
  };

  private currentSession: PlaybackSession | null = null;
  private progressUpdateInterval: number | null = null;
  private progressUpdateFrequency = 2000; // 2초마다 진행률 업데이트

  /**
   * 서비스 초기화
   */
  async initialize(): Promise<void> {
    if (this.integrationState.isInitialized) {
      return;
    }

    try {
      this.integrationState.isLoading = true;

      // WebSocket 이벤트 리스너 등록
      this.setupWebSocketListeners();

      // 오디오 서비스와 스토어 연동
      this.setupAudioServiceIntegration();

      this.integrationState.isInitialized = true;
      this.integrationState.isLoading = false;

      logger.info("Player integration service initialized");
    } catch (error) {
      this.integrationState.lastError =
        error instanceof Error ? error.message : "Initialization failed";
      this.integrationState.isLoading = false;
      logError(error, "Failed to initialize player integration service");
      throw error;
    }
  }

  /**
   * 스크립트 로드 및 재생 준비
   */
  async loadScript(scriptId: string, authToken?: string): Promise<void> {
    try {
      this.integrationState.isLoading = true;
      this.integrationState.lastError = null;

      // 1. 스크립트 데이터 로드
      console.log("Loading script data...");
      const script = await scriptsApi.getScript(scriptId);

      // 2. 스크립트 매핑 로드
      console.log("Loading script mappings...");
      const mappings = await syncApi.getScriptMappings(scriptId);

      // 3. 스크립트 스토어 업데이트
      const scriptWithMappings: Script = {
        ...script,
        mappings,
      };
      scriptActions.setCurrentScript(scriptWithMappings);

      // 4. 오디오 스트림 정보 가져오기
      console.log("Getting audio stream info...");
      const streamInfo = await audioApi.getStreamInfo(scriptId, {
        quality: "medium",
        format: "hls",
      });

      // 5. 재생 세션 생성
      console.log("Creating playback session...");
      const playSession = await audioApi.createPlaySession({
        script_id: scriptId,
        position: 0,
      });

      this.currentSession = {
        sessionId: playSession.session_id,
        scriptId: scriptId,
        startPosition: playSession.start_position,
        streamUrl: playSession.stream_url,
        expiresAt: playSession.expires_at,
      };

      this.integrationState.currentSessionId = playSession.session_id;

      // 6. 오디오 서비스에 스트림 로드
      console.log("Loading audio stream...");
      await audioService.loadAudio(playSession.stream_url);

      // 7. WebSocket 연결
      console.log("Connecting to sync WebSocket...");
      this.integrationState.syncStatus = "connecting";
      await websocketService.connect(scriptId, authToken);

      // 8. 저장된 진행률 복원
      await this.restorePlaybackProgress(scriptId);

      // 9. 진행률 업데이트 시작
      this.startProgressTracking();

      this.integrationState.isLoading = false;
      console.log("Script loaded successfully:", scriptId);
    } catch (error) {
      this.integrationState.lastError =
        error instanceof Error ? error.message : "Failed to load script";
      this.integrationState.isLoading = false;
      this.integrationState.syncStatus = "error";
      console.error("Failed to load script:", error);
      throw error;
    }
  }

  /**
   * 저장된 재생 진행률 복원
   */
  private async restorePlaybackProgress(scriptId: string): Promise<void> {
    try {
      const progress = await scriptsApi.getPlaybackProgress(scriptId);

      if (progress && progress.current_time > 0) {
        // 진행률이 있으면 해당 위치로 이동
        await audioService.seekTo(progress.current_time);

        // 완료된 문장들 하이라이트 업데이트
        if (progress.completed_sentences.length > 0) {
          scriptActions.setCompletedSentences(progress.completed_sentences);
        }

        console.log(`Restored playback progress: ${progress.current_time}s`);
      }
    } catch (error) {
      console.warn("Failed to restore playback progress:", error);
      // 진행률 복원 실패는 치명적이지 않으므로 계속 진행
    }
  }

  /**
   * WebSocket 이벤트 리스너 설정
   */
  private setupWebSocketListeners(): void {
    // 연결 성공
    websocketService.on("connection_ack", (data) => {
      this.integrationState.syncStatus = "connected";
      console.log("WebSocket sync connected:", data.connection_id);
    });

    // 위치 동기화
    websocketService.on("position_sync", (data) => {
      // 다른 참가자의 위치 업데이트 (현재는 로그만)
      console.debug("Position sync from other participant:", data);
    });

    // 매핑 업데이트
    websocketService.on("mapping_update", async (data) => {
      console.log("Mapping updated by other participant:", data);

      // 매핑 변경사항 반영
      try {
        const updatedMapping = await syncApi.getSentenceMapping(
          data.sentence_id
        );
        if (updatedMapping) {
          scriptActions.updateMapping(updatedMapping);
        }
      } catch (error) {
        console.error("Failed to update mapping:", error);
      }
    });

    // 참가자 입장/퇴장
    websocketService.on("participant_join", (data) => {
      console.log("Participant joined:", data.connection_id);
    });

    websocketService.on("participant_leave", (data) => {
      console.log("Participant left:", data.connection_id);
    });

    // 에러 처리
    websocketService.on("error", (data) => {
      this.integrationState.syncStatus = "error";
      this.integrationState.lastError = data.message;
      console.error("WebSocket error:", data);
    });
  }

  /**
   * 오디오 서비스와 스토어 연동 설정
   */
  private setupAudioServiceIntegration(): void {
    // 오디오 상태 변경 시 WebSocket으로 동기화
    audioState.subscribe((state) => {
      if (websocketService.isConnected() && this.currentSession) {
        // 위치와 재생 상태 동기화
        websocketService.sendPositionUpdate(
          state.currentTime,
          state.isPlaying,
          get(highlightState).currentSentenceId
        );
      }
    });

    // AB 반복 상태 변경 모니터링
    abRepeatState.subscribe((state) => {
      if (state.isActive && state.pointA !== null && state.pointB !== null) {
        console.log("AB repeat activated:", state.pointA, "to", state.pointB);
      }
    });
  }

  /**
   * 진행률 추적 시작
   */
  private startProgressTracking(): void {
    this.stopProgressTracking();

    this.progressUpdateInterval = window.setInterval(() => {
      this.updatePlaybackProgress();
    }, this.progressUpdateFrequency);
  }

  /**
   * 진행률 추적 중지
   */
  private stopProgressTracking(): void {
    if (this.progressUpdateInterval) {
      clearInterval(this.progressUpdateInterval);
      this.progressUpdateInterval = null;
    }
  }

  /**
   * 재생 진행률 업데이트
   */
  private async updatePlaybackProgress(): Promise<void> {
    if (!this.currentSession) return;

    try {
      const currentState = get(audioState);
      const scriptState = get(currentScript);
      const highlightSt = get(highlightState);

      // 완료된 문장 ID 목록 생성
      const completedSentences =
        scriptState?.sentences
          .filter((s) => s.orderIndex < (highlightSt.currentSentenceIndex || 0))
          .map((s) => s.id) || [];

      // 진행률 업데이트 API 호출
      await scriptsApi.updatePlaybackProgress(this.currentSession.scriptId, {
        current_time: currentState.currentTime,
        completed_sentences: completedSentences,
      });

      // 오디오 API에도 진행률 업데이트
      await audioApi.updateProgress({
        session_id: this.currentSession.sessionId,
        position: currentState.currentTime,
        sentence_id: highlightSt.currentSentenceId,
        playback_rate: currentState.playbackRate,
      });
    } catch (error) {
      console.warn("Failed to update playback progress:", error);
      // 진행률 업데이트 실패는 사용자 경험에 큰 영향을 주지 않으므로 조용히 처리
    }
  }

  /**
   * 매핑 편집 후 동기화
   */
  async updateMapping(
    sentenceId: string,
    startTime: number,
    endTime: number,
    editReason?: string
  ): Promise<void> {
    try {
      // API를 통해 매핑 업데이트
      const updatedMapping = await syncApi.updateSentenceMapping(sentenceId, {
        startTime,
        endTime,
        mappingType: "manual",
        editReason,
      });

      // 로컬 스토어 업데이트
      scriptActions.updateMapping(updatedMapping);

      // WebSocket을 통해 다른 참가자들에게 알림
      websocketService.sendMappingEdit(
        sentenceId,
        startTime,
        endTime,
        "manual"
      );

      console.log("Mapping updated and synchronized:", sentenceId);
    } catch (error) {
      console.error("Failed to update mapping:", error);
      throw error;
    }
  }

  /**
   * 북마크 생성
   */
  async createBookmark(position?: number, note?: string): Promise<void> {
    if (!this.currentSession) {
      throw new Error("No active session");
    }

    try {
      const currentState = get(audioState);
      const bookmarkPosition = position ?? currentState.currentTime;

      await audioApi.createBookmark({
        script_id: this.currentSession.scriptId,
        position: bookmarkPosition,
        note,
      });

      console.log("Bookmark created at:", bookmarkPosition);
    } catch (error) {
      console.error("Failed to create bookmark:", error);
      throw error;
    }
  }

  /**
   * 세션 정리 및 종료
   */
  async cleanup(): Promise<void> {
    try {
      // 진행률 추적 중지
      this.stopProgressTracking();

      // 마지막 진행률 업데이트
      if (this.currentSession) {
        await this.updatePlaybackProgress();
      }

      // WebSocket 연결 해제
      websocketService.disconnect();
      this.integrationState.syncStatus = "disconnected";

      // 오디오 세션 종료
      if (this.currentSession) {
        await audioApi.endSession(this.currentSession.sessionId);
      }

      // 오디오 서비스 정리
      audioService.cleanup();

      // 상태 초기화
      this.currentSession = null;
      this.integrationState.currentSessionId = null;
      this.integrationState.lastError = null;

      console.log("Player integration service cleaned up");
    } catch (error) {
      console.error("Failed to cleanup integration service:", error);
      // 정리 실패는 치명적이지 않으므로 throw하지 않음
    }
  }

  /**
   * 현재 상태 조회
   */
  getState(): IntegrationState & { session: PlaybackSession | null } {
    return {
      ...this.integrationState,
      session: this.currentSession,
    };
  }

  /**
   * 서비스 상태 확인
   */
  isReady(): boolean {
    return (
      this.integrationState.isInitialized &&
      !this.integrationState.isLoading &&
      this.currentSession !== null
    );
  }
}

// 싱글톤 인스턴스
let playerIntegrationInstance: PlayerIntegrationService | null = null;

/**
 * 플레이어 통합 서비스 인스턴스 가져오기
 */
export function getPlayerIntegrationService(): PlayerIntegrationService {
  if (!playerIntegrationInstance) {
    playerIntegrationInstance = new PlayerIntegrationService();
  }
  return playerIntegrationInstance;
}

/**
 * 플레이어 통합 서비스 인스턴스 설정 (테스트용)
 */
export function setPlayerIntegrationService(
  service: PlayerIntegrationService
): void {
  playerIntegrationInstance = service;
}

// 기본 export
export const playerIntegrationService = getPlayerIntegrationService();
