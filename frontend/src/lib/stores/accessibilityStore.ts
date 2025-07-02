/**
 * 접근성 설정 및 상태 관리 스토어
 */

import { writable, derived, readable } from 'svelte/store';
import { browser } from '$app/environment';
import { 
  prefersReducedMotion, 
  prefersHighContrast, 
  prefersDarkMode
} from '../utils/accessibility';
import { 
  globalShortcutManager,
  registerCommonShortcuts
} from '../utils/keyboardNavigation';

/**
 * 접근성 설정 인터페이스
 */
export interface AccessibilitySettings {
  // 키보드 탐색
  focusRingVisible: boolean;
  keyboardNavigationEnabled: boolean;
  
  // 애니메이션 및 모션
  animationsEnabled: boolean;
  reducedMotion: boolean;
  
  // 시각적 접근성
  highContrast: boolean;
  focusIndicatorEnhanced: boolean;
  
  // 스크린 리더
  screenReaderOptimized: boolean;
  announcements: boolean;
  verboseDescriptions: boolean;
  
  // 키보드 단축키
  keyboardShortcutsEnabled: boolean;
  globalShortcutsEnabled: boolean;
  
  // 자동 기능
  autoPlayDisabled: boolean;
  autoScrollDisabled: boolean;
  
  // 디버깅 및 검사
  accessibilityDebugMode: boolean;
  showFocusOutlines: boolean;
  showARIAInfo: boolean;
}

/**
 * 시스템 접근성 기본 설정 인터페이스
 */
export interface SystemAccessibilityPreferences {
  reducedMotion: boolean;
  highContrast: boolean;
  darkMode: boolean;
  colorScheme: 'light' | 'dark' | 'auto';
}

/**
 * 기본 접근성 설정
 */
const defaultAccessibilitySettings: AccessibilitySettings = {
  focusRingVisible: true,
  keyboardNavigationEnabled: true,
  animationsEnabled: true,
  reducedMotion: false,
  highContrast: false,
  focusIndicatorEnhanced: false,
  screenReaderOptimized: false,
  announcements: true,
  verboseDescriptions: false,
  keyboardShortcutsEnabled: true,
  globalShortcutsEnabled: true,
  autoPlayDisabled: false,
  autoScrollDisabled: false,
  accessibilityDebugMode: false,
  showFocusOutlines: false,
  showARIAInfo: false
};

/**
 * 로컬 스토리지에서 설정 로드
 */
function loadAccessibilitySettings(): AccessibilitySettings {
  if (!browser) return defaultAccessibilitySettings;
  
  try {
    const stored = localStorage.getItem('accessibility-settings');
    if (stored) {
      return { ...defaultAccessibilitySettings, ...JSON.parse(stored) };
    }
  } catch (error) {
    console.warn('Failed to load accessibility settings:', error);
  }
  
  return defaultAccessibilitySettings;
}

/**
 * 로컬 스토리지에 설정 저장
 */
function saveAccessibilitySettings(settings: AccessibilitySettings): void {
  if (!browser) return;
  
  try {
    localStorage.setItem('accessibility-settings', JSON.stringify(settings));
  } catch (error) {
    console.warn('Failed to save accessibility settings:', error);
  }
}

// 접근성 설정 스토어
export const accessibilitySettings = writable<AccessibilitySettings>(
  loadAccessibilitySettings()
);

// 설정 변경 시 로컬 스토리지에 저장
accessibilitySettings.subscribe(settings => {
  saveAccessibilitySettings(settings);
});

/**
 * 시스템 접근성 기본 설정 감지 (reactive)
 */
export const systemAccessibilityPreferences = readable<SystemAccessibilityPreferences>(
  {
    reducedMotion: false,
    highContrast: false,
    darkMode: false,
    colorScheme: 'auto'
  },
  (set) => {
    if (!browser) return;

    // 미디어 쿼리 리스너 설정
    const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const highContrastQuery = window.matchMedia('(prefers-contrast: high)');
    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');

    function updatePreferences() {
      set({
        reducedMotion: reducedMotionQuery.matches,
        highContrast: highContrastQuery.matches,
        darkMode: darkModeQuery.matches,
        colorScheme: darkModeQuery.matches ? 'dark' : 'light'
      });
    }

    // 초기값 설정
    updatePreferences();

    // 변경 감지
    reducedMotionQuery.addEventListener('change', updatePreferences);
    highContrastQuery.addEventListener('change', updatePreferences);
    darkModeQuery.addEventListener('change', updatePreferences);

    // 정리 함수
    return () => {
      reducedMotionQuery.removeEventListener('change', updatePreferences);
      highContrastQuery.removeEventListener('change', updatePreferences);
      darkModeQuery.removeEventListener('change', updatePreferences);
    };
  }
);

/**
 * 통합 접근성 상태 (사용자 설정 + 시스템 설정)
 */
export const effectiveAccessibilityState = derived(
  [accessibilitySettings, systemAccessibilityPreferences],
  ([$settings, $system]) => ({
    // 사용자 설정이 우선, 시스템 설정을 기본값으로 사용
    reducedMotion: $settings.reducedMotion || $system.reducedMotion,
    highContrast: $settings.highContrast || $system.highContrast,
    animationsEnabled: $settings.animationsEnabled && !($settings.reducedMotion || $system.reducedMotion),
    
    // 기타 설정들
    focusRingVisible: $settings.focusRingVisible,
    keyboardNavigationEnabled: $settings.keyboardNavigationEnabled,
    screenReaderOptimized: $settings.screenReaderOptimized,
    announcements: $settings.announcements,
    keyboardShortcutsEnabled: $settings.keyboardShortcutsEnabled,
    
    // 디버그 설정
    debugMode: $settings.accessibilityDebugMode,
    showFocusOutlines: $settings.showFocusOutlines,
    showARIAInfo: $settings.showARIAInfo
  })
);

/**
 * 접근성 액션 함수들
 */
export const accessibilityActions = {
  /**
   * 특정 설정 업데이트
   */
  updateSetting<K extends keyof AccessibilitySettings>(
    key: K,
    value: AccessibilitySettings[K]
  ): void {
    accessibilitySettings.update(settings => ({
      ...settings,
      [key]: value
    }));
  },

  /**
   * 여러 설정 동시 업데이트
   */
  updateSettings(updates: Partial<AccessibilitySettings>): void {
    accessibilitySettings.update(settings => ({
      ...settings,
      ...updates
    }));
  },

  /**
   * 기본 설정으로 초기화
   */
  resetToDefaults(): void {
    accessibilitySettings.set(defaultAccessibilitySettings);
  },

  /**
   * 시스템 기본 설정에 맞춰 자동 조정
   */
  autoConfigureFromSystem(): void {
    const reducedMotion = prefersReducedMotion();
    const highContrast = prefersHighContrast();
    
    accessibilityActions.updateSettings({
      reducedMotion,
      highContrast,
      animationsEnabled: !reducedMotion,
      focusIndicatorEnhanced: highContrast
    });
  },

  /**
   * 키보드 단축키 토글
   */
  toggleKeyboardShortcuts(): void {
    accessibilitySettings.update(settings => {
      const enabled = !settings.keyboardShortcutsEnabled;
      
      // 전역 단축키 관리자 활성화/비활성화
      globalShortcutManager.setEnabled(enabled);
      
      return {
        ...settings,
        keyboardShortcutsEnabled: enabled
      };
    });
  },

  /**
   * 스크린 리더 모드 토글
   */
  toggleScreenReaderMode(): void {
    accessibilitySettings.update(settings => ({
      ...settings,
      screenReaderOptimized: !settings.screenReaderOptimized,
      verboseDescriptions: !settings.screenReaderOptimized,
      announcements: true // 스크린 리더 모드에서는 항상 알림 활성화
    }));
  },

  /**
   * 고대비 모드 토글
   */
  toggleHighContrast(): void {
    accessibilitySettings.update(settings => ({
      ...settings,
      highContrast: !settings.highContrast,
      focusIndicatorEnhanced: !settings.highContrast
    }));
  },

  /**
   * 애니메이션 토글
   */
  toggleAnimations(): void {
    accessibilitySettings.update(settings => ({
      ...settings,
      animationsEnabled: !settings.animationsEnabled,
      reducedMotion: settings.animationsEnabled // 애니메이션 끄면 reduced motion 켜기
    }));
  },

  /**
   * 디버그 모드 토글
   */
  toggleDebugMode(): void {
    accessibilitySettings.update(settings => ({
      ...settings,
      accessibilityDebugMode: !settings.accessibilityDebugMode,
      showFocusOutlines: !settings.accessibilityDebugMode,
      showARIAInfo: !settings.accessibilityDebugMode
    }));
  }
};

/**
 * 접근성 초기화 (앱 시작 시 호출)
 */
export function initializeAccessibility(): void {
  if (!browser) return;

  // 시스템 설정에 따른 자동 구성
  accessibilityActions.autoConfigureFromSystem();

  // 공통 키보드 단축키 등록
  registerCommonShortcuts();

  // 포커스 가시성 모니터링
  let isUsingKeyboard = false;

  // 키보드 사용 감지
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      isUsingKeyboard = true;
      document.body.classList.add('using-keyboard');
    }
  });

  // 마우스 사용 감지
  document.addEventListener('mousedown', () => {
    isUsingKeyboard = false;
    document.body.classList.remove('using-keyboard');
  });

  // 접근성 설정에 따른 CSS 클래스 관리
  effectiveAccessibilityState.subscribe(state => {
    const body = document.body;
    
    // 클래스 토글
    body.classList.toggle('reduced-motion', state.reducedMotion);
    body.classList.toggle('high-contrast', state.highContrast);
    body.classList.toggle('screen-reader-optimized', state.screenReaderOptimized);
    body.classList.toggle('accessibility-debug', state.debugMode);
    body.classList.toggle('show-focus-outlines', state.showFocusOutlines);
    
    // CSS 커스텀 속성 설정
    body.style.setProperty('--animation-duration', state.animationsEnabled ? '200ms' : '0ms');
    body.style.setProperty('--focus-ring-width', state.focusRingVisible ? '2px' : '0px');
  });

  console.log('✅ Accessibility system initialized');
}

/**
 * 접근성 위반 사항 감지 및 보고
 */
export const accessibilityChecker = {
  /**
   * 페이지의 기본 접근성 검사 수행
   */
  performBasicCheck(): void {
    if (!browser) return;

    const issues: string[] = [];

    // 이미지 alt 텍스트 확인
    const images = document.querySelectorAll('img:not([alt])');
    if (images.length > 0) {
      issues.push(`${images.length}개의 이미지에 alt 텍스트가 없습니다.`);
    }

    // 버튼 레이블 확인
    const unlabeledButtons = document.querySelectorAll('button:not([aria-label]):not([aria-labelledby])');
    const emptyButtons = Array.from(unlabeledButtons).filter(btn => !btn.textContent?.trim());
    if (emptyButtons.length > 0) {
      issues.push(`${emptyButtons.length}개의 버튼에 접근 가능한 레이블이 없습니다.`);
    }

    // 링크 텍스트 확인
    const vagueLinkTexts = ['여기', 'click here', '더보기', '자세히'];
    const vagueLinks = Array.from(document.querySelectorAll('a')).filter(link => {
      const text = link.textContent?.trim().toLowerCase();
      return text && vagueLinkTexts.some(vague => text.includes(vague));
    });
    if (vagueLinks.length > 0) {
      issues.push(`${vagueLinks.length}개의 링크가 모호한 텍스트를 사용합니다.`);
    }

    // 디버그 모드에서만 콘솔에 출력
    const unsubscribe = accessibilitySettings.subscribe(settings => {
      if (settings.accessibilityDebugMode && issues.length > 0) {
        console.warn('🔍 접근성 문제 발견:', issues);
      }
    });
    unsubscribe();
  },

  /**
   * 실시간 접근성 모니터링 시작
   */
  startMonitoring(): () => void {
    if (!browser) return () => {};

    // DOM 변경 감지하여 접근성 재검사
    const observer = new MutationObserver(() => {
      this.performBasicCheck();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['aria-label', 'aria-labelledby', 'alt', 'role']
    });

    return () => observer.disconnect();
  }
}; 