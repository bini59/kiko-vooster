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
    const params = new URLSearchParams({
      query,
      search_type: searchType,
      limit: limit.toString()
    });

    return this.apiClient.get<WordSearchResponse>(`/words/search?${params}`);
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
      page: page.toString(),
      limit: limit.toString()
    });

    if (tags && tags.length > 0) {
      params.append('tags', tags.join(','));
    }

    if (masteryLevels && masteryLevels.length > 0) {
      params.append('mastery_levels', masteryLevels.join(','));
    }

    return this.apiClient.get(`/vocabulary/words?${params}`);
  }

  /**
   * 단어를 사용자 단어장에 추가
   */
  async addWordToVocabulary(request: AddWordRequest): Promise<AddWordResponse> {
    return this.apiClient.post<AddWordResponse>('/vocabulary/words', request);
  }

  /**
   * 사용자 단어 정보 업데이트
   */
  async updateUserWord(wordId: string, request: UpdateWordRequest): Promise<UpdateWordResponse> {
    return this.apiClient.put<UpdateWordResponse>(`/vocabulary/words/${wordId}`, request);
  }

  /**
   * 단어장에서 단어 제거
   */
  async removeWordFromVocabulary(wordId: string): Promise<{ message: string }> {
    return this.apiClient.delete(`/vocabulary/words/${wordId}`);
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
    return this.apiClient.get<string[]>('/vocabulary/tags');
  }

  /**
   * 태그별 단어 수 조회
   */
  async getTagCounts(): Promise<Record<string, number>> {
    return this.apiClient.get<Record<string, number>>('/vocabulary/tags/counts');
  }

  /**
   * 태그 이름 변경
   */
  async renameTag(oldTag: string, newTag: string): Promise<{ message: string }> {
    return this.apiClient.put('/vocabulary/tags/rename', {
      old_tag: oldTag,
      new_tag: newTag
    });
  }

  /**
   * 태그 삭제 (모든 단어에서 제거)
   */
  async deleteTag(tag: string): Promise<{ message: string }> {
    return this.apiClient.delete(`/vocabulary/tags/${encodeURIComponent(tag)}`);
  }

  // ===================
  // 통계 및 분석 API
  // ===================

  /**
   * 단어장 통계 조회
   */
  async getVocabularyStats(): Promise<VocabularyStatsResponse> {
    return this.apiClient.get<VocabularyStatsResponse>('/vocabulary/stats');
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
    return this.apiClient.get('/vocabulary/progress');
  }

  // ===================
  // 복습 시스템 API
  // ===================

  /**
   * 복습할 단어 목록 조회
   */
  async getReviewWords(request: ReviewWordsRequest): Promise<ReviewWordsResponse> {
    const params = new URLSearchParams({
      count: request.count.toString(),
      mode: request.mode
    });

    return this.apiClient.get<ReviewWordsResponse>(`/vocabulary/review?${params}`);
  }

  /**
   * 복습 결과 제출
   */
  async submitReviewResult(result: ReviewResultRequest): Promise<ReviewResultResponse> {
    return this.apiClient.post<ReviewResultResponse>('/vocabulary/review/result', result);
  }

  /**
   * 복습 세션 시작
   */
  async startReviewSession(mode: ReviewMode, count: number): Promise<{
    sessionId: string;
    words: UserWord[];
    totalDue: number;
  }> {
    return this.apiClient.post('/vocabulary/review/session', {
      mode,
      count
    });
  }

  /**
   * 복습 세션 종료
   */
  async endReviewSession(sessionId: string, results: {
    totalWords: number;
    correctAnswers: number;
    totalTime: number;
  }): Promise<{ message: string }> {
    return this.apiClient.post(`/vocabulary/review/session/${sessionId}/end`, results);
  }

  // ===================
  // 일괄 작업 API
  // ===================

  /**
   * 여러 단어 일괄 추가
   */
  async bulkAddWords(requests: AddWordRequest[]): Promise<{
    added: UserWord[];
    failed: { request: AddWordRequest; error: string }[];
  }> {
    return this.apiClient.post('/vocabulary/words/bulk', { words: requests });
  }

  /**
   * 여러 단어 일괄 업데이트
   */
  async bulkUpdateWords(updates: {
    wordId: string;
    request: UpdateWordRequest;
  }[]): Promise<{
    updated: UserWord[];
    failed: { wordId: string; error: string }[];
  }> {
    return this.apiClient.put('/vocabulary/words/bulk', { updates });
  }

  /**
   * 여러 단어 일괄 삭제
   */
  async bulkDeleteWords(wordIds: string[]): Promise<{
    deleted: string[];
    failed: { wordId: string; error: string }[];
  }> {
    return this.apiClient.request('/vocabulary/words/bulk', {
      method: 'DELETE',
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
    return this.apiClient.get('/vocabulary/export');
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
    return this.apiClient.post('/vocabulary/import', data);
  }
}

// 싱글톤 인스턴스 생성
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

/**
 * VocabularyApiService 인스턴스 설정 (테스트용)
 */
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