/**
 * 오디오 관련 타입 정의
 */

// 오디오 재생 상태
export interface AudioState {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  playbackRate: number;
  buffered: TimeRanges | null;
  isLoading: boolean;
  error: string | null;
}

// AB 반복 상태
export interface ABRepeatState {
  pointA: number | null;
  pointB: number | null;
  isActive: boolean;
  repeatCount: number;
  maxRepeats: number | null;
}

// 오디오 플레이어 이벤트
export interface AudioPlayerEvent {
  type: "play" | "pause" | "timeupdate" | "loadstart" | "loadeddata" | "error";
  currentTime?: number;
  duration?: number;
  error?: string;
}

// 오디오 플레이어 제어 인터페이스
export interface AudioController {
  play(): Promise<void>;
  pause(): void;
  seekTo(time: number): void;
  setVolume(volume: number): void;
  setPlaybackRate(rate: number): void;
  getCurrentTime(): number;
  getDuration(): number;
  isPlaying(): boolean;
}
