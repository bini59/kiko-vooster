/**
 * 오디오 서비스 - HTML5 Audio API 래핑
 *
 * 기능:
 * - 오디오 재생/일시정지/탐색
 * - AB 구간 반복 재생
 * - 실시간 상태 업데이트
 * - 오류 처리 및 이벤트 관리
 */

import {
  audioState,
  abRepeatState,
  audioActions,
  abRepeatActions,
  type AudioState,
  type ABRepeatState,
} from "$lib/stores/audioStore";
import { scriptActions } from "$lib/stores/scriptStore";
import { get } from "svelte/store";

export class AudioService {
  private audio: HTMLAudioElement | null = null;
  private updateInterval: number | null = null;
  private abRepeatCheckInterval: number | null = null;
  private isInitialized = false;

  constructor() {
    this.initialize();
  }

  /**
   * 오디오 서비스 초기화
   */
  private async initialize() {
    if (this.isInitialized) return;

    try {
      this.audio = new Audio();
      this.setupEventListeners();
      this.setupStoreSubscriptions();
      this.isInitialized = true;

      console.log("🎵 AudioService initialized successfully");
    } catch (error) {
      console.error("❌ AudioService initialization failed:", error);
      audioActions.setError("오디오 서비스 초기화에 실패했습니다");
    }
  }

  /**
   * HTML5 Audio 이벤트 리스너 설정
   */
  private setupEventListeners() {
    if (!this.audio) return;

    // 메타데이터 로드 완료
    this.audio.addEventListener("loadedmetadata", () => {
      if (!this.audio) return;

      audioState.update((state) => ({
        ...state,
        duration: this.audio!.duration,
        isLoading: false,
        error: null,
      }));

      console.log("📊 Audio metadata loaded, duration:", this.audio.duration);
    });

    // 오디오 데이터 로딩 시작
    this.audio.addEventListener("loadstart", () => {
      audioActions.setLoading(true);
      audioActions.setError(null);
    });

    // 재생 가능 상태
    this.audio.addEventListener("canplay", () => {
      audioActions.setLoading(false);
    });

    // 재생 시작
    this.audio.addEventListener("play", () => {
      audioState.update((state) => ({ ...state, isPlaying: true }));
      this.startTimeTracking();
      this.startABRepeatTracking();
    });

    // 일시정지
    this.audio.addEventListener("pause", () => {
      audioState.update((state) => ({ ...state, isPlaying: false }));
      this.stopTimeTracking();
      this.stopABRepeatTracking();
    });

    // 재생 종료
    this.audio.addEventListener("ended", () => {
      audioState.update((state) => ({ ...state, isPlaying: false }));
      this.stopTimeTracking();
      this.stopABRepeatTracking();
    });

    // 시간 업데이트
    this.audio.addEventListener("timeupdate", () => {
      if (!this.audio) return;
      this.handleTimeUpdate(this.audio.currentTime);
    });

    // 탐색 (사용자가 진행바 조작)
    this.audio.addEventListener("seeking", () => {
      audioActions.setLoading(true);
    });

    this.audio.addEventListener("seeked", () => {
      audioActions.setLoading(false);
      if (this.audio) {
        this.handleTimeUpdate(this.audio.currentTime);
      }
    });

    // 오류 처리
    this.audio.addEventListener("error", (e) => {
      const error = this.audio?.error;
      let errorMessage = "오디오 재생 중 오류가 발생했습니다";

      if (error) {
        switch (error.code) {
          case MediaError.MEDIA_ERR_ABORTED:
            errorMessage = "오디오 로딩이 중단되었습니다";
            break;
          case MediaError.MEDIA_ERR_NETWORK:
            errorMessage = "네트워크 오류로 오디오를 로드할 수 없습니다";
            break;
          case MediaError.MEDIA_ERR_DECODE:
            errorMessage = "오디오 디코딩 오류가 발생했습니다";
            break;
          case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
            errorMessage = "지원하지 않는 오디오 형식입니다";
            break;
        }
      }

      console.error("🚨 Audio error:", error, e);
      audioActions.setError(errorMessage);
    });

    // 볼륨 변경
    this.audio.addEventListener("volumechange", () => {
      if (this.audio) {
        audioState.update((state) => ({
          ...state,
          volume: this.audio!.volume,
        }));
      }
    });

    // 재생 속도 변경
    this.audio.addEventListener("ratechange", () => {
      if (this.audio) {
        audioState.update((state) => ({
          ...state,
          playbackRate: this.audio!.playbackRate,
        }));
      }
    });
  }

  /**
   * 스토어 구독 설정 - 스토어 변경사항을 오디오 요소에 반영
   */
  private setupStoreSubscriptions() {
    // 볼륨 변경 구독
    audioState.subscribe((state) => {
      if (this.audio && this.audio.volume !== state.volume) {
        this.audio.volume = state.volume;
      }
      if (this.audio && this.audio.playbackRate !== state.playbackRate) {
        this.audio.playbackRate = state.playbackRate;
      }
    });
  }

  /**
   * 시간 업데이트 처리
   */
  private handleTimeUpdate(currentTime: number) {
    // 오디오 상태 업데이트
    audioActions.updateTime(currentTime);

    // 스크립트 하이라이트 업데이트
    scriptActions.updateHighlightByTime(currentTime);

    // AB 반복 확인
    this.checkABRepeat(currentTime);
  }

  /**
   * 실시간 시간 추적 시작
   */
  private startTimeTracking() {
    if (this.updateInterval) return;

    this.updateInterval = window.setInterval(() => {
      if (this.audio && !this.audio.paused) {
        this.handleTimeUpdate(this.audio.currentTime);
      }
    }, 100); // 100ms마다 업데이트
  }

  /**
   * 실시간 시간 추적 중지
   */
  private stopTimeTracking() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }
  }

  /**
   * AB 반복 추적 시작
   */
  private startABRepeatTracking() {
    if (this.abRepeatCheckInterval) return;

    this.abRepeatCheckInterval = window.setInterval(() => {
      if (this.audio && !this.audio.paused) {
        this.checkABRepeat(this.audio.currentTime);
      }
    }, 50); // 50ms마다 체크 (정확한 반복을 위해)
  }

  /**
   * AB 반복 추적 중지
   */
  private stopABRepeatTracking() {
    if (this.abRepeatCheckInterval) {
      clearInterval(this.abRepeatCheckInterval);
      this.abRepeatCheckInterval = null;
    }
  }

  /**
   * AB 반복 체크 및 처리
   */
  private checkABRepeat(currentTime: number) {
    const abState = get(abRepeatState);

    if (!abState.isActive || !abState.pointA || !abState.pointB) return;

    // B 포인트를 넘어서면 A 포인트로 돌아가기
    if (currentTime >= abState.pointB) {
      this.seekTo(abState.pointA);
      abRepeatActions.incrementRepeatCount();

      // 최대 반복 횟수 체크
      if (abState.maxRepeats && abState.repeatCount >= abState.maxRepeats) {
        abRepeatActions.toggleRepeat(); // 반복 중지
      }
    }
  }

  // ==================== 공개 메서드들 ====================

  /**
   * 오디오 파일 로드
   */
  async loadAudio(url: string): Promise<void> {
    if (!this.audio) {
      await this.initialize();
    }

    if (!this.audio) {
      throw new Error("Audio initialization failed");
    }

    try {
      audioActions.setLoading(true);
      audioActions.setError(null);

      this.audio.src = url;
      this.audio.load();

      console.log("🎵 Loading audio:", url);

      // 메타데이터 로드 대기
      return new Promise((resolve, reject) => {
        if (!this.audio) {
          reject(new Error("Audio not initialized"));
          return;
        }

        const onLoadedMetadata = () => {
          this.audio!.removeEventListener("loadedmetadata", onLoadedMetadata);
          this.audio!.removeEventListener("error", onError);
          resolve();
        };

        const onError = () => {
          this.audio!.removeEventListener("loadedmetadata", onLoadedMetadata);
          this.audio!.removeEventListener("error", onError);
          reject(new Error("Failed to load audio"));
        };

        this.audio.addEventListener("loadedmetadata", onLoadedMetadata);
        this.audio.addEventListener("error", onError);
      });
    } catch (error) {
      console.error("❌ Failed to load audio:", error);
      audioActions.setError("오디오 파일을 로드할 수 없습니다");
      throw error;
    }
  }

  /**
   * 재생/일시정지 토글
   */
  async togglePlay(): Promise<void> {
    if (!this.audio) {
      throw new Error("Audio not loaded");
    }

    try {
      if (this.audio.paused) {
        await this.audio.play();
      } else {
        this.audio.pause();
      }
    } catch (error) {
      console.error("❌ Failed to toggle play:", error);
      audioActions.setError("재생 제어에 실패했습니다");
      throw error;
    }
  }

  /**
   * 특정 시간으로 탐색
   */
  seekTo(time: number): void {
    if (!this.audio) return;

    const targetTime = Math.max(0, Math.min(time, this.audio.duration || 0));
    this.audio.currentTime = targetTime;

    console.log("⏩ Seeking to:", targetTime);
  }

  /**
   * 볼륨 설정
   */
  setVolume(volume: number): void {
    if (!this.audio) return;

    const clampedVolume = Math.max(0, Math.min(1, volume));
    this.audio.volume = clampedVolume;
    audioActions.setVolume(clampedVolume);
  }

  /**
   * 재생 속도 설정
   */
  setPlaybackRate(rate: number): void {
    if (!this.audio) return;

    const clampedRate = Math.max(0.25, Math.min(2, rate));
    this.audio.playbackRate = clampedRate;
    audioActions.setPlaybackRate(clampedRate);
  }

  /**
   * A 포인트 설정
   */
  setPointA(time?: number): void {
    const currentTime = time ?? this.audio?.currentTime ?? 0;
    abRepeatActions.setPointA(currentTime);
    console.log("📍 A point set at:", currentTime);
  }

  /**
   * B 포인트 설정
   */
  setPointB(time?: number): void {
    const currentTime = time ?? this.audio?.currentTime ?? 0;
    abRepeatActions.setPointB(currentTime);
    console.log("📍 B point set at:", currentTime);
  }

  /**
   * AB 반복 토글
   */
  toggleABRepeat(): void {
    abRepeatActions.toggleRepeat();

    const abState = get(abRepeatState);
    console.log("🔄 AB repeat:", abState.isActive ? "ON" : "OFF");
  }

  /**
   * AB 포인트 초기화
   */
  clearABPoints(): void {
    abRepeatActions.clearPoints();
    console.log("🗑️ AB points cleared");
  }

  /**
   * 문장 클릭 핸들러 - 해당 문장의 시작 시간으로 탐색
   */
  jumpToSentence(sentenceId: string, mappings: any[]): void {
    const mapping = mappings.find(
      (m) => m.sentenceId === sentenceId && m.isActive
    );

    if (mapping) {
      this.seekTo(mapping.startTime);
      scriptActions.setCurrentSentence(sentenceId);
      console.log(
        "🎯 Jumped to sentence:",
        sentenceId,
        "at",
        mapping.startTime
      );
    } else {
      console.warn("⚠️ No mapping found for sentence:", sentenceId);
    }
  }

  /**
   * 정리 - 컴포넌트 언마운트 시 호출
   */
  destroy(): void {
    this.stopTimeTracking();
    this.stopABRepeatTracking();

    if (this.audio) {
      this.audio.pause();
      this.audio.src = "";
      this.audio.load();
      this.audio = null;
    }

    this.isInitialized = false;
    console.log("🧹 AudioService destroyed");
  }

  /**
   * 현재 오디오 요소 반환 (디버깅용)
   */
  getAudioElement(): HTMLAudioElement | null {
    return this.audio;
  }

  /**
   * 서비스 상태 확인
   */
  isReady(): boolean {
    return this.isInitialized && this.audio !== null;
  }
}

// 싱글톤 인스턴스
export const audioService = new AudioService();
