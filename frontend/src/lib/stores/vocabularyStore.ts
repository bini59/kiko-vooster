/**
 * 단어장 상태 관리 스토어
 * 
 * 사용자 단어장, 검색 결과, 복습 세션 등 모든 단어장 관련 상태를 관리합니다.
 * 기존 audioStore, scriptStore 패턴을 따릅니다.
 */

import { writable, derived, get } from 'svelte/store';
import {
  SearchType,
  VocabularySortBy,
  SortOrder,
  ReviewMode,
  GameMode,
  DEFAULT_VOCABULARY_FILTER,
  DEFAULT_REVIEW_SETTINGS,
  DEFAULT_VOCABULARY_CONFIG
} from '$lib/types/vocabulary';
import type {
  VocabularyState,
  VocabularyFilter,
  UserWord,
  Word,
  ReviewSession,
  ReviewProgress,
  ReviewSettings,
  ReviewAnswer,
  VocabularyStatsResponse,
  DifficultyLevel
} from '$lib/types/vocabulary';
import { vocabularyApi } from '$lib/api/vocabulary';
import { notificationActions } from '$lib/stores/notificationStore';

// ===================
// 초기 상태 정의
// ===================

const initialVocabularyState: VocabularyState = {
  // 데이터
  userWords: [],
  searchResults: [],
  allTags: [],
  stats: null,
  
  // UI 상태
  currentFilter: { ...DEFAULT_VOCABULARY_FILTER },
  currentPage: 1,
  totalPages: 1,
  pageSize: DEFAULT_VOCABULARY_CONFIG.defaultPageSize,
  
  // 로딩/에러 상태
  loading: false,
  error: null,
  
  // 선택된 단어
  selectedWord: null,
  isDetailModalOpen: false
};

const initialReviewSession: ReviewSession | null = null;

// ===================
// 기본 스토어 생성
// ===================

export const vocabularyState = writable<VocabularyState>(initialVocabularyState);
export const reviewSession = writable<ReviewSession | null>(initialReviewSession);
export const reviewSettings = writable<ReviewSettings>({ ...DEFAULT_REVIEW_SETTINGS });

// ===================
// 유도 스토어 (Derived Stores)
// ===================

/**
 * 필터링된 사용자 단어 목록
 */
export const filteredWords = derived(
  [vocabularyState],
  ([$state]) => {
    let words = [...$state.userWords];
    const filter = $state.currentFilter;

    // 검색어 필터
    if (filter.searchQuery) {
      const query = filter.searchQuery.toLowerCase();
      words = words.filter(userWord => {
        const word = userWord.word;
        if (!word) return false;

        switch (filter.searchType) {
          case SearchType.KANJI:
            return word.text.toLowerCase().includes(query);
          case SearchType.HIRAGANA:
            return word.reading?.toLowerCase().includes(query) || false;
          case SearchType.MEANING:
            return word.meaning.toLowerCase().includes(query);
          default: // ALL
            return (
              word.text.toLowerCase().includes(query) ||
              word.reading?.toLowerCase().includes(query) ||
              word.meaning.toLowerCase().includes(query) ||
              userWord.notes?.toLowerCase().includes(query) ||
              false
            );
        }
      });
    }

    // 태그 필터
    if (filter.tags.length > 0) {
      words = words.filter(userWord =>
        filter.tags.some(tag => userWord.tags.includes(tag))
      );
    }

    // 숙련도 필터
    if (filter.masteryLevels.length > 0) {
      words = words.filter(userWord =>
        filter.masteryLevels.includes(userWord.masteryLevel)
      );
    }

    // 난이도 필터
    if (filter.difficultyLevels.length > 0) {
      words = words.filter(userWord =>
        userWord.word && filter.difficultyLevels.includes(userWord.word.difficultyLevel)
      );
    }

    // 정렬
    words.sort((a, b) => {
      let comparison = 0;
      
      switch (filter.sortBy) {
        case VocabularySortBy.ADDED_DATE:
          comparison = new Date(a.addedAt).getTime() - new Date(b.addedAt).getTime();
          break;
        case VocabularySortBy.LAST_REVIEWED:
          const aReviewed = a.lastReviewed ? new Date(a.lastReviewed).getTime() : 0;
          const bReviewed = b.lastReviewed ? new Date(b.lastReviewed).getTime() : 0;
          comparison = aReviewed - bReviewed;
          break;
        case VocabularySortBy.MASTERY_LEVEL:
          comparison = a.masteryLevel - b.masteryLevel;
          break;
        case VocabularySortBy.ALPHABETICAL:
          comparison = (a.word?.text || '').localeCompare(b.word?.text || '');
          break;
        case VocabularySortBy.DIFFICULTY:
          const difficultyOrder = { beginner: 1, intermediate: 2, advanced: 3 };
          const aDiff = difficultyOrder[a.word?.difficultyLevel || 'beginner'];
          const bDiff = difficultyOrder[b.word?.difficultyLevel || 'beginner'];
          comparison = aDiff - bDiff;
          break;
      }

      return filter.sortOrder === SortOrder.DESC ? -comparison : comparison;
    });

    return words;
  }
);

/**
 * 현재 페이지의 단어 목록
 */
export const paginatedWords = derived(
  [filteredWords, vocabularyState],
  ([$filteredWords, $state]) => {
    const startIndex = ($state.currentPage - 1) * $state.pageSize;
    const endIndex = startIndex + $state.pageSize;
    return $filteredWords.slice(startIndex, endIndex);
  }
);

/**
 * 복습 진행도
 */
export const reviewProgress = derived(
  [reviewSession],
  ([$session]): ReviewProgress | null => {
    if (!$session) return null;

    const totalWords = $session.words.length;
    const currentIndex = $session.currentIndex;
    const answers = $session.answers;
    
    const correctAnswers = answers.filter(a => a.correct).length;
    const incorrectAnswers = answers.filter(a => !a.correct).length;
    
    const averageResponseTime = answers.length > 0
      ? answers.reduce((sum, a) => sum + a.responseTime, 0) / answers.length
      : 0;
    
    const accuracyRate = answers.length > 0
      ? (correctAnswers / answers.length) * 100
      : 0;

    return {
      totalWords,
      currentIndex,
      correctAnswers,
      incorrectAnswers,
      averageResponseTime,
      accuracyRate,
      remainingWords: totalWords - currentIndex
    };
  }
);

/**
 * 현재 복습 단어
 */
export const currentReviewWord = derived(
  [reviewSession],
  ([$session]) => {
    if (!$session || $session.currentIndex >= $session.words.length) {
      return null;
    }
    return $session.words[$session.currentIndex];
  }
);

/**
 * 복습 완료 여부
 */
export const isReviewComplete = derived(
  [reviewSession],
  ([$session]) => {
    if (!$session) return false;
    return $session.currentIndex >= $session.words.length;
  }
);

/**
 * 모든 태그와 사용 빈도
 */
export const tagFrequency = derived(
  [vocabularyState],
  ([$state]) => {
    const frequency: Record<string, number> = {};
    $state.userWords.forEach(userWord => {
      userWord.tags.forEach(tag => {
        frequency[tag] = (frequency[tag] || 0) + 1;
      });
    });
    return frequency;
  }
);

/**
 * 인기 태그 (상위 10개)
 */
export const popularTags = derived(
  [tagFrequency],
  ([$frequency]) => {
    return Object.entries($frequency)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)
      .map(([tag]) => tag);
  }
);

// ===================
// 액션 함수들
// ===================

export const vocabularyActions = {
  /**
   * 단어장 데이터 로드
   */
  async loadUserWords(refresh = false) {
    if (!refresh && get(vocabularyState).userWords.length > 0) {
      return; // 이미 로드된 경우 스킵
    }

    vocabularyState.update(state => ({ ...state, loading: true, error: null }));

    try {
      const response = await vocabularyApi.getUserWords(1, 1000); // 모든 단어 로드
      const tags = await vocabularyApi.getTags();
      const stats = await vocabularyApi.getStats();

      vocabularyState.update(state => ({
        ...state,
        userWords: response.words,
        allTags: tags,
        stats,
        loading: false,
        totalPages: response.totalPages
      }));
    } catch (error) {
      console.error('Failed to load user words:', error);
      vocabularyState.update(state => ({
        ...state,
        loading: false,
        error: '단어장을 불러오는데 실패했습니다.'
      }));
      notificationActions.add({
        type: 'error',
        message: '단어장을 불러오는데 실패했습니다.'
      });
    }
  },

  /**
   * 단어 검색
   */
  async searchWords(query: string, searchType: SearchType = SearchType.ALL) {
    if (!query.trim()) {
      vocabularyState.update(state => ({ ...state, searchResults: [] }));
      return;
    }

    vocabularyState.update(state => ({ ...state, loading: true }));

    try {
      const response = await vocabularyApi.searchWords(query, searchType, 20);
      vocabularyState.update(state => ({
        ...state,
        searchResults: response.results,
        loading: false
      }));
    } catch (error) {
      console.error('Failed to search words:', error);
      vocabularyState.update(state => ({
        ...state,
        loading: false,
        error: '단어 검색에 실패했습니다.'
      }));
    }
  },

  /**
   * 단어장에 단어 추가
   */
  async addWord(wordText: string, tags: string[] = [], notes?: string) {
    try {
      const response = await vocabularyApi.addWord(wordText, tags, notes);
      
      vocabularyState.update(state => ({
        ...state,
        userWords: [...state.userWords, response.word]
      }));

      notificationActions.add({
        type: 'success',
        message: `"${wordText}"이(가) 단어장에 추가되었습니다.`
      });

      return response.word;
    } catch (error) {
      console.error('Failed to add word:', error);
      notificationActions.add({
        type: 'error',
        message: '단어 추가에 실패했습니다.'
      });
      throw error;
    }
  },

  /**
   * 단어 정보 업데이트
   */
  async updateWord(wordId: string, updates: { masteryLevel?: number; tags?: string[]; notes?: string }) {
    try {
      // API 호출 시 백엔드가 기대하는 형식으로 변환
      const response = await vocabularyApi.updateWord(wordId, {
        masteryLevel: updates.masteryLevel,
        tags: updates.tags,
        notes: updates.notes
      });
      
      vocabularyState.update(state => ({
        ...state,
        userWords: state.userWords.map(word =>
          word.id === wordId ? response.word : word
        )
      }));

      notificationActions.add({
        type: 'success',
        message: '단어 정보가 업데이트되었습니다.'
      });

      return response.word;
    } catch (error) {
      console.error('Failed to update word:', error);
      notificationActions.add({
        type: 'error',
        message: '단어 업데이트에 실패했습니다.'
      });
      throw error;
    }
  },

  /**
   * 단어장에서 단어 제거
   */
  async removeWord(wordId: string) {
    try {
      await vocabularyApi.removeWord(wordId);
      
      vocabularyState.update(state => ({
        ...state,
        userWords: state.userWords.filter(word => word.id !== wordId)
      }));

      notificationActions.add({
        type: 'success',
        message: '단어가 단어장에서 제거되었습니다.'
      });
    } catch (error) {
      console.error('Failed to remove word:', error);
      notificationActions.add({
        type: 'error',
        message: '단어 제거에 실패했습니다.'
      });
      throw error;
    }
  },

  /**
   * 필터 설정
   */
  setFilter(filter: Partial<VocabularyFilter>) {
    vocabularyState.update(state => ({
      ...state,
      currentFilter: { ...state.currentFilter, ...filter },
      currentPage: 1 // 필터 변경 시 첫 페이지로
    }));
  },

  /**
   * 페이지 변경
   */
  setPage(page: number) {
    vocabularyState.update(state => ({ ...state, currentPage: page }));
  },

  /**
   * 단어 선택 (상세 보기용)
   */
  selectWord(word: UserWord | null) {
    vocabularyState.update(state => ({
      ...state,
      selectedWord: word,
      isDetailModalOpen: !!word
    }));
  },

  /**
   * 상세 모달 닫기
   */
  closeDetailModal() {
    vocabularyState.update(state => ({
      ...state,
      selectedWord: null,
      isDetailModalOpen: false
    }));
  },

  /**
   * 에러 상태 초기화
   */
  clearError() {
    vocabularyState.update(state => ({ ...state, error: null }));
  }
};

export const reviewActions = {
  /**
   * 복습 세션 시작
   */
  async startReview(mode: ReviewMode, gameMode: GameMode, count: number = 10) {
    try {
      const response = await vocabularyApi.getReviewWords(count, mode);
      
      if (response.words.length === 0) {
        notificationActions.add({
          type: 'info',
          message: '복습할 단어가 없습니다.'
        });
        return null;
      }

      const session: ReviewSession = {
        id: `session_${Date.now()}`,
        mode,
        gameMode,
        words: response.words,
        currentIndex: 0,
        answers: [],
        startTime: new Date().toISOString(),
        settings: get(reviewSettings)
      };

      reviewSession.set(session);
      
      notificationActions.add({
        type: 'success',
        message: `${response.words.length}개 단어로 복습을 시작합니다.`
      });

      return session;
    } catch (error) {
      console.error('Failed to start review:', error);
      notificationActions.add({
        type: 'error',
        message: '복습 시작에 실패했습니다.'
      });
      throw error;
    }
  },

  /**
   * 다음 단어로 이동
   */
  nextWord() {
    reviewSession.update(session => {
      if (!session) return null;
      return {
        ...session,
        currentIndex: session.currentIndex + 1
      };
    });
  },

  /**
   * 답변 제출
   */
  async submitAnswer(userAnswer: string, correct: boolean, responseTime: number) {
    const session = get(reviewSession);
    if (!session) return;

    const currentWord = session.words[session.currentIndex];
    if (!currentWord) return;

    const answer: ReviewAnswer = {
      wordId: currentWord.id,
      correct,
      userAnswer,
      correctAnswer: currentWord.word?.text || '',
      responseTime,
      timestamp: new Date().toISOString()
    };

    // 세션에 답변 추가
    reviewSession.update(session => {
      if (!session) return null;
      return {
        ...session,
        answers: [...session.answers, answer]
      };
    });

    // 백엔드에 결과 전송
    try {
      await vocabularyApi.submitReviewResult({
        wordId: currentWord.id,
        correct,
        responseTime
      });
    } catch (error) {
      console.error('Failed to submit review result:', error);
    }
  },

  /**
   * 복습 세션 종료
   */
  async endReview() {
    const session = get(reviewSession);
    if (!session) return;

    try {
      const totalTime = new Date().getTime() - new Date(session.startTime).getTime();
      const correctAnswers = session.answers.filter(a => a.correct).length;

      // 세션 종료 시간 설정
      reviewSession.update(session => {
        if (!session) return null;
        return {
          ...session,
          endTime: new Date().toISOString()
        };
      });

      // 결과 알림
      const accuracyRate = session.answers.length > 0
        ? Math.round((correctAnswers / session.answers.length) * 100)
        : 0;

      notificationActions.add({
        type: 'success',
        message: `복습 완료! 정답률: ${accuracyRate}% (${correctAnswers}/${session.answers.length})`
      });

      // 단어장 데이터 새로고침 (숙련도 업데이트 반영)
      await vocabularyActions.loadUserWords(true);
      
    } catch (error) {
      console.error('Failed to end review:', error);
    } finally {
      // 세션 초기화
      reviewSession.set(null);
    }
  },

  /**
   * 복습 설정 업데이트
   */
  updateSettings(settings: Partial<ReviewSettings>) {
    reviewSettings.update(current => ({ ...current, ...settings }));
  }
};

// 초기화 함수 (앱 시작 시 호출)
export async function initializeVocabulary() {
  await vocabularyActions.loadUserWords();
}

// 통합 스토어 객체 (기존 코드 호환성을 위해)
export const vocabularyStore = {
  ...vocabularyActions,
  ...reviewActions,
  state: vocabularyState,
  reviewSession,
  reviewSettings,
  filteredWords,
  paginatedWords,
  reviewProgress,
  initializeVocabulary
}; 