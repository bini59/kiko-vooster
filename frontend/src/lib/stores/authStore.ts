/**
 * 인증 상태 관리 스토어
 */

import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import type {
  AuthState,
  User,
  UserProfile,
  UserStats,
  UserPreferences,
  AuthProvider,
  OAuthLoginRequest
} from '../types/auth';
import { authApi, loginWithGoogle, loginWithApple, initGoogleOAuth } from '../api/auth';
import { logger, logError, logUserAction } from '../utils/logger';

// 초기 인증 상태
const initialAuthState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  token: null
};

// 초기 사용자 프로필
const initialUserProfile: UserProfile = {
  name: '',
  japanese_level: 'beginner',
  bio: '',
  learning_goals: [],
  daily_goal_minutes: 30
};

// 초기 사용자 통계
const initialUserStats: UserStats = {
  total_listening_minutes: 0,
  total_words_saved: 0,
  current_streak_days: 0,
  level_progress_percentage: 0,
  total_scripts_completed: 0,
  favorite_content_types: []
};

// 초기 사용자 설정
const initialUserPreferences: UserPreferences = {
  theme: 'auto',
  language: 'ko',
  playback_speed: 1.0,
  auto_pause_on_unknown_word: false,
  show_furigana: true,
  font_size: 'medium',
  notifications_enabled: true,
  email_reminders: false
};

// 스토어 생성
export const authState = writable<AuthState>(initialAuthState);
export const userProfile = writable<UserProfile>(initialUserProfile);
export const userStats = writable<UserStats>(initialUserStats);
export const userPreferences = writable<UserPreferences>(initialUserPreferences);

// 유도 스토어 (computed 상태)
export const isLoggedIn = derived(
  authState,
  ($auth) => $auth.isAuthenticated && !!$auth.user
);

export const currentUser = derived(
  authState,
  ($auth) => $auth.user
);

export const hasCompletedProfile = derived(
  userProfile,
  ($profile) => !!$profile.name && $profile.japanese_level !== 'beginner'
);

export const learningProgress = derived(
  userStats,
  ($stats) => ({
    dailyProgress: Math.min(100, ($stats.total_listening_minutes % 30) * 100 / 30),
    weeklyStreak: $stats.current_streak_days,
    totalWords: $stats.total_words_saved,
    totalMinutes: $stats.total_listening_minutes
  })
);

export const isLoading = derived(
  authState,
  ($auth) => $auth.isLoading
);

export const authError = derived(
  authState,
  ($auth) => $auth.error
);

// 액션 함수들
export const authActions = {
  // 로딩 상태 설정
  setLoading: (isLoading: boolean) => {
    authState.update(state => ({
      ...state,
      isLoading,
      error: isLoading ? null : state.error
    }));
  },

  // 에러 설정
  setError: (error: string | null) => {
    authState.update(state => ({
      ...state,
      error,
      isLoading: false
    }));
  },

  // 로그인 성공 처리
  setUser: (user: User, token: string) => {
    authState.update(state => ({
      ...state,
      user,
      token,
      isAuthenticated: true,
      isLoading: false,
      error: null
    }));

    if (browser) {
      localStorage.setItem('auth_token', token);
    }
  },

  // 로그아웃 처리
  logout: async () => {
    try {
      await authApi.logout();
    } catch (error) {
      logError(error, 'Logout API call failed');
    } finally {
      // 로컬 상태 클리어
      authState.set(initialAuthState);
      userProfile.set(initialUserProfile);
      userStats.set(initialUserStats);
      userPreferences.set(initialUserPreferences);

      if (browser) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('refresh_token');
      }
    }
  },

  // Google 로그인
  loginWithGoogle: async () => {
    authActions.setLoading(true);
    authActions.setError(null);

    try {
      // Google OAuth SDK 초기화
      await initGoogleOAuth();
      
      // Google 로그인 실행
      const oauthRequest = await loginWithGoogle();
      
      // 백엔드에 OAuth 토큰 전송
      const response = await authApi.oauthLogin(oauthRequest);
      
      // 인증 상태 업데이트
      authActions.setUser(response.user, response.access_token);
      
      // 사용자 데이터 로드
      await authActions.loadUserData();
      
      logger.info('✅ Google 로그인 성공');
      logUserAction('login', { provider: 'google' });
    } catch (error: any) {
      logError(error, '❌ Google 로그인 실패');
      authActions.setError(error.message || 'Google 로그인에 실패했습니다');
    }
  },

  // Apple 로그인
  loginWithApple: async () => {
    authActions.setLoading(true);
    authActions.setError(null);

    try {
      // Apple 로그인 실행
      const oauthRequest = await loginWithApple();
      
      // 백엔드에 OAuth 토큰 전송
      const response = await authApi.oauthLogin(oauthRequest);
      
      // 인증 상태 업데이트
      authActions.setUser(response.user, response.access_token);
      
      // 사용자 데이터 로드
      await authActions.loadUserData();
      
      logger.info('✅ Apple 로그인 성공');
      logUserAction('login', { provider: 'apple' });
    } catch (error: any) {
      logError(error, '❌ Apple 로그인 실패');
      authActions.setError(error.message || 'Apple 로그인에 실패했습니다');
    }
  },

  // 사용자 데이터 로드
  loadUserData: async () => {
    try {
      const [profile, stats, preferences] = await Promise.all([
        authApi.getUserProfile(),
        authApi.getUserStats(),
        authApi.getUserPreferences()
      ]);

      userProfile.set(profile);
      userStats.set(stats);
      userPreferences.set(preferences);
    } catch (error: any) {
      logError(error, '사용자 데이터 로드 실패');
      throw error;
    }
  },

  // 프로필 업데이트
  updateProfile: async (updates: Partial<UserProfile>) => {
    authActions.setLoading(true);
    
    try {
      const updatedProfile = await authApi.updateUserProfile(updates);
      userProfile.set(updatedProfile);
      
      logger.info('✅ 프로필 업데이트 성공');
      logUserAction('profile_update', { fields: Object.keys(updates) });
    } catch (error: any) {
      logError(error, '❌ 프로필 업데이트 실패');
      authActions.setError('프로필 업데이트에 실패했습니다');
      throw error;
    } finally {
      authActions.setLoading(false);
    }
  },

  // 설정 업데이트
  updatePreferences: async (updates: Partial<UserPreferences>) => {
    try {
      const updatedPreferences = await authApi.updateUserPreferences(updates);
      userPreferences.set(updatedPreferences);
      
      logger.info('✅ 설정 업데이트 성공');
      logUserAction('preferences_update', { settings: Object.keys(updates) });
    } catch (error: any) {
      logError(error, '❌ 설정 업데이트 실패');
      authActions.setError('설정 업데이트에 실패했습니다');
      throw error;
    }
  },

  // 통계 새로고침
  refreshStats: async () => {
    try {
      const stats = await authApi.getUserStats();
      userStats.set(stats);
    } catch (error: any) {
      logError(error, '❌ 통계 새로고침 실패');
    }
  },

  // 현재 사용자 정보 새로고침
  refreshUser: async () => {
    try {
      const user = await authApi.getCurrentUser();
      authState.update(state => ({
        ...state,
        user
      }));
    } catch (error: any) {
      logError(error, '❌ 사용자 정보 새로고침 실패');
      // 토큰이 만료된 경우 로그아웃
      if (error.status === 401) {
        await authActions.logout();
      }
    }
  },

  // 계정 삭제
  deleteAccount: async () => {
    authActions.setLoading(true);
    
    try {
      await authApi.deleteAccount();
      await authActions.logout();
      
      logger.info('✅ 계정 삭제 완료');
      logUserAction('account_delete');
    } catch (error: any) {
      logError(error, '❌ 계정 삭제 실패');
      authActions.setError('계정 삭제에 실패했습니다');
      throw error;
    } finally {
      authActions.setLoading(false);
    }
  }
};

// 설정 관련 액션들
export const preferencesActions = {
  // 테마 변경
  setTheme: async (theme: UserPreferences['theme']) => {
    await authActions.updatePreferences({ theme });
  },

  // 언어 변경
  setLanguage: async (language: UserPreferences['language']) => {
    await authActions.updatePreferences({ language });
  },

  // 재생 속도 변경
  setPlaybackSpeed: async (playback_speed: number) => {
    await authActions.updatePreferences({ playback_speed });
  },

  // 폰트 크기 변경
  setFontSize: async (font_size: UserPreferences['font_size']) => {
    await authActions.updatePreferences({ font_size });
  },

  // 후리가나 표시 토글
  toggleFurigana: async () => {
    const currentPreferences = userPreferences;
    const current = await new Promise<UserPreferences>(resolve => {
      const unsubscribe = currentPreferences.subscribe(value => {
        resolve(value);
        unsubscribe();
      });
    });
    
    await authActions.updatePreferences({ 
      show_furigana: !current.show_furigana 
    });
  },

  // 알림 토글
  toggleNotifications: async () => {
    const currentPreferences = userPreferences;
    const current = await new Promise<UserPreferences>(resolve => {
      const unsubscribe = currentPreferences.subscribe(value => {
        resolve(value);
        unsubscribe();
      });
    });
    
    await authActions.updatePreferences({ 
      notifications_enabled: !current.notifications_enabled 
    });
  },

  // 개별 설정 업데이트
  updateSetting: async (key: keyof UserPreferences, value: any) => {
    await authActions.updatePreferences({ [key]: value });
  },

  // 전체 설정 저장
  savePreferences: async (preferences: UserPreferences) => {
    await authActions.updatePreferences(preferences);
  },

  // 기본값으로 초기화
  resetToDefaults: async () => {
    const defaultPreferences: UserPreferences = {
      theme: 'auto',
      language: 'ko',
      playback_speed: 1.0,
      auto_pause_on_unknown_word: false,
      show_furigana: true,
      font_size: 'medium',
      notifications_enabled: true,
      email_reminders: false
    };
    await authActions.updatePreferences(defaultPreferences);
  },

  // 설정 로드
  loadPreferences: async () => {
    try {
      const preferences = await authApi.getUserPreferences();
      userPreferences.set(preferences);
    } catch (error: any) {
      logError(error, '설정 로드 실패');
      throw error;
    }
  }
};

// 로컬 스토리지에서 초기 상태 복원 (authActions 정의 후)
if (browser) {
  const savedToken = localStorage.getItem('auth_token');
  if (savedToken) {
    authState.update(state => ({
      ...state,
      token: savedToken,
      isAuthenticated: true
    }));
    
    // 저장된 토큰으로 사용자 정보 자동 로드
    authActions.loadUserData().catch(() => {
      // 토큰이 유효하지 않은 경우 클리어
      authActions.logout();
    });
  }
} 