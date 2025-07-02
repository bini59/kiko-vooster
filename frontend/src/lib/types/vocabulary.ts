/**
 * 단어장 관련 타입 정의
 * 
 * 백엔드 API와 일치하는 타입들과 프론트엔드 전용 UI 상태 타입들을 정의합니다.
 */

// ===================
// 기본 열거형 타입
// ===================

export enum DifficultyLevel {
  BEGINNER = "beginner",
  INTERMEDIATE = "intermediate", 
  ADVANCED = "advanced"
}

export enum PartOfSpeech {
  NOUN = "noun",
  VERB = "verb",
  ADJECTIVE = "adjective", 
  ADVERB = "adverb",
  PARTICLE = "particle",
  INTERJECTION = "interjection",
  CONJUNCTION = "conjunction",
  PRONOUN = "pronoun",
  AUXILIARY = "auxiliary",
  COUNTER = "counter",
  PREFIX = "prefix",
  SUFFIX = "suffix",
  UNKNOWN = "unknown"
}

export enum SearchType {
  ALL = "all",
  KANJI = "kanji", 
  HIRAGANA = "hiragana",
  MEANING = "meaning"
}

export enum ReviewMode {
  NEW = "new",
  REVIEW = "review", 
  MIXED = "mixed"
}

export enum GameMode {
  FLASHCARD = "flashcard",
  FILL_IN_BLANKS = "fill_in_blanks", 
  SPELLING = "spelling"
}

// ===================
// 기본 데이터 모델
// ===================

export interface Word {
  id: string;
  text: string;
  reading?: string;
  meaning: string;
  partOfSpeech: PartOfSpeech;
  difficultyLevel: DifficultyLevel;
  exampleSentence?: string;
  exampleTranslation?: string;
  audioUrl?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface UserWord {
  id: string;
  userId: string;
  wordId: string;
  word?: Word;
  masteryLevel: number; // 0-5
  reviewCount: number;
  tags: string[];
  notes?: string;
  addedAt: string;
  lastReviewed?: string;
  nextReview?: string;
  updatedAt?: string;
}

// ===================
// API 요청/응답 타입
// ===================

export interface WordSearchRequest {
  query: string;
  searchType: SearchType;
  limit: number;
}

export interface WordSearchResponse {
  results: Word[];
  total: number;
  query: string;
  searchType: SearchType;
}

export interface AddWordRequest {
  wordText: string;
  tags: string[];
  notes?: string;
}

export interface AddWordResponse {
  message: string;
  word: UserWord;
}

export interface UpdateWordRequest {
  masteryLevel?: number;
  tags?: string[];
  notes?: string;
}

export interface UpdateWordResponse {
  message: string;
  word: UserWord;
}

export interface VocabularyStatsResponse {
  totalWords: number;
  masteryDistribution: Record<string, number>;
  recentAdditions: number;
  dueForReview: number;
  favoriteTags: string[];
  tagCounts: Record<string, number>;
}

export interface ReviewWordsRequest {
  count: number;
  mode: ReviewMode;
}

export interface ReviewWordsResponse {
  words: UserWord[];
  totalDue: number;
  mode: ReviewMode;
  sessionId?: string;
}

export interface ReviewResultRequest {
  wordId: string;
  correct: boolean;
  responseTime?: number;
  sessionId?: string;
}

export interface ReviewResultResponse {
  message: string;
  correct: boolean;
  newMasteryLevel: number;
  nextReview?: string;
  responseTime?: number;
}

// ===================
// UI 상태 타입
// ===================

export interface VocabularyFilter {
  tags: string[];
  masteryLevels: number[];
  difficultyLevels: DifficultyLevel[];
  searchQuery: string;
  searchType: SearchType;
  sortBy: VocabularySortBy;
  sortOrder: SortOrder;
}

export enum VocabularySortBy {
  ADDED_DATE = "addedDate",
  LAST_REVIEWED = "lastReviewed", 
  MASTERY_LEVEL = "masteryLevel",
  ALPHABETICAL = "alphabetical",
  DIFFICULTY = "difficulty"
}

export enum SortOrder {
  ASC = "asc",
  DESC = "desc"
}

export interface VocabularyState {
  // 데이터
  userWords: UserWord[];
  searchResults: Word[];
  allTags: string[];
  stats: VocabularyStatsResponse | null;
  
  // UI 상태
  currentFilter: VocabularyFilter;
  currentPage: number;
  totalPages: number;
  pageSize: number;
  
  // 로딩/에러 상태
  loading: boolean;
  error: string | null;
  
  // 선택된 단어
  selectedWord: UserWord | null;
  isDetailModalOpen: boolean;
}

// ===================
// 복습 세션 타입
// ===================

export interface ReviewSession {
  id: string;
  mode: ReviewMode;
  gameMode: GameMode;
  words: UserWord[];
  currentIndex: number;
  answers: ReviewAnswer[];
  startTime: string;
  endTime?: string;
  settings: ReviewSettings;
}

export interface ReviewAnswer {
  wordId: string;
  correct: boolean;
  userAnswer: string;
  correctAnswer: string;
  responseTime: number; // milliseconds
  timestamp: string;
}

export interface ReviewSettings {
  showReading: boolean;
  showExample: boolean;
  autoAdvance: boolean;
  timeLimit?: number; // seconds
  shuffleWords: boolean;
  repeatIncorrect: boolean;
}

export interface ReviewProgress {
  totalWords: number;
  currentIndex: number;
  correctAnswers: number;
  incorrectAnswers: number;
  averageResponseTime: number;
  accuracyRate: number;
  remainingWords: number;
}

// ===================
// 게임 모드별 타입
// ===================

export interface FlashcardState {
  showAnswer: boolean;
  isAnswered: boolean;
  difficulty: 'easy' | 'medium' | 'hard';
}

export interface FillInBlanksState {
  sentence: string;
  blanks: BlankInfo[];
  userAnswers: string[];
  isSubmitted: boolean;
}

export interface BlankInfo {
  index: number;
  correctAnswer: string;
  hint?: string;
  position: {
    start: number;
    end: number;
  };
}

export interface SpellingGameState {
  targetWord: string;
  userInput: string;
  hints: SpellingHint[];
  isSubmitted: boolean;
  showHiragana: boolean;
}

export interface SpellingHint {
  type: 'character' | 'length' | 'reading';
  value: string;
  revealed: boolean;
}

// ===================
// 이벤트 타입
// ===================

export interface WordClickEvent {
  word: Word | UserWord;
  action: 'view' | 'edit' | 'delete' | 'practice';
  event: MouseEvent | KeyboardEvent;
}

export interface ReviewCompleteEvent {
  session: ReviewSession;
  results: ReviewResults;
}

export interface ReviewResults {
  totalWords: number;
  correctAnswers: number;
  incorrectAnswers: number;
  accuracyRate: number;
  totalTime: number;
  averageResponseTime: number;
  wordsToReview: UserWord[];
}

export interface TagSelectEvent {
  tags: string[];
  action: 'add' | 'remove' | 'filter';
}

// ===================
// 설정 및 환경 타입
// ===================

export interface VocabularyConfig {
  maxWordsPerSession: number;
  defaultPageSize: number;
  autoSaveInterval: number; // milliseconds
  maxTagsPerWord: number;
  reviewIntervals: number[]; // days for each mastery level
}

export interface AccessibilitySettings {
  reducedMotion: boolean;
  highContrast: boolean;
  fontSize: 'small' | 'medium' | 'large';
  screenReaderAnnouncements: boolean;
  keyboardShortcuts: boolean;
}

// ===================
// 유틸리티 타입
// ===================

export type WordId = string;
export type UserId = string;
export type TagName = string;

export type VocabularyAction = 
  | { type: 'LOAD_WORDS'; payload: UserWord[] }
  | { type: 'ADD_WORD'; payload: UserWord }
  | { type: 'UPDATE_WORD'; payload: UserWord }
  | { type: 'REMOVE_WORD'; payload: WordId }
  | { type: 'SET_FILTER'; payload: Partial<VocabularyFilter> }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SELECT_WORD'; payload: UserWord | null };

export type ReviewAction =
  | { type: 'START_SESSION'; payload: ReviewSession }
  | { type: 'NEXT_WORD' }
  | { type: 'ANSWER_WORD'; payload: ReviewAnswer }
  | { type: 'END_SESSION' }
  | { type: 'UPDATE_SETTINGS'; payload: Partial<ReviewSettings> };

// ===================
// 기본값 상수
// ===================

export const DEFAULT_VOCABULARY_FILTER: VocabularyFilter = {
  tags: [],
  masteryLevels: [],
  difficultyLevels: [],
  searchQuery: '',
  searchType: SearchType.ALL,
  sortBy: VocabularySortBy.ADDED_DATE,
  sortOrder: SortOrder.DESC
};

export const DEFAULT_REVIEW_SETTINGS: ReviewSettings = {
  showReading: true,
  showExample: true,
  autoAdvance: false,
  shuffleWords: true,
  repeatIncorrect: true
};

export const DEFAULT_VOCABULARY_CONFIG: VocabularyConfig = {
  maxWordsPerSession: 50,
  defaultPageSize: 20,
  autoSaveInterval: 30000, // 30 seconds
  maxTagsPerWord: 10,
  reviewIntervals: [1, 3, 7, 14, 30, 90] // days
};

// ===================
// 타입 가드 함수
// ===================

export function isWord(obj: any): obj is Word {
  return obj && typeof obj.id === 'string' && typeof obj.text === 'string';
}

export function isUserWord(obj: any): obj is UserWord {
  return obj && typeof obj.id === 'string' && typeof obj.userId === 'string';
}

export function isValidMasteryLevel(level: any): level is number {
  return typeof level === 'number' && level >= 0 && level <= 5;
}

export function isValidDifficulty(difficulty: any): difficulty is DifficultyLevel {
  return Object.values(DifficultyLevel).includes(difficulty);
}

export function isValidPartOfSpeech(pos: any): pos is PartOfSpeech {
  return Object.values(PartOfSpeech).includes(pos);
} 