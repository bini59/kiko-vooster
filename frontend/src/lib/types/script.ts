/**
 * 스크립트 관련 타입 정의
 */

// 문장 정보
export interface Sentence {
  id: string;
  content: string;
  orderIndex: number;
  metadata?: Record<string, any>;
}

// 문장 매핑 정보 (타임코드)
export interface SentenceMapping {
  id: string;
  sentenceId: string;
  startTime: number;
  endTime: number;
  mappingType: "manual" | "auto" | "ai_generated";
  confidence: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

// 스크립트 정보
export interface Script {
  id: string;
  title: string;
  description?: string;
  language: string;
  sentences: Sentence[];
  mappings: SentenceMapping[];
  metadata?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

// 하이라이트 상태
export interface HighlightState {
  currentSentenceId: string | null;
  highlightedSentences: Set<string>;
  isAutoHighlight: boolean;
}

// 문장 클릭 이벤트
export interface SentenceClickEvent {
  sentenceId: string;
  sentence: Sentence;
  mapping?: SentenceMapping;
  event: MouseEvent | KeyboardEvent;
}
