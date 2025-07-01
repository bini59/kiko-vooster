/**
 * Base API 클라이언트
 *
 * 모든 백엔드 API 호출의 기본이 되는 클라이언트 클래스
 * 인증, 에러 처리, 재시도 로직을 포함합니다.
 */

import { browser } from "$app/environment";
import { goto } from "$app/navigation";
import { get } from "svelte/store";

// API 에러 타입 정의
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: any
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class NetworkError extends Error {
  constructor(message: string = "Network connection failed") {
    super(message);
    this.name = "NetworkError";
  }
}

export class AuthError extends Error {
  constructor(message: string = "Authentication failed") {
    super(message);
    this.name = "AuthError";
  }
}

// API 응답 인터페이스
interface ApiResponse<T = any> {
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  meta?: {
    total?: number;
    page?: number;
    limit?: number;
  };
}

// 재시도 설정
interface RetryConfig {
  maxAttempts: number;
  backoffMs: number;
  retryCondition: (error: Error) => boolean;
}

// 요청 옵션
interface RequestOptions extends RequestInit {
  timeout?: number;
  retry?: Partial<RetryConfig>;
  skipAuth?: boolean;
  skipErrorHandling?: boolean;
}

export class ApiClient {
  private baseURL: string;
  private authToken: string | null = null;
  private refreshToken: string | null = null;
  private defaultTimeout = 10000; // 10초

  // 기본 재시도 설정
  private defaultRetryConfig: RetryConfig = {
    maxAttempts: 3,
    backoffMs: 1000,
    retryCondition: (error: Error) => {
      // 네트워크 에러와 5xx 서버 에러에 대해서만 재시도
      return (
        error instanceof NetworkError ||
        (error instanceof ApiError && error.status >= 500)
      );
    },
  };

  constructor(baseURL?: string) {
    this.baseURL =
      baseURL ||
      (browser
        ? window.location.origin.replace("5173", "8000") + "/api/v1"
        : "http://localhost:8000/api/v1");

    // 로컬 스토리지에서 토큰 복원
    if (browser) {
      this.authToken = localStorage.getItem("auth_token");
      this.refreshToken = localStorage.getItem("refresh_token");
    }
  }

  /**
   * 인증 토큰 설정
   */
  setAuthTokens(accessToken: string, refreshToken?: string) {
    this.authToken = accessToken;
    if (refreshToken) {
      this.refreshToken = refreshToken;
    }

    if (browser) {
      localStorage.setItem("auth_token", accessToken);
      if (refreshToken) {
        localStorage.setItem("refresh_token", refreshToken);
      }
    }
  }

  /**
   * 토큰 제거 (로그아웃)
   */
  clearAuthTokens() {
    this.authToken = null;
    this.refreshToken = null;

    if (browser) {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("refresh_token");
    }
  }

  /**
   * 현재 인증 상태 확인
   */
  isAuthenticated(): boolean {
    return !!this.authToken;
  }

  /**
   * 기본 헤더 구성
   */
  private getDefaultHeaders(skipAuth = false): HeadersInit {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      Accept: "application/json",
    };

    if (!skipAuth && this.authToken) {
      headers["Authorization"] = `Bearer ${this.authToken}`;
    }

    return headers;
  }

  /**
   * 요청 타임아웃 처리
   */
  private createTimeoutController(timeoutMs: number): AbortController {
    const controller = new AbortController();
    setTimeout(() => controller.abort(), timeoutMs);
    return controller;
  }

  /**
   * 토큰 갱신 시도
   */
  private async refreshAuthToken(): Promise<boolean> {
    if (!this.refreshToken) {
      return false;
    }

    try {
      const response = await fetch(`${this.baseURL}/auth/refresh`, {
        method: "POST",
        headers: this.getDefaultHeaders(true),
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      });

      if (response.ok) {
        const data = await response.json();
        this.setAuthTokens(data.access_token, data.refresh_token);
        return true;
      }
    } catch (error) {
      console.error("Token refresh failed:", error);
    }

    return false;
  }

  /**
   * 인증 에러 처리
   */
  private async handleAuthError(): Promise<void> {
    // 토큰 갱신 시도
    const refreshed = await this.refreshAuthToken();

    if (!refreshed) {
      // 갱신 실패 시 로그아웃 처리
      this.clearAuthTokens();

      if (browser) {
        // 로그인 페이지로 리다이렉트
        goto(
          "/auth/login?redirect=" + encodeURIComponent(window.location.pathname)
        );
      }

      throw new AuthError("Authentication session expired");
    }
  }

  /**
   * 응답을 파싱하고 에러 처리
   */
  private async parseResponse<T>(response: Response): Promise<T> {
    const contentType = response.headers.get("content-type");

    let responseData: any;
    if (contentType?.includes("application/json")) {
      responseData = await response.json();
    } else {
      responseData = await response.text();
    }

    if (!response.ok) {
      // 인증 에러 처리
      if (response.status === 401) {
        await this.handleAuthError();
        throw new AuthError(responseData?.message || "Authentication failed");
      }

      // API 에러 생성
      const errorMessage =
        responseData?.detail ||
        responseData?.message ||
        `HTTP ${response.status}`;
      const errorCode = responseData?.code || response.status.toString();

      throw new ApiError(
        errorMessage,
        response.status,
        errorCode,
        responseData
      );
    }

    // 성공 응답 처리
    if (
      responseData &&
      typeof responseData === "object" &&
      "data" in responseData
    ) {
      return responseData.data;
    }

    return responseData;
  }

  /**
   * 재시도 로직이 포함된 fetch 실행
   */
  private async fetchWithRetry<T>(
    url: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const retryConfig = { ...this.defaultRetryConfig, ...options.retry };
    const timeout = options.timeout || this.defaultTimeout;

    let lastError: Error;

    for (let attempt = 1; attempt <= retryConfig.maxAttempts; attempt++) {
      try {
        const controller = this.createTimeoutController(timeout);

        const response = await fetch(url, {
          ...options,
          signal: controller.signal,
          headers: {
            ...this.getDefaultHeaders(options.skipAuth),
            ...options.headers,
          },
        });

        return await this.parseResponse<T>(response);
      } catch (error) {
        lastError = error as Error;

        // AbortError는 타임아웃으로 간주
        if (lastError.name === "AbortError") {
          lastError = new NetworkError("Request timeout");
        }

        // 네트워크 에러로 변환
        if (
          lastError instanceof TypeError &&
          lastError.message.includes("fetch")
        ) {
          lastError = new NetworkError("Network connection failed");
        }

        // 재시도 조건 확인
        const shouldRetry =
          attempt < retryConfig.maxAttempts &&
          retryConfig.retryCondition(lastError);

        if (!shouldRetry) {
          break;
        }

        // 백오프 대기
        const backoffMs = retryConfig.backoffMs * Math.pow(2, attempt - 1);
        await new Promise((resolve) => setTimeout(resolve, backoffMs));

        console.warn(
          `API request failed, retrying (${attempt}/${retryConfig.maxAttempts}):`,
          lastError
        );
      }
    }

    throw lastError!;
  }

  /**
   * GET 요청
   */
  async get<T = any>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    return this.fetchWithRetry<T>(url, {
      ...options,
      method: "GET",
    });
  }

  /**
   * POST 요청
   */
  async post<T = any>(
    endpoint: string,
    data?: any,
    options: RequestOptions = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    return this.fetchWithRetry<T>(url, {
      ...options,
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * PUT 요청
   */
  async put<T = any>(
    endpoint: string,
    data?: any,
    options: RequestOptions = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    return this.fetchWithRetry<T>(url, {
      ...options,
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * DELETE 요청
   */
  async delete<T = any>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    return this.fetchWithRetry<T>(url, {
      ...options,
      method: "DELETE",
    });
  }

  /**
   * PATCH 요청
   */
  async patch<T = any>(
    endpoint: string,
    data?: any,
    options: RequestOptions = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    return this.fetchWithRetry<T>(url, {
      ...options,
      method: "PATCH",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * 일반적인 요청 메서드 (고급 사용)
   */
  async request<T = any>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    return this.fetchWithRetry<T>(url, options);
  }
}

// 싱글톤 인스턴스
let apiClientInstance: ApiClient | null = null;

/**
 * API 클라이언트 인스턴스 가져오기
 */
export function getApiClient(): ApiClient {
  if (!apiClientInstance) {
    apiClientInstance = new ApiClient();
  }
  return apiClientInstance;
}

/**
 * API 클라이언트 인스턴스 설정 (테스트용)
 */
export function setApiClient(client: ApiClient): void {
  apiClientInstance = client;
}
