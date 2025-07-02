/**
 * 인증 관련 타입 정의
 */

// 인증 제공자 타입
export type AuthProvider = 'google' | 'apple' | 'local';

// 일본어 레벨 타입
export type JapaneseLevel = 'beginner' | 'elementary' | 'intermediate' | 'advanced' | 'proficient';

// 사용자 인터페이스
export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  provider: AuthProvider;
  japanese_level: JapaneseLevel;
  created_at: string;
  updated_at: string;
}

// 인증 상태 인터페이스
export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  token: string | null;
}

// OAuth 로그인 요청
export interface OAuthLoginRequest {
  provider: AuthProvider;
  access_token: string;
  id_token?: string;
}

// 인증 응답
export interface AuthResponse {
  user: User;
  access_token: string;
  token_type: string;
  expires_in: number;
}

// 사용자 프로필
export interface UserProfile {
  name: string;
  avatar_url?: string;
  japanese_level: JapaneseLevel;
  bio?: string;
  learning_goals?: string[];
  daily_goal_minutes?: number;
}

// 프로필 업데이트 요청
export interface UpdateProfile {
  name?: string;
  japanese_level?: JapaneseLevel;
  bio?: string;
  learning_goals?: string[];
  daily_goal_minutes?: number;
}

// 사용자 통계
export interface UserStats {
  total_listening_minutes: number;
  total_words_saved: number;
  current_streak_days: number;
  level_progress_percentage: number;
  total_scripts_completed: number;
  favorite_content_types: string[];
}

// 사용자 설정
export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: 'ko' | 'en' | 'ja';
  playback_speed: number;
  auto_pause_on_unknown_word: boolean;
  show_furigana: boolean;
  font_size: 'small' | 'medium' | 'large';
  notifications_enabled: boolean;
  email_reminders: boolean;
}

// 인증 이벤트 타입
export interface AuthEvent {
  type: 'login' | 'logout' | 'profile_update' | 'error';
  user?: User;
  error?: string;
}

// OAuth 제공자 설정
export interface OAuthProviderConfig {
  clientId: string;
  redirectUri: string;
  scope: string[];
}

// Google OAuth 응답
export interface GoogleOAuthResponse {
  access_token: string;
  id_token: string;
  scope: string;
  token_type: string;
  expires_in: number;
}

// Apple OAuth 응답
export interface AppleOAuthResponse {
  access_token: string;
  id_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
} 