/**
 * 인증 API 서비스
 * OAuth 로그인, 프로필 관리, 사용자 통계 등의 API를 처리합니다.
 */

import { getApiClient } from './client';
import type {
  AuthResponse,
  OAuthLoginRequest,
  User,
  UserProfile,
  UpdateProfile,
  UserStats,
  UserPreferences,
  AuthProvider
} from '../types/auth';

export class AuthApiService {
  private apiClient = getApiClient();

  /**
   * OAuth 소셜 로그인
   */
  async oauthLogin(request: OAuthLoginRequest): Promise<AuthResponse> {
    try {
      const response = await this.apiClient.post<AuthResponse>(
        '/auth/oauth/login',
        request,
        { skipAuth: true }
      );

      // 성공 시 토큰 저장
      if (response.access_token) {
        this.apiClient.setAuthTokens(response.access_token);
      }

      return response;
    } catch (error) {
      console.error('OAuth login failed:', error);
      throw error;
    }
  }

  /**
   * 로그아웃
   */
  async logout(): Promise<void> {
    try {
      await this.apiClient.post('/auth/logout');
    } catch (error) {
      console.error('Logout request failed:', error);
      // 로그아웃은 로컬에서도 처리되어야 함
    } finally {
      this.apiClient.clearAuthTokens();
    }
  }

  /**
   * 현재 사용자 정보 조회
   */
  async getCurrentUser(): Promise<User> {
    return this.apiClient.get<User>('/auth/me');
  }

  /**
   * 토큰 갱신
   */
  async refreshToken(): Promise<AuthResponse> {
    return this.apiClient.post<AuthResponse>('/auth/refresh');
  }

  /**
   * 사용자 프로필 조회
   */
  async getUserProfile(): Promise<UserProfile> {
    return this.apiClient.get<UserProfile>('/users/profile');
  }

  /**
   * 사용자 프로필 업데이트
   */
  async updateUserProfile(profile: UpdateProfile): Promise<UserProfile> {
    return this.apiClient.put<UserProfile>('/users/profile', profile);
  }

  /**
   * 사용자 학습 통계 조회
   */
  async getUserStats(): Promise<UserStats> {
    return this.apiClient.get<UserStats>('/users/stats');
  }

  /**
   * 사용자 설정 조회
   */
  async getUserPreferences(): Promise<UserPreferences> {
    return this.apiClient.get<UserPreferences>('/users/preferences');
  }

  /**
   * 사용자 설정 업데이트
   */
  async updateUserPreferences(preferences: Partial<UserPreferences>): Promise<UserPreferences> {
    return this.apiClient.put<UserPreferences>('/users/preferences', preferences);
  }

  /**
   * 계정 삭제
   */
  async deleteAccount(): Promise<void> {
    await this.apiClient.delete('/users/account');
    this.apiClient.clearAuthTokens();
  }
}

// OAuth 제공자별 설정
export const oauthConfigs = {
  google: {
    clientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || '',
    redirectUri: `${window.location.origin}/auth/callback/google`,
    scope: ['openid', 'email', 'profile']
  },
  apple: {
    clientId: import.meta.env.VITE_APPLE_CLIENT_ID || '',
    redirectUri: `${window.location.origin}/auth/callback/apple`,
    scope: ['name', 'email']
  }
};

/**
 * Google OAuth 로그인 초기화
 */
export function initGoogleOAuth(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (typeof window === 'undefined') {
      reject(new Error('Google OAuth는 브라우저 환경에서만 사용 가능합니다'));
      return;
    }

    // Google OAuth SDK 로드
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.onload = () => {
      console.log('Google OAuth SDK loaded');
      resolve();
    };
    script.onerror = () => {
      reject(new Error('Google OAuth SDK 로드에 실패했습니다'));
    };
    document.head.appendChild(script);
  });
}

/**
 * Google OAuth 로그인 실행
 */
export function loginWithGoogle(): Promise<OAuthLoginRequest> {
  return new Promise((resolve, reject) => {
    if (!window.google) {
      reject(new Error('Google OAuth SDK가 로드되지 않았습니다'));
      return;
    }

    const config = oauthConfigs.google;
    if (!config.clientId) {
      reject(new Error('Google Client ID가 설정되지 않았습니다'));
      return;
    }

    window.google.accounts.oauth2.initCodeClient({
      client_id: config.clientId,
      scope: config.scope.join(' '),
      ux_mode: 'popup',
      callback: (response: any) => {
        if (response.error) {
          reject(new Error(`Google OAuth 에러: ${response.error}`));
          return;
        }

        resolve({
          provider: 'google',
          access_token: response.access_token,
          id_token: response.id_token
        });
      }
    }).requestAccessToken();
  });
}

/**
 * Apple OAuth 로그인 실행
 */
export function loginWithApple(): Promise<OAuthLoginRequest> {
  return new Promise((resolve, reject) => {
    if (!window.AppleID) {
      reject(new Error('Apple OAuth SDK가 로드되지 않았습니다'));
      return;
    }

    const config = oauthConfigs.apple;
    if (!config.clientId) {
      reject(new Error('Apple Client ID가 설정되지 않았습니다'));
      return;
    }

    window.AppleID.auth.init({
      clientId: config.clientId,
      scope: config.scope.join(' '),
      redirectURI: config.redirectUri,
      usePopup: true
    });

    window.AppleID.auth.signIn().then((response: any) => {
      resolve({
        provider: 'apple',
        access_token: response.authorization.code,
        id_token: response.authorization.id_token
      });
    }).catch((error: any) => {
      reject(new Error(`Apple OAuth 에러: ${error.error}`));
    });
  });
}

// 타입 확장 (글로벌 객체)
declare global {
  interface Window {
    google?: {
      accounts: {
        oauth2: {
          initCodeClient: (config: any) => { requestAccessToken: () => void };
        };
      };
    };
    AppleID?: {
      auth: {
        init: (config: any) => void;
        signIn: () => Promise<any>;
      };
    };
  }
}

// 싱글톤 인스턴스 생성
export const authApi = new AuthApiService(); 