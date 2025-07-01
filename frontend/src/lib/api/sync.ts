/**
 * 스크립트-오디오 싱크 관련 API 서비스
 *
 * 백엔드 /api/v1/sync 엔드포인트와 연동
 * 문장 매핑, 편집 내역, 동기화 세션 관리
 */

import { getApiClient, ApiError } from "./client.js";
import type { SentenceMapping } from "$lib/types/script.js";

// 백엔드 요청/응답 타입 정의
interface SentenceMappingCreate {
  sentence_id: string;
  start_time: number;
  end_time: number;
  mapping_type: "manual" | "auto" | "ai_generated";
  metadata?: Record<string, any>;
}

interface SentenceMappingUpdate {
  start_time?: number;
  end_time?: number;
  mapping_type?: "manual" | "auto" | "ai_generated";
  edit_reason?: string;
  metadata?: Record<string, any>;
}

interface BackendSentenceMapping {
  id: string;
  sentence_id: string;
  start_time: number;
  end_time: number;
  mapping_type: string;
  confidence: number;
  is_active: boolean;
  user_id?: string;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

interface MappingEditResponse {
  id: string;
  sentence_id: string;
  old_start_time?: number;
  old_end_time?: number;
  new_start_time: number;
  new_end_time: number;
  edit_reason?: string;
  user_id: string;
  created_at: string;
}

interface SyncSessionCreate {
  script_id: string;
  initial_position?: number;
  session_type?: "solo" | "collaborative";
}

interface SyncSessionResponse {
  session_id: string;
  script_id: string;
  current_position: number;
  is_active: boolean;
  participant_count: number;
  created_at: string;
}

interface SyncPositionUpdate {
  session_id: string;
  position: number;
  is_playing: boolean;
  sentence_id?: string;
}

interface RoomParticipant {
  connection_id: string;
  user_id?: string;
  current_position: number;
  is_playing: boolean;
  joined_at: string;
}

interface AutoAlignRequest {
  script_id: string;
  audio_url?: string;
  alignment_method?: "whisper" | "forced_alignment" | "hybrid";
  confidence_threshold?: number;
}

interface AutoAlignResponse {
  job_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  progress: number; // 0-100
  estimated_completion?: string;
  results?: BackendSentenceMapping[];
  error_message?: string;
}

interface SyncOperationResponse {
  success: boolean;
  message: string;
  data?: any;
}

// 타입 변환 함수
function convertBackendMappingToFrontend(
  backendMapping: BackendSentenceMapping
): SentenceMapping {
  return {
    id: backendMapping.id,
    sentenceId: backendMapping.sentence_id,
    startTime: backendMapping.start_time,
    endTime: backendMapping.end_time,
    mappingType: backendMapping.mapping_type as
      | "manual"
      | "auto"
      | "ai_generated",
    confidence: backendMapping.confidence,
    isActive: backendMapping.is_active,
    createdAt: backendMapping.created_at,
    updatedAt: backendMapping.updated_at,
  };
}

function convertFrontendMappingToBackend(
  sentenceId: string,
  startTime: number,
  endTime: number,
  mappingType: "manual" | "auto" | "ai_generated" = "manual",
  metadata?: Record<string, any>
): SentenceMappingCreate {
  return {
    sentence_id: sentenceId,
    start_time: startTime,
    end_time: endTime,
    mapping_type: mappingType,
    metadata,
  };
}

class SyncApiService {
  private client = getApiClient();

  /**
   * 새 문장 매핑 생성
   */
  async createSentenceMapping(
    sentenceId: string,
    startTime: number,
    endTime: number,
    mappingType: "manual" | "auto" | "ai_generated" = "manual",
    metadata?: Record<string, any>
  ): Promise<SentenceMapping> {
    try {
      const mappingData = convertFrontendMappingToBackend(
        sentenceId,
        startTime,
        endTime,
        mappingType,
        metadata
      );

      const backendMapping: BackendSentenceMapping = await this.client.post(
        "/sync/mappings",
        mappingData
      );

      return convertBackendMappingToFrontend(backendMapping);
    } catch (error) {
      console.error(
        `Failed to create mapping for sentence ${sentenceId}:`,
        error
      );
      throw error;
    }
  }

  /**
   * 문장 매핑 조회
   */
  async getSentenceMapping(
    sentenceId: string
  ): Promise<SentenceMapping | null> {
    try {
      const backendMapping: BackendSentenceMapping = await this.client.get(
        `/sync/mappings/sentence/${sentenceId}`
      );

      if (!backendMapping) {
        return null;
      }

      return convertBackendMappingToFrontend(backendMapping);
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        return null;
      }

      console.error(`Failed to get mapping for sentence ${sentenceId}:`, error);
      throw error;
    }
  }

  /**
   * 문장 매핑 수정
   */
  async updateSentenceMapping(
    sentenceId: string,
    updates: Partial<{
      startTime: number;
      endTime: number;
      mappingType: "manual" | "auto" | "ai_generated";
      editReason: string;
      metadata: Record<string, any>;
    }>
  ): Promise<SentenceMapping> {
    try {
      const updateData: SentenceMappingUpdate = {};

      if (updates.startTime !== undefined)
        updateData.start_time = updates.startTime;
      if (updates.endTime !== undefined) updateData.end_time = updates.endTime;
      if (updates.mappingType !== undefined)
        updateData.mapping_type = updates.mappingType;
      if (updates.editReason !== undefined)
        updateData.edit_reason = updates.editReason;
      if (updates.metadata !== undefined)
        updateData.metadata = updates.metadata;

      const backendMapping: BackendSentenceMapping = await this.client.put(
        `/sync/mappings/sentence/${sentenceId}`,
        updateData
      );

      return convertBackendMappingToFrontend(backendMapping);
    } catch (error) {
      console.error(
        `Failed to update mapping for sentence ${sentenceId}:`,
        error
      );
      throw error;
    }
  }

  /**
   * 문장 매핑 삭제
   */
  async deleteSentenceMapping(sentenceId: string): Promise<boolean> {
    try {
      const response: SyncOperationResponse = await this.client.delete(
        `/sync/mappings/sentence/${sentenceId}`
      );

      return response.success;
    } catch (error) {
      console.error(
        `Failed to delete mapping for sentence ${sentenceId}:`,
        error
      );
      throw error;
    }
  }

  /**
   * 스크립트의 모든 매핑 조회
   */
  async getScriptMappings(
    scriptId: string,
    includeInactive = false
  ): Promise<SentenceMapping[]> {
    try {
      const queryParams = new URLSearchParams();
      if (includeInactive) queryParams.append("include_inactive", "true");

      const endpoint = `/sync/mappings/script/${scriptId}${
        queryParams.toString() ? `?${queryParams.toString()}` : ""
      }`;

      const backendMappings: BackendSentenceMapping[] = await this.client.get(
        endpoint
      );

      return backendMappings.map(convertBackendMappingToFrontend);
    } catch (error) {
      console.error(`Failed to get mappings for script ${scriptId}:`, error);
      throw error;
    }
  }

  /**
   * 문장 매핑 편집 내역 조회
   */
  async getMappingEditHistory(
    sentenceId: string,
    limit = 50
  ): Promise<MappingEditResponse[]> {
    try {
      const endpoint = `/sync/mappings/sentence/${sentenceId}/history?limit=${limit}`;

      const editHistory: MappingEditResponse[] = await this.client.get(
        endpoint
      );

      return editHistory;
    } catch (error) {
      console.error(
        `Failed to get edit history for sentence ${sentenceId}:`,
        error
      );
      throw error;
    }
  }

  /**
   * 동기화 세션 생성
   */
  async createSyncSession(
    scriptId: string,
    initialPosition = 0,
    sessionType: "solo" | "collaborative" = "solo"
  ): Promise<SyncSessionResponse> {
    try {
      const sessionData: SyncSessionCreate = {
        script_id: scriptId,
        initial_position: initialPosition,
        session_type: sessionType,
      };

      const session: SyncSessionResponse = await this.client.post(
        "/sync/sessions",
        sessionData
      );

      return session;
    } catch (error) {
      console.error(
        `Failed to create sync session for script ${scriptId}:`,
        error
      );
      throw error;
    }
  }

  /**
   * 동기화 위치 업데이트
   */
  async updateSyncPosition(
    positionUpdate: SyncPositionUpdate
  ): Promise<boolean> {
    try {
      const response: SyncOperationResponse = await this.client.put(
        `/sync/sessions/${positionUpdate.session_id}/position`,
        positionUpdate
      );

      return response.success;
    } catch (error) {
      console.error("Failed to update sync position:", error);
      // 위치 업데이트 실패는 실시간 동기화에 영향을 주지만 critical하지 않음
      return false;
    }
  }

  /**
   * 방 참가자 목록 조회
   */
  async getRoomParticipants(scriptId: string): Promise<RoomParticipant[]> {
    try {
      const participants: RoomParticipant[] = await this.client.get(
        `/sync/sessions/script/${scriptId}/participants`
      );

      return participants;
    } catch (error) {
      console.error(
        `Failed to get participants for script ${scriptId}:`,
        error
      );
      throw error;
    }
  }

  /**
   * AI 자동 정렬 요청
   */
  async requestAutoAlign(
    scriptId: string,
    options: {
      audioUrl?: string;
      alignmentMethod?: "whisper" | "forced_alignment" | "hybrid";
      confidenceThreshold?: number;
    } = {}
  ): Promise<AutoAlignResponse> {
    try {
      const alignRequest: AutoAlignRequest = {
        script_id: scriptId,
        audio_url: options.audioUrl,
        alignment_method: options.alignmentMethod || "hybrid",
        confidence_threshold: options.confidenceThreshold || 0.7,
      };

      const response: AutoAlignResponse = await this.client.post(
        "/sync/ai-align",
        alignRequest
      );

      return response;
    } catch (error) {
      console.error(
        `Failed to request auto align for script ${scriptId}:`,
        error
      );
      throw error;
    }
  }

  /**
   * AI 자동 정렬 상태 조회
   */
  async getAutoAlignStatus(jobId: string): Promise<AutoAlignResponse> {
    try {
      const response: AutoAlignResponse = await this.client.get(
        `/sync/ai-align/status/${jobId}`
      );

      return response;
    } catch (error) {
      console.error(`Failed to get auto align status for job ${jobId}:`, error);
      throw error;
    }
  }

  /**
   * 동기화 서비스 상태 확인
   */
  async getHealthStatus(): Promise<{
    status: string;
    version: string;
    uptime: number;
  }> {
    try {
      const health = await this.client.get("/sync/health");

      return health;
    } catch (error) {
      console.error("Failed to get sync health status:", error);
      throw error;
    }
  }

  /**
   * 매핑 일괄 업로드 (CSV/JSON)
   */
  async uploadMappings(
    scriptId: string,
    mappings: Array<{
      sentenceId: string;
      startTime: number;
      endTime: number;
      confidence?: number;
    }>
  ): Promise<{ success: number; failed: number; errors: string[] }> {
    try {
      const response = await this.client.post(
        `/sync/mappings/batch/${scriptId}`,
        { mappings }
      );

      return response;
    } catch (error) {
      console.error(`Failed to upload mappings for script ${scriptId}:`, error);
      throw error;
    }
  }
}

// 싱글톤 인스턴스
let syncApiInstance: SyncApiService | null = null;

/**
 * 싱크 API 서비스 인스턴스 가져오기
 */
export function getSyncApi(): SyncApiService {
  if (!syncApiInstance) {
    syncApiInstance = new SyncApiService();
  }
  return syncApiInstance;
}

/**
 * 싱크 API 서비스 인스턴스 설정 (테스트용)
 */
export function setSyncApi(api: SyncApiService): void {
  syncApiInstance = api;
}

// 기본 export
export const syncApi = getSyncApi();
