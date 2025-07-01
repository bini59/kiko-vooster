/**
 * 스크립트 상태 관리 스토어
 */

import { writable, derived } from "svelte/store";

// 스크립트 관련 인터페이스
export interface Sentence {
  id: string;
  content: string;
  orderIndex: number;
  metadata?: Record<string, any>;
}

export interface SentenceMapping {
  id: string;
  sentenceId: string;
  startTime: number;
  endTime: number;
  mappingType: "manual" | "auto" | "ai_generated";
  confidence: number;
  isActive: boolean;
}

export interface Script {
  id: string;
  title: string;
  description?: string;
  language: string;
  sentences: Sentence[];
  mappings: SentenceMapping[];
  metadata?: Record<string, any>;
}

export interface HighlightState {
  currentSentenceId: string | null;
  highlightedSentences: Set<string>;
  isAutoHighlight: boolean;
}

// 초기 상태
const initialScript: Script | null = null;
const initialHighlightState: HighlightState = {
  currentSentenceId: null,
  highlightedSentences: new Set(),
  isAutoHighlight: true,
};

// 스토어 생성
export const currentScript = writable<Script | null>(initialScript);
export const highlightState = writable<HighlightState>(initialHighlightState);

// 유도 스토어
export const sentences = derived(
  currentScript,
  ($script) => $script?.sentences || []
);

export const mappings = derived(
  currentScript,
  ($script) => $script?.mappings || []
);

export const currentSentence = derived(
  [sentences, highlightState],
  ([$sentences, $highlight]) => {
    if (!$highlight.currentSentenceId) return null;
    return (
      $sentences.find((s) => s.id === $highlight.currentSentenceId) || null
    );
  }
);

export const activeMappings = derived(mappings, ($mappings) =>
  $mappings.filter((m) => m.isActive)
);

// 문장별 매핑 정보 조회 함수
export const getSentenceMapping = derived(
  [mappings],
  ([$mappings]) =>
    (sentenceId: string) => {
      return $mappings.find((m) => m.sentenceId === sentenceId && m.isActive);
    }
);

// 시간대별 문장 조회 함수
export const getSentenceByTime = derived(
  [sentences, mappings],
  ([$sentences, $mappings]) =>
    (currentTime: number) => {
      const mapping = $mappings.find(
        (m) =>
          m.isActive && currentTime >= m.startTime && currentTime <= m.endTime
      );

      if (!mapping) return null;

      return $sentences.find((s) => s.id === mapping.sentenceId) || null;
    }
);

// 액션 함수들
export const scriptActions = {
  // 스크립트 설정
  setScript: (script: Script) => {
    currentScript.set(script);
    // 스크립트 변경 시 하이라이트 초기화
    highlightState.update((state) => ({
      ...state,
      currentSentenceId: null,
      highlightedSentences: new Set(),
    }));
  },

  // 현재 문장 설정 (하이라이트)
  setCurrentSentence: (sentenceId: string | null) => {
    highlightState.update((state) => ({
      ...state,
      currentSentenceId: sentenceId,
    }));
  },

  // 문장 하이라이트 추가
  addHighlight: (sentenceId: string) => {
    highlightState.update((state) => ({
      ...state,
      highlightedSentences: new Set([
        ...state.highlightedSentences,
        sentenceId,
      ]),
    }));
  },

  // 문장 하이라이트 제거
  removeHighlight: (sentenceId: string) => {
    highlightState.update((state) => {
      const newSet = new Set(state.highlightedSentences);
      newSet.delete(sentenceId);
      return {
        ...state,
        highlightedSentences: newSet,
      };
    });
  },

  // 모든 하이라이트 초기화
  clearHighlights: () => {
    highlightState.update((state) => ({
      ...state,
      highlightedSentences: new Set(),
      currentSentenceId: null,
    }));
  },

  // 자동 하이라이트 토글
  toggleAutoHighlight: () => {
    highlightState.update((state) => ({
      ...state,
      isAutoHighlight: !state.isAutoHighlight,
    }));
  },

  // 시간 기반 자동 하이라이트 업데이트
  updateHighlightByTime: (currentTime: number) => {
    // 시간에 해당하는 문장 찾기
    mappings.subscribe(($mappings) => {
      const mapping = $mappings.find(
        (m) =>
          m.isActive && currentTime >= m.startTime && currentTime <= m.endTime
      );

      highlightState.update((state) => {
        if (!state.isAutoHighlight) return state;

        const newSentenceId = mapping?.sentenceId || null;

        // 문장이 변경된 경우에만 업데이트
        if (newSentenceId !== state.currentSentenceId) {
          return {
            ...state,
            currentSentenceId: newSentenceId,
          };
        }

        return state;
      });
    })();
  },
};
