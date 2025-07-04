/**
 * 단어장 API 서비스
 * 
 * 단어 검색, 사용자 단어장 관리, 복습 기능을 위한 모든 API 호출을 담당합니다.
 */

import { getApiClient } from './client';
import {
  SearchType,
  ReviewMode
} from '$lib/types/vocabulary';
import type {
  Word,
  UserWord,
  WordSearchRequest,
  WordSearchResponse,
  AddWordRequest,
  AddWordResponse,
  UpdateWordRequest,
  UpdateWordResponse,
  VocabularyStatsResponse,
  ReviewWordsRequest,
  ReviewWordsResponse,
  ReviewResultRequest,
  ReviewResultResponse,
  DifficultyLevel,
  PartOfSpeech
} from '$lib/types/vocabulary';

export class VocabularyApiService {
  private apiClient = getApiClient();

  // ===================
  // 단어 검색 API
  // ===================

  /**
   * 단어 검색 (JMdict 사전)
   */
  async searchWords(
    query: string,
    searchType: SearchType = SearchType.ALL,
    limit: number = 20
  ): Promise<WordSearchResponse> {
    // 백엔드는 POST 방식으로 request body를 받습니다
    return this.apiClient.post<WordSearchResponse>('/words/search', {
      query,
      search_type: searchType,
      limit
    });
  }

  /**
   * 단어 상세 정보 조회
   */
  async getWordDetail(wordId: string): Promise<Word> {
    return this.apiClient.get<Word>(`/words/${wordId}`);
  }

  /**
   * 인기 단어 목록 조회
   */
  async getPopularWords(limit: number = 10): Promise<Word[]> {
    const params = new URLSearchParams({
      limit: limit.toString()
    });

    return this.apiClient.get<Word[]>(`/words/popular?${params}`);
  }

  /**
   * 난이도별 단어 목록 조회
   */
  async getWordsByDifficulty(
    difficulty: DifficultyLevel,
    limit: number = 20,
    offset: number = 0
  ): Promise<Word[]> {
    const params = new URLSearchParams({
      difficulty,
      limit: limit.toString(),
      offset: offset.toString()
    });

    return this.apiClient.get<Word[]>(`/words/by-difficulty?${params}`);
  }

  // ===================
  // 사용자 단어장 API
  // ===================

  /**
   * 사용자 단어장 목록 조회
   */
  async getUserWords(
    page: number = 1,
    limit: number = 20,
    tags?: string[],
    masteryLevels?: number[]
  ): Promise<{ words: UserWord[]; total: number; page: number; totalPages: number }> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: ((page - 1) * limit).toString()
    });

    if (tags && tags.length > 0) {
      // 백엔드는 여러 태그를 개별 쿼리 파라미터로 받습니다
      tags.forEach(tag => params.append('tags', tag));
    }

    if (masteryLevels && masteryLevels.length > 0) {
      // 백엔드는 단일 mastery_level만 지원하므로 첫 번째 값 사용
      params.append('mastery_level', masteryLevels[0].toString());
    }

    // 수정된 경로: /words/vocabulary/list
    const response = await this.apiClient.get(`/words/vocabulary/list?${params}`);
    
    // 백엔드 응답을 프론트엔드 형식에 맞게 변환
    return {
      words: response.words,
      total: response.total,
      page: page,
      totalPages: Math.ceil(response.total / limit)
    };
  }

  /**
   * 단어를 사용자 단어장에 추가
   */
  async addWordToVocabulary(request: AddWordRequest): Promise<AddWordResponse> {
    // 수정된 경로: /words/vocabulary/add
    return this.apiClient.post<AddWordResponse>('/words/vocabulary/add', {
      word_text: request.wordText,
      tags: request.tags,
      notes: request.notes
    });
  }

  /**
   * 사용자 단어 정보 업데이트
   */
  async updateUserWord(wordId: string, request: UpdateWordRequest): Promise<UpdateWordResponse> {
    // 수정된 경로: /words/vocabulary/{wordId}
    return this.apiClient.put<UpdateWordResponse>(`/words/vocabulary/${wordId}`, {
      mastery_level: request.masteryLevel,
      tags: request.tags,
      notes: request.notes
    });
  }

  /**
   * 단어장에서 단어 제거
   */
  async removeWordFromVocabulary(wordId: string): Promise<{ message: string }> {
    // 수정된 경로: /words/vocabulary/{wordId}
    return this.apiClient.delete(`/words/vocabulary/${wordId}`);
  }

  /**
   * 단어 숙련도 업데이트
   */
  async updateMasteryLevel(wordId: string, masteryLevel: number): Promise<UpdateWordResponse> {
    return this.updateUserWord(wordId, { masteryLevel });
  }

  /**
   * 단어 태그 업데이트
   */
  async updateWordTags(wordId: string, tags: string[]): Promise<UpdateWordResponse> {
    return this.updateUserWord(wordId, { tags });
  }

  /**
   * 단어 노트 업데이트
   */
  async updateWordNotes(wordId: string, notes: string): Promise<UpdateWordResponse> {
    return this.updateUserWord(wordId, { notes });
  }

  // ===================
  // 태그 관리 API
  // ===================

  /**
   * 사용자의 모든 태그 조회
   */
  async getUserTags(): Promise<string[]> {
    // 수정된 경로: /words/vocabulary/tags
    const response = await this.apiClient.get<{ tags: string[] }>('/words/vocabulary/tags');
    return response.tags;
  }

  /**
   * 태그별 단어 수 조회
   */
  async getTagCounts(): Promise<Record<string, number>> {
    return this.apiClient.get<Record<string, number>>('/words/vocabulary/tags/counts');
  }

  /**
   * 태그 이름 변경
   */
  async renameTag(oldTag: string, newTag: string): Promise<{ message: string }> {
    return this.apiClient.put('/words/vocabulary/tags/rename', {
      old_tag: oldTag,
      new_tag: newTag
    });
  }

  /**
   * 태그 삭제 (모든 단어에서 제거)
   */
  async deleteTag(tag: string): Promise<{ message: string }> {
    return this.apiClient.delete(`/words/vocabulary/tags/${encodeURIComponent(tag)}`);
  }

  // ===================
  // 통계 및 분석 API
  // ===================

  /**
   * 단어장 통계 조회
   */
  async getVocabularyStats(): Promise<VocabularyStatsResponse> {
    // 수정된 경로: /words/vocabulary/stats
    return this.apiClient.get<VocabularyStatsResponse>('/words/vocabulary/stats');
  }

  /**
   * 학습 진행도 조회
   */
  async getLearningProgress(): Promise<{
    totalWords: number;
    masteryDistribution: Record<string, number>;
    weeklyAdditions: number[];
    accuracyTrend: number[];
  }> {
    return this.apiClient.get('/words/vocabulary/progress');
  }

  // ===================
  // 복습 시스템 API
  // ===================

  /**
   * 복습할 단어 목록 조회
   */
  async getReviewWords(request: ReviewWordsRequest): Promise<ReviewWordsResponse> {
    // 백엔드는 POST 방식으로 request body를 받습니다
    return this.apiClient.post<ReviewWordsResponse>('/words/review/words', {
      count: request.count,
      mode: request.mode
    });
  }

  /**
   * 복습 결과 제출
   */
  async submitReviewResult(result: ReviewResultRequest): Promise<ReviewResultResponse> {
    // 수정된 경로: /words/review/submit
    return this.apiClient.post<ReviewResultResponse>('/words/review/submit', result);
  }

  /**
   * 복습 세션 시작
   */
  async startReviewSession(mode: ReviewMode, count: number): Promise<{
    sessionId: string;
    words: UserWord[];
    totalDue: number;
  }> {
    return this.apiClient.post('/words/review/start', { mode, count });
  }

  /**
   * 복습 세션 종료
   */
  async endReviewSession(sessionId: string, results: {
    totalWords: number;
    correctAnswers: number;
    totalTime: number;
  }): Promise<{ message: string }> {
    return this.apiClient.post(`/words/review/sessions/${sessionId}/end`, results);
  }

  // ===================
  // 벌크 작업 API
  // ===================

  /**
   * 여러 단어를 한번에 추가
   */
  async bulkAddWords(requests: AddWordRequest[]): Promise<{
    added: UserWord[];
    failed: { request: AddWordRequest; error: string }[];
  }> {
    return this.apiClient.post('/words/vocabulary/bulk/add', { words: requests });
  }

  /**
   * 여러 단어를 한번에 업데이트
   */
  async bulkUpdateWords(updates: {
    wordId: string;
    request: UpdateWordRequest;
  }[]): Promise<{
    updated: UserWord[];
    failed: { wordId: string; error: string }[];
  }> {
    return this.apiClient.put('/words/vocabulary/bulk/update', { updates });
  }

  /**
   * 여러 단어를 한번에 삭제
   */
  async bulkDeleteWords(wordIds: string[]): Promise<{
    deleted: string[];
    failed: { wordId: string; error: string }[];
  }> {
    // DELETE 요청에서 body 데이터를 보내는 방식 조정
    return this.apiClient.request('/words/vocabulary/bulk/delete', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ word_ids: wordIds })
    });
  }

  // ===================
  // 내보내기/가져오기 API
  // ===================

  /**
   * 단어장 내보내기 (JSON 형식)
   */
  async exportVocabulary(): Promise<{
    words: UserWord[];
    metadata: {
      exportDate: string;
      totalWords: number;
      version: string;
    };
  }> {
    return this.apiClient.get('/words/vocabulary/export');
  }

  /**
   * 단어장 가져오기 (JSON 형식)
   */
  async importVocabulary(data: {
    words: Omit<UserWord, 'id' | 'userId'>[];
    replaceExisting?: boolean;
  }): Promise<{
    imported: UserWord[];
    skipped: number;
    failed: { word: any; error: string }[];
  }> {
    return this.apiClient.post('/words/vocabulary/import', data);
  }
}

// 싱글톤 인스턴스 관리
let vocabularyApiService: VocabularyApiService | null = null;

/**
 * VocabularyApiService 인스턴스 반환
 */
export function getVocabularyApiService(): VocabularyApiService {
  if (!vocabularyApiService) {
    vocabularyApiService = new VocabularyApiService();
  }
  return vocabularyApiService;
}

export function setVocabularyApiService(service: VocabularyApiService): void {
  vocabularyApiService = service;
}

// 편의 함수들
export const vocabularyApi = {
  // 검색
  searchWords: (query: string, searchType?: SearchType, limit?: number) =>
    getVocabularyApiService().searchWords(query, searchType, limit),
  
  getWordDetail: (wordId: string) =>
    getVocabularyApiService().getWordDetail(wordId),
  
  // 단어장 관리
  getUserWords: (page?: number, limit?: number, tags?: string[], masteryLevels?: number[]) =>
    getVocabularyApiService().getUserWords(page, limit, tags, masteryLevels),
  
  addWord: (wordText: string, tags: string[] = [], notes?: string) =>
    getVocabularyApiService().addWordToVocabulary({ wordText, tags, notes }),
  
  updateWord: (wordId: string, updates: UpdateWordRequest) =>
    getVocabularyApiService().updateUserWord(wordId, updates),
  
  removeWord: (wordId: string) =>
    getVocabularyApiService().removeWordFromVocabulary(wordId),
  
  // 복습
  getReviewWords: (count: number, mode: ReviewMode) =>
    getVocabularyApiService().getReviewWords({ count, mode }),
  
  submitReviewResult: (result: ReviewResultRequest) =>
    getVocabularyApiService().submitReviewResult(result),
  
  // 통계
  getStats: () => getVocabularyApiService().getVocabularyStats(),
  getTags: () => getVocabularyApiService().getUserTags(),
};

export default vocabularyApi; 