/**
 * WebSocket 실시간 동기화 서비스
 *
 * 백엔드 WebSocket API와 연동하여 실시간 상태 동기화를 처리
 * 위치 동기화, 매핑 업데이트, 참가자 상태 등
 */

import { browser } from "$app/environment";
import { get, writable, type Writable } from "svelte/store";
import type { WebSocketMessage } from "$lib/types/sync.js";

// WebSocket 연결 상태
export const wsConnectionState = writable<{
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  reconnectAttempts: number;
  lastConnectedAt: string | null;
}>({
  isConnected: false,
  isConnecting: false,
  error: null,
  reconnectAttempts: 0,
  lastConnectedAt: null,
});

// 실시간 이벤트 리스너 타입
type EventListener<T = any> = (data: T) => void;

interface WebSocketEventMap {
  position_sync: {
    connection_id: string;
    position: number;
    is_playing: boolean;
    sentence_id?: string;
  };
  mapping_update: {
    connection_id: string;
    sentence_id: string;
    start_time: number;
    end_time: number;
    edit_type: string;
  };
  participant_join: { connection_id: string; user_id?: string };
  participant_leave: { connection_id: string; user_id?: string };
  connection_ack: {
    connection_id: string;
    room_id: string;
    user_id?: string;
    message: string;
  };
  error: { code: string; message: string; details?: any };
  pong: { timestamp: string };
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private currentScriptId: string | null = null;
  private connectionId: string | null = null;
  private roomId: string | null = null;

  // 이벤트 리스너들
  private eventListeners: Map<keyof WebSocketEventMap, Set<EventListener>> =
    new Map();

  // 재연결 설정
  private reconnectDelay = 1000; // 1초
  private maxReconnectDelay = 30000; // 30초
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectTimeoutId: number | null = null;

  // Ping/Pong 설정
  private pingInterval = 30000; // 30초
  private pingTimeoutId: number | null = null;
  private pongTimeoutId: number | null = null;

  // 메시지 큐 (연결 실패 시 임시 저장)
  private messageQueue: WebSocketMessage[] = [];

  /**
   * 스크립트 룸에 연결
   */
  async connect(scriptId: string, authToken?: string): Promise<void> {
    if (!browser) {
      console.warn("WebSocket connection attempted on server side");
      return;
    }

    if (
      this.ws &&
      this.ws.readyState === WebSocket.OPEN &&
      this.currentScriptId === scriptId
    ) {
      console.log("Already connected to the same script");
      return;
    }

    // 기존 연결 정리
    this.disconnect();

    this.currentScriptId = scriptId;

    wsConnectionState.update((state) => ({
      ...state,
      isConnecting: true,
      error: null,
    }));

    try {
      const wsUrl = this.buildWebSocketUrl(scriptId, authToken);
      this.ws = new WebSocket(wsUrl);

      this.setupEventHandlers();

      // 연결 타임아웃 (10초)
      const connectionTimeout = setTimeout(() => {
        if (this.ws && this.ws.readyState !== WebSocket.OPEN) {
          this.ws.close();
          this.handleConnectionError(new Error("Connection timeout"));
        }
      }, 10000);

      // 연결 성공 시 타임아웃 클리어
      this.ws.addEventListener(
        "open",
        () => {
          clearTimeout(connectionTimeout);
        },
        { once: true }
      );
    } catch (error) {
      this.handleConnectionError(error as Error);
    }
  }

  /**
   * WebSocket URL 구성
   */
  private buildWebSocketUrl(scriptId: string, authToken?: string): string {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host.replace("5173", "8000"); // dev 환경 포트 변경
    let url = `${protocol}//${host}/ws/sync/${scriptId}`;

    if (authToken) {
      url += `?token=${encodeURIComponent(authToken)}`;
    }

    return url;
  }

  /**
   * WebSocket 이벤트 핸들러 설정
   */
  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.addEventListener("open", this.handleOpen.bind(this));
    this.ws.addEventListener("message", this.handleMessage.bind(this));
    this.ws.addEventListener("close", this.handleClose.bind(this));
    this.ws.addEventListener("error", this.handleError.bind(this));
  }

  /**
   * 연결 성공 처리
   */
  private handleOpen(): void {
    console.log("WebSocket connected");

    wsConnectionState.update((state) => ({
      ...state,
      isConnected: true,
      isConnecting: false,
      error: null,
      reconnectAttempts: 0,
      lastConnectedAt: new Date().toISOString(),
    }));

    this.reconnectAttempts = 0;

    // 큐에 저장된 메시지들 전송
    this.flushMessageQueue();

    // Ping 시작
    this.startPing();
  }

  /**
   * 메시지 수신 처리
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);

      console.debug("WebSocket message received:", message);

      switch (message.type) {
        case "CONNECTION_ACK":
          this.handleConnectionAck(message.data);
          break;
        case "POSITION_SYNC":
          this.emitEvent("position_sync", message.data);
          break;
        case "MAPPING_UPDATE":
          this.emitEvent("mapping_update", message.data);
          break;
        case "PARTICIPANT_JOIN":
          this.emitEvent("participant_join", message.data);
          break;
        case "PARTICIPANT_LEAVE":
          this.emitEvent("participant_leave", message.data);
          break;
        case "PONG":
          this.handlePong(message.data);
          break;
        default:
          console.warn("Unknown WebSocket message type:", message.type);
      }
    } catch (error) {
      console.error("Failed to parse WebSocket message:", error);
    }
  }

  /**
   * 연결 확인 메시지 처리
   */
  private handleConnectionAck(data: any): void {
    this.connectionId = data.connection_id;
    this.roomId = data.room_id;

    this.emitEvent("connection_ack", data);

    console.log(
      `Connected to room ${this.roomId} with connection ID ${this.connectionId}`
    );
  }

  /**
   * Pong 응답 처리
   */
  private handlePong(data: any): void {
    if (this.pongTimeoutId) {
      clearTimeout(this.pongTimeoutId);
      this.pongTimeoutId = null;
    }

    this.emitEvent("pong", data);

    console.debug("Pong received");
  }

  /**
   * 연결 종료 처리
   */
  private handleClose(event: CloseEvent): void {
    console.log("WebSocket closed:", event.code, event.reason);

    wsConnectionState.update((state) => ({
      ...state,
      isConnected: false,
      isConnecting: false,
    }));

    this.stopPing();

    // 비정상 종료 시 재연결 시도
    if (event.code !== 1000 && this.currentScriptId) {
      this.scheduleReconnect();
    }
  }

  /**
   * 에러 처리
   */
  private handleError(event: Event): void {
    console.error("WebSocket error:", event);

    this.handleConnectionError(new Error("WebSocket connection error"));
  }

  /**
   * 연결 에러 처리
   */
  private handleConnectionError(error: Error): void {
    wsConnectionState.update((state) => ({
      ...state,
      isConnected: false,
      isConnecting: false,
      error: error.message,
    }));

    this.emitEvent("error", {
      code: "CONNECTION_ERROR",
      message: error.message,
    });

    if (this.currentScriptId) {
      this.scheduleReconnect();
    }
  }

  /**
   * 재연결 스케줄링
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      wsConnectionState.update((state) => ({
        ...state,
        error: "Connection failed after maximum retry attempts",
      }));
      return;
    }

    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts),
      this.maxReconnectDelay
    );

    console.log(
      `Scheduling reconnection in ${delay}ms (attempt ${
        this.reconnectAttempts + 1
      })`
    );

    this.reconnectTimeoutId = window.setTimeout(() => {
      this.reconnectAttempts++;
      wsConnectionState.update((state) => ({
        ...state,
        reconnectAttempts: this.reconnectAttempts,
      }));

      if (this.currentScriptId) {
        this.connect(this.currentScriptId);
      }
    }, delay);
  }

  /**
   * Ping 전송 시작
   */
  private startPing(): void {
    this.stopPing();

    this.pingTimeoutId = window.setInterval(() => {
      this.sendPing();
    }, this.pingInterval);
  }

  /**
   * Ping 전송 중지
   */
  private stopPing(): void {
    if (this.pingTimeoutId) {
      clearInterval(this.pingTimeoutId);
      this.pingTimeoutId = null;
    }

    if (this.pongTimeoutId) {
      clearTimeout(this.pongTimeoutId);
      this.pongTimeoutId = null;
    }
  }

  /**
   * Ping 메시지 전송
   */
  private sendPing(): void {
    if (!this.isConnected()) return;

    this.sendMessage({
      type: "PING",
      timestamp: Date.now(),
    });

    // Pong 타임아웃 설정 (5초)
    this.pongTimeoutId = window.setTimeout(() => {
      console.warn("Pong timeout - connection may be dead");
      this.ws?.close(1002, "Ping timeout");
    }, 5000);
  }

  /**
   * 메시지 큐 flush
   */
  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.isConnected()) {
      const message = this.messageQueue.shift();
      if (message) {
        this.sendMessage(message);
      }
    }
  }

  /**
   * 메시지 전송
   */
  sendMessage(message: Partial<WebSocketMessage>): void {
    const fullMessage: WebSocketMessage = {
      type: message.type || "POSITION_UPDATE",
      scriptId: message.scriptId || this.currentScriptId || "",
      data: message.data,
      timestamp: message.timestamp || Date.now(),
    };

    if (this.isConnected()) {
      try {
        this.ws!.send(JSON.stringify(fullMessage));
      } catch (error) {
        console.error("Failed to send WebSocket message:", error);
        this.messageQueue.push(fullMessage);
      }
    } else {
      // 연결이 안 되어 있으면 큐에 저장
      this.messageQueue.push(fullMessage);

      // 큐 크기 제한 (최대 50개)
      if (this.messageQueue.length > 50) {
        this.messageQueue.shift();
      }
    }
  }

  /**
   * 재생 위치 업데이트 전송
   */
  sendPositionUpdate(
    position: number,
    isPlaying: boolean,
    sentenceId?: string
  ): void {
    this.sendMessage({
      type: "POSITION_UPDATE",
      data: {
        position,
        is_playing: isPlaying,
        sentence_id: sentenceId,
      },
    });
  }

  /**
   * 매핑 편집 알림 전송
   */
  sendMappingEdit(
    sentenceId: string,
    startTime: number,
    endTime: number,
    editType = "manual"
  ): void {
    this.sendMessage({
      type: "MAPPING_EDIT",
      data: {
        sentence_id: sentenceId,
        start_time: startTime,
        end_time: endTime,
        edit_type: editType,
      },
    });
  }

  /**
   * 이벤트 리스너 등록
   */
  on<K extends keyof WebSocketEventMap>(
    eventType: K,
    listener: EventListener<WebSocketEventMap[K]>
  ): void {
    if (!this.eventListeners.has(eventType)) {
      this.eventListeners.set(eventType, new Set());
    }
    this.eventListeners.get(eventType)!.add(listener);
  }

  /**
   * 이벤트 리스너 제거
   */
  off<K extends keyof WebSocketEventMap>(
    eventType: K,
    listener: EventListener<WebSocketEventMap[K]>
  ): void {
    const listeners = this.eventListeners.get(eventType);
    if (listeners) {
      listeners.delete(listener);
    }
  }

  /**
   * 이벤트 발생
   */
  private emitEvent<K extends keyof WebSocketEventMap>(
    eventType: K,
    data: WebSocketEventMap[K]
  ): void {
    const listeners = this.eventListeners.get(eventType);
    if (listeners) {
      listeners.forEach((listener) => {
        try {
          listener(data);
        } catch (error) {
          console.error(
            `Error in WebSocket event listener for ${eventType}:`,
            error
          );
        }
      });
    }
  }

  /**
   * 연결 상태 확인
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * 연결 해제
   */
  disconnect(): void {
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }

    this.stopPing();

    if (this.ws) {
      this.ws.close(1000, "Client disconnect");
      this.ws = null;
    }

    this.currentScriptId = null;
    this.connectionId = null;
    this.roomId = null;
    this.reconnectAttempts = 0;
    this.messageQueue = [];

    wsConnectionState.update((state) => ({
      ...state,
      isConnected: false,
      isConnecting: false,
      error: null,
      reconnectAttempts: 0,
    }));
  }

  /**
   * 현재 연결 정보 조회
   */
  getConnectionInfo() {
    return {
      scriptId: this.currentScriptId,
      connectionId: this.connectionId,
      roomId: this.roomId,
      isConnected: this.isConnected(),
      reconnectAttempts: this.reconnectAttempts,
    };
  }
}

// 싱글톤 인스턴스
let websocketServiceInstance: WebSocketService | null = null;

/**
 * WebSocket 서비스 인스턴스 가져오기
 */
export function getWebSocketService(): WebSocketService {
  if (!websocketServiceInstance) {
    websocketServiceInstance = new WebSocketService();
  }
  return websocketServiceInstance;
}

/**
 * WebSocket 서비스 인스턴스 설정 (테스트용)
 */
export function setWebSocketService(service: WebSocketService): void {
  websocketServiceInstance = service;
}

// 기본 export
export const websocketService = getWebSocketService();
