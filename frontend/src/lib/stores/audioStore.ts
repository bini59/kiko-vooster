/**
 * 오디오 상태 관리 스토어
 */

import { writable, derived } from "svelte/store";

// 오디오 상태 인터페이스
export interface AudioState {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  playbackRate: number;
  isLoading: boolean;
  error: string | null;
}

// AB 반복 상태 인터페이스
export interface ABRepeatState {
  pointA: number | null;
  pointB: number | null;
  isActive: boolean;
  repeatCount: number;
  maxRepeats: number | null;
}

// 초기 오디오 상태
const initialAudioState: AudioState = {
  isPlaying: false,
  currentTime: 0,
  duration: 0,
  volume: 1.0,
  playbackRate: 1.0,
  isLoading: false,
  error: null,
};

// 초기 AB 반복 상태
const initialABRepeatState: ABRepeatState = {
  pointA: null,
  pointB: null,
  isActive: false,
  repeatCount: 0,
  maxRepeats: null,
};

// 스토어 생성
export const audioState = writable<AudioState>(initialAudioState);
export const abRepeatState = writable<ABRepeatState>(initialABRepeatState);

// 유도 스토어 (computed 상태)
export const isWithinABRange = derived(
  [audioState, abRepeatState],
  ([$audio, $abRepeat]) => {
    if (!$abRepeat.pointA || !$abRepeat.pointB) return false;
    return (
      $audio.currentTime >= $abRepeat.pointA &&
      $audio.currentTime <= $abRepeat.pointB
    );
  }
);

export const abRangeDuration = derived(abRepeatState, ($abRepeat) => {
  if (!$abRepeat.pointA || !$abRepeat.pointB) return 0;
  return $abRepeat.pointB - $abRepeat.pointA;
});

export const formattedCurrentTime = derived(audioState, ($audio) =>
  formatTime($audio.currentTime)
);

export const formattedDuration = derived(audioState, ($audio) =>
  formatTime($audio.duration)
);

// 헬퍼 함수
function formatTime(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, "0")}:${secs
      .toString()
      .padStart(2, "0")}`;
  }
  return `${minutes}:${secs.toString().padStart(2, "0")}`;
}

// 액션 함수들
export const audioActions = {
  // 재생/일시정지 토글
  togglePlay: () => {
    audioState.update((state) => ({
      ...state,
      isPlaying: !state.isPlaying,
    }));
  },

  // 시간 업데이트
  updateTime: (currentTime: number) => {
    audioState.update((state) => ({
      ...state,
      currentTime,
    }));
  },

  // 볼륨 설정
  setVolume: (volume: number) => {
    audioState.update((state) => ({
      ...state,
      volume: Math.max(0, Math.min(1, volume)),
    }));
  },

  // 재생 속도 설정
  setPlaybackRate: (rate: number) => {
    audioState.update((state) => ({
      ...state,
      playbackRate: Math.max(0.25, Math.min(2, rate)),
    }));
  },

  // 에러 설정
  setError: (error: string | null) => {
    audioState.update((state) => ({
      ...state,
      error,
      isLoading: false,
    }));
  },

  // 로딩 상태 설정
  setLoading: (isLoading: boolean) => {
    audioState.update((state) => ({
      ...state,
      isLoading,
    }));
  },
};

// AB 반복 액션들
export const abRepeatActions = {
  // A 포인트 설정
  setPointA: (time?: number) => {
    audioState.subscribe((audio) => {
      abRepeatState.update((state) => ({
        ...state,
        pointA: time ?? audio.currentTime,
      }));
    })();
  },

  // B 포인트 설정
  setPointB: (time?: number) => {
    audioState.subscribe((audio) => {
      abRepeatState.update((state) => ({
        ...state,
        pointB: time ?? audio.currentTime,
      }));
    })();
  },

  // AB 반복 토글
  toggleRepeat: () => {
    abRepeatState.update((state) => ({
      ...state,
      isActive: !state.isActive,
      repeatCount: 0,
    }));
  },

  // AB 포인트 초기화
  clearPoints: () => {
    abRepeatState.update((state) => ({
      ...state,
      pointA: null,
      pointB: null,
      isActive: false,
      repeatCount: 0,
    }));
  },

  // 반복 횟수 증가
  incrementRepeatCount: () => {
    abRepeatState.update((state) => ({
      ...state,
      repeatCount: state.repeatCount + 1,
    }));
  },
};
