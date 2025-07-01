/**
 * 스크립트-오디오 싱크 관련 타입 정의
 */

import type { AudioState, ABRepeatState } from "./audio.js";
import type { Script, HighlightState } from "./script.js";

// 싱크 연결 상태
export interface SyncConnectionState {
  isConnected: boolean;
  wsUrl: string | null;
  reconnectAttempts: number;
  lastError: string | null;
}

// 실시간 동기화 상태
export interface SyncState {
  connection: SyncConnectionState;
  currentScript: Script | null;
  audioState: AudioState;
  highlightState: HighlightState;
  abRepeatState: ABRepeatState;
  editMode: boolean;
  syncAccuracy: number; // 동기화 정확도 (0-1)
}

// WebSocket 메시지 타입
export interface WebSocketMessage {
  type: "POSITION_UPDATE" | "MAPPING_EDIT" | "CONNECTION_ACK" | "PING" | "PONG";
  scriptId?: string;
  sentenceId?: string;
  currentTime?: number;
  isPlaying?: boolean;
  data?: any;
  timestamp: number;
}

// 싱크 UI 설정
export interface SyncUISettings {
  autoScroll: boolean;
  highlightDelay: number; // ms
  clickToSeek: boolean;
  showTimestamps: boolean;
  fontSize: "sm" | "md" | "lg" | "xl";
  theme: "light" | "dark" | "auto";
  accessibilityMode: boolean;
}
