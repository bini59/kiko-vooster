/**
 * 오디오 관련 API 서비스
 *
 * 백엔드 /api/v1/audio 엔드포인트와 연동
 * 오디오 스트리밍, 재생 세션, 진행률 관리
 */

import { getApiClient, ApiError } from "./client.js";

// 백엔드 요청/응답 타입 정의
interface StreamRequest {
  quality?: "low" | "medium" | "high";
  format?: "hls" | "mp3";
}

interface StreamResponse {
  stream_url: string;
  duration: number;
  format: string;
  quality: string;
  expires_at: string;
  segment_duration?: number; // HLS인 경우
  bitrate?: number;
}

interface PrepareRequest {
  priority?: "low" | "normal" | "high";
}

interface PrepareResponse {
  status: "queued" | "processing" | "ready" | "failed";
  progress: number; // 0-100
  estimated_completion?: string; // ISO 문자열
  message?: string;
}

interface PlayRequest {
  script_id: string;
  position?: number; // 시작 위치 (초)
  sentence_id?: string; // 특정 문장에서 시작
}

interface PlayResponse {
  session_id: string;
  stream_url: string;
  duration: number;
  start_position: number;
  expires_at: string;
}

interface ProgressUpdate {
  session_id: string;
  position: number;
  sentence_id?: string;
  playback_rate?: number;
}

interface ProgressResponse {
  session_id: string;
  position: number;
  sentence_id?: string;
  last_updated: string;
  sync_status: "synced" | "pending" | "failed";
}

interface SeekRequest {
  session_id: string;
  position: number;
  sentence_id?: string;
}

interface SeekResponse {
  session_id: string;
  new_position: number;
  sentence_id?: string;
  status: "success" | "failed";
}

interface BookmarkRequest {
  script_id: string;
  position: number;
  note?: string;
}

interface BookmarkResponse {
  id: string;
  script_id: string;
  position: number;
  note?: string;
  created_at: string;
}

interface LoopRequest {
  session_id: string;
  start_time: number;
  end_time: number;
  max_repeats?: number;
}

interface LoopResponse {
  session_id: string;
  loop_id: string;
  start_time: number;
  end_time: number;
  max_repeats: number;
  current_repeat: number;
  status: "active" | "completed" | "cancelled";
}

interface AudioError {
  error_code: string;
  message: string;
  details?: any;
}

class AudioApiService {
  private client = getApiClient();

  /**
   * 오디오 스트림 URL 및 메타데이터 조회
   */
  async getStreamInfo(
    scriptId: string,
    options: StreamRequest = {}
  ): Promise<StreamResponse> {
    try {
      const queryParams = new URLSearchParams();

      if (options.quality) queryParams.append("quality", options.quality);
      if (options.format) queryParams.append("format", options.format);

      const queryString = queryParams.toString();
      const endpoint = `/audio/stream/${scriptId}${
        queryString ? `?${queryString}` : ""
      }`;

      const streamInfo: StreamResponse = await this.client.get(endpoint);

      return streamInfo;
    } catch (error) {
      console.error(`Failed to get stream info for script ${scriptId}:`, error);
      throw error;
    }
  }

  /**
   * 오디오 파일 사전 처리 및 캐싱 요청
   */
  async prepareAudio(
    scriptId: string,
    options: PrepareRequest = {}
  ): Promise<PrepareResponse> {
    try {
      const response: PrepareResponse = await this.client.post(
        `/audio/prepare/${scriptId}`,
        options
      );

      return response;
    } catch (error) {
      console.error(`Failed to prepare audio for script ${scriptId}:`, error);
      throw error;
    }
  }

  /**
   * 재생 세션 생성
   */
  async createPlaySession(playRequest: PlayRequest): Promise<PlayResponse> {
    try {
      const response: PlayResponse = await this.client.post(
        "/audio/play",
        playRequest
      );

      return response;
    } catch (error) {
      console.error("Failed to create play session:", error);
      throw error;
    }
  }

  /**
   * 재생 진행률 업데이트
   */
  async updateProgress(
    progressUpdate: ProgressUpdate
  ): Promise<ProgressResponse> {
    try {
      const response: ProgressResponse = await this.client.put(
        "/audio/progress",
        progressUpdate
      );

      return response;
    } catch (error) {
      console.error("Failed to update progress:", error);
      // 진행률 업데이트 실패는 사용자 경험에 큰 영향을 주지 않으므로 로그만 남기고 에러를 던지지 않음
      return {
        session_id: progressUpdate.session_id,
        position: progressUpdate.position,
        sentence_id: progressUpdate.sentence_id,
        last_updated: new Date().toISOString(),
        sync_status: "failed",
      };
    }
  }

  /**
   * 특정 위치로 탐색
   */
  async seekTo(seekRequest: SeekRequest): Promise<SeekResponse> {
    try {
      const response: SeekResponse = await this.client.post(
        "/audio/seek",
        seekRequest
      );

      return response;
    } catch (error) {
      console.error("Failed to seek:", error);
      throw error;
    }
  }

  /**
   * 재생 위치 북마크 생성
   */
  async createBookmark(
    bookmarkRequest: BookmarkRequest
  ): Promise<BookmarkResponse> {
    try {
      const response: BookmarkResponse = await this.client.post(
        "/audio/bookmark",
        bookmarkRequest
      );

      return response;
    } catch (error) {
      console.error("Failed to create bookmark:", error);
      throw error;
    }
  }

  /**
   * A-B 구간 반복 설정
   */
  async setLoop(loopRequest: LoopRequest): Promise<LoopResponse> {
    try {
      const response: LoopResponse = await this.client.post(
        "/audio/loop",
        loopRequest
      );

      return response;
    } catch (error) {
      console.error("Failed to set loop:", error);
      throw error;
    }
  }

  /**
   * A-B 구간 반복 취소
   */
  async cancelLoop(sessionId: string, loopId: string): Promise<void> {
    try {
      await this.client.delete(`/audio/loop/${loopId}?session_id=${sessionId}`);
    } catch (error) {
      console.error(`Failed to cancel loop ${loopId}:`, error);
      throw error;
    }
  }

  /**
   * 재생 세션 종료
   */
  async endSession(sessionId: string): Promise<void> {
    try {
      await this.client.delete(`/audio/session/${sessionId}`);
    } catch (error) {
      console.error(`Failed to end session ${sessionId}:`, error);
      // 세션 종료 실패는 크게 문제가 되지 않으므로 조용히 처리
    }
  }

  /**
   * 오디오 스트림 상태 확인
   */
  async getStreamStatus(
    scriptId: string
  ): Promise<{ status: string; health: string }> {
    try {
      const response = await this.client.get(`/audio/status/${scriptId}`);

      return response;
    } catch (error) {
      console.error(
        `Failed to get stream status for script ${scriptId}:`,
        error
      );
      throw error;
    }
  }

  /**
   * 사용자의 현재 활성 세션 조회
   */
  async getActiveSessions(): Promise<PlayResponse[]> {
    try {
      const sessions: PlayResponse[] = await this.client.get(
        "/audio/sessions/active"
      );

      return sessions;
    } catch (error) {
      console.error("Failed to get active sessions:", error);
      throw error;
    }
  }

  /**
   * 사용자의 북마크 목록 조회
   */
  async getBookmarks(scriptId?: string): Promise<BookmarkResponse[]> {
    try {
      const endpoint = scriptId
        ? `/audio/bookmarks?script_id=${scriptId}`
        : "/audio/bookmarks";

      const bookmarks: BookmarkResponse[] = await this.client.get(endpoint);

      return bookmarks;
    } catch (error) {
      console.error("Failed to get bookmarks:", error);
      throw error;
    }
  }

  /**
   * 북마크 삭제
   */
  async deleteBookmark(bookmarkId: string): Promise<void> {
    try {
      await this.client.delete(`/audio/bookmark/${bookmarkId}`);
    } catch (error) {
      console.error(`Failed to delete bookmark ${bookmarkId}:`, error);
      throw error;
    }
  }

  /**
   * 오디오 캐시 무효화 (관리자 기능)
   */
  async invalidateCache(scriptId: string): Promise<void> {
    try {
      await this.client.post(`/audio/cache/invalidate/${scriptId}`);
    } catch (error) {
      console.error(
        `Failed to invalidate cache for script ${scriptId}:`,
        error
      );
      throw error;
    }
  }
}

// 싱글톤 인스턴스
let audioApiInstance: AudioApiService | null = null;

/**
 * 오디오 API 서비스 인스턴스 가져오기
 */
export function getAudioApi(): AudioApiService {
  if (!audioApiInstance) {
    audioApiInstance = new AudioApiService();
  }
  return audioApiInstance;
}

/**
 * 오디오 API 서비스 인스턴스 설정 (테스트용)
 */
export function setAudioApi(api: AudioApiService): void {
  audioApiInstance = api;
}

// 기본 export
export const audioApi = getAudioApi();
