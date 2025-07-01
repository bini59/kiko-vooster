/**
 * 스크립트 관련 API 서비스
 *
 * 백엔드 /api/v1/scripts 엔드포인트와 연동
 */

import { getApiClient, ApiError } from "./client.js";
import type { Script, Sentence } from "$lib/types/script.js";

// 백엔드 응답 타입 정의
interface BackendSentence {
  id: string;
  text: string;
  reading?: string; // 후리가나
  translation: string;
  start_time: number; // 시작 시간 (초)
  end_time: number; // 종료 시간 (초)
  difficulty_level: string;
}

interface BackendScript {
  id: string;
  title: string;
  description: string;
  audio_url: string;
  thumbnail_url?: string;
  duration: number; // 총 재생 시간 (초)
  difficulty_level: string;
  category: string; // news, anime, podcast, etc.
  language: string;
  created_at: string;
  sentences: BackendSentence[];
}

interface PlaybackProgress {
  script_id: string;
  current_time: number; // 현재 재생 시간 (초)
  completed_sentences: string[]; // 완료한 문장 ID 목록
  last_played: string; // ISO 문자열
}

// API 요청/응답 타입
interface GetScriptsParams {
  category?: string;
  difficulty?: string;
  limit?: number;
  offset?: number;
}

interface UpdateProgressRequest {
  current_time: number;
  completed_sentences: string[];
}

interface GetProgressResponse {
  script_id: string;
  current_time: number;
  completed_sentences: string[];
  last_played: string;
}

// 타입 변환 함수들
function convertBackendSentenceToFrontend(
  backendSentence: BackendSentence,
  orderIndex: number
): Sentence {
  return {
    id: backendSentence.id,
    content: backendSentence.text,
    orderIndex,
    metadata: {
      reading: backendSentence.reading,
      translation: backendSentence.translation,
      startTime: backendSentence.start_time,
      endTime: backendSentence.end_time,
      difficultyLevel: backendSentence.difficulty_level,
    },
  };
}

function convertBackendScriptToFrontend(backendScript: BackendScript): Script {
  const sentences = backendScript.sentences.map((sentence, index) =>
    convertBackendSentenceToFrontend(sentence, index)
  );

  return {
    id: backendScript.id,
    title: backendScript.title,
    description: backendScript.description,
    language: backendScript.language,
    sentences,
    mappings: [], // 매핑은 별도 API에서 로드
    metadata: {
      audioUrl: backendScript.audio_url,
      thumbnailUrl: backendScript.thumbnail_url,
      duration: backendScript.duration,
      difficultyLevel: backendScript.difficulty_level,
      category: backendScript.category,
    },
    createdAt: backendScript.created_at,
    updatedAt: backendScript.created_at, // 백엔드에서 updatedAt이 없으므로 createdAt 사용
  };
}

class ScriptsApiService {
  private client = getApiClient();

  /**
   * 스크립트 목록 조회
   */
  async getScripts(params: GetScriptsParams = {}): Promise<Script[]> {
    try {
      const queryParams = new URLSearchParams();

      if (params.category) queryParams.append("category", params.category);
      if (params.difficulty)
        queryParams.append("difficulty", params.difficulty);
      if (params.limit) queryParams.append("limit", params.limit.toString());
      if (params.offset) queryParams.append("offset", params.offset.toString());

      const queryString = queryParams.toString();
      const endpoint = `/scripts${queryString ? `?${queryString}` : ""}`;

      const backendScripts: BackendScript[] = await this.client.get(endpoint);

      return backendScripts.map(convertBackendScriptToFrontend);
    } catch (error) {
      console.error("Failed to fetch scripts:", error);
      throw error;
    }
  }

  /**
   * 특정 스크립트 상세 조회
   */
  async getScript(scriptId: string): Promise<Script> {
    try {
      const backendScript: BackendScript = await this.client.get(
        `/scripts/${scriptId}`
      );

      return convertBackendScriptToFrontend(backendScript);
    } catch (error) {
      console.error(`Failed to fetch script ${scriptId}:`, error);
      throw error;
    }
  }

  /**
   * 스크립트의 문장 목록만 조회
   */
  async getScriptSentences(scriptId: string): Promise<Sentence[]> {
    try {
      const backendSentences: BackendSentence[] = await this.client.get(
        `/scripts/${scriptId}/sentences`
      );

      return backendSentences.map((sentence, index) =>
        convertBackendSentenceToFrontend(sentence, index)
      );
    } catch (error) {
      console.error(`Failed to fetch sentences for script ${scriptId}:`, error);
      throw error;
    }
  }

  /**
   * 재생 진행률 업데이트
   */
  async updatePlaybackProgress(
    scriptId: string,
    progress: UpdateProgressRequest
  ): Promise<void> {
    try {
      const progressData: PlaybackProgress = {
        script_id: scriptId,
        current_time: progress.current_time,
        completed_sentences: progress.completed_sentences,
        last_played: new Date().toISOString(),
      };

      await this.client.post(`/scripts/${scriptId}/progress`, progressData);
    } catch (error) {
      console.error(`Failed to update progress for script ${scriptId}:`, error);
      // 진행률 업데이트 실패는 사용자 경험을 크게 해치지 않으므로 조용히 로그만 남김
      // throw하지 않음
    }
  }

  /**
   * 재생 진행률 조회
   */
  async getPlaybackProgress(
    scriptId: string
  ): Promise<GetProgressResponse | null> {
    try {
      const progress: GetProgressResponse = await this.client.get(
        `/scripts/${scriptId}/progress`
      );

      return progress;
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        // 진행률이 없는 경우 null 반환
        return null;
      }

      console.error(`Failed to fetch progress for script ${scriptId}:`, error);
      throw error;
    }
  }

  /**
   * 카테고리 목록 조회
   */
  async getCategories(): Promise<string[]> {
    try {
      const response: { categories: string[] } = await this.client.get(
        "/scripts/categories"
      );

      return response.categories || [];
    } catch (error) {
      console.error("Failed to fetch categories:", error);
      throw error;
    }
  }

  /**
   * 스크립트 북마크 추가
   */
  async bookmarkScript(scriptId: string): Promise<void> {
    try {
      await this.client.post(`/scripts/${scriptId}/bookmark`);
    } catch (error) {
      console.error(`Failed to bookmark script ${scriptId}:`, error);
      throw error;
    }
  }

  /**
   * 스크립트 북마크 제거
   */
  async removeBookmark(scriptId: string): Promise<void> {
    try {
      await this.client.delete(`/scripts/${scriptId}/bookmark`);
    } catch (error) {
      console.error(`Failed to remove bookmark for script ${scriptId}:`, error);
      throw error;
    }
  }

  /**
   * 스크립트 검색 (제목, 설명으로)
   */
  async searchScripts(
    query: string,
    params: GetScriptsParams = {}
  ): Promise<Script[]> {
    try {
      const searchParams = {
        ...params,
        q: query,
      };

      const queryParams = new URLSearchParams();
      Object.entries(searchParams).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });

      const endpoint = `/scripts/search?${queryParams.toString()}`;
      const backendScripts: BackendScript[] = await this.client.get(endpoint);

      return backendScripts.map(convertBackendScriptToFrontend);
    } catch (error) {
      console.error("Failed to search scripts:", error);
      throw error;
    }
  }
}

// 싱글톤 인스턴스
let scriptsApiInstance: ScriptsApiService | null = null;

/**
 * 스크립트 API 서비스 인스턴스 가져오기
 */
export function getScriptsApi(): ScriptsApiService {
  if (!scriptsApiInstance) {
    scriptsApiInstance = new ScriptsApiService();
  }
  return scriptsApiInstance;
}

/**
 * 스크립트 API 서비스 인스턴스 설정 (테스트용)
 */
export function setScriptsApi(api: ScriptsApiService): void {
  scriptsApiInstance = api;
}

// 기본 export
export const scriptsApi = getScriptsApi();
