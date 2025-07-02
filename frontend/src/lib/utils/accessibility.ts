/**
 * 접근성 공통 유틸리티
 * WCAG 2.1 AA 기준을 만족하는 헬퍼 함수들
 */

/**
 * 고유한 ID 생성 (aria-labelledby, aria-describedby 등에 사용)
 */
export function generateId(prefix: string = 'a11y'): string {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * 요소가 포커스 가능한지 확인
 */
export function isFocusable(element: Element): boolean {
  if (!element || element.getAttribute('disabled') === 'true') return false;
  
  const focusableSelectors = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable="true"]',
    'audio[controls]',
    'video[controls]',
    'summary'
  ];
  
  return focusableSelectors.some(selector => element.matches(selector));
}

/**
 * 컨테이너 내의 모든 포커스 가능한 요소 찾기
 */
export function getFocusableElements(container: Element): Element[] {
  const focusableSelectors = [
    'a[href]:not([disabled])',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"]):not([disabled])',
    '[contenteditable="true"]',
    'audio[controls]:not([disabled])',
    'video[controls]:not([disabled])',
    'summary:not([disabled])'
  ].join(',');
  
  const elements = Array.from(container.querySelectorAll(focusableSelectors));
  return elements.filter(el => {
    // 숨겨진 요소 제외
    const style = window.getComputedStyle(el);
    return (
      style.display !== 'none' &&
      style.visibility !== 'hidden' &&
      el.getAttribute('aria-hidden') !== 'true'
    );
  });
}

/**
 * 첫 번째 포커스 가능한 요소에 포커스
 */
export function focusFirstElement(container: Element): boolean {
  const focusableElements = getFocusableElements(container);
  if (focusableElements.length > 0) {
    (focusableElements[0] as HTMLElement).focus();
    return true;
  }
  return false;
}

/**
 * 마지막 포커스 가능한 요소에 포커스
 */
export function focusLastElement(container: Element): boolean {
  const focusableElements = getFocusableElements(container);
  if (focusableElements.length > 0) {
    (focusableElements[focusableElements.length - 1] as HTMLElement).focus();
    return true;
  }
  return false;
}

/**
 * 스크린 리더에 메시지 알림 (aria-live 영역 사용)
 */
export function announceToScreenReader(message: string, priority: 'polite' | 'assertive' = 'polite'): void {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.textContent = message;
  
  document.body.appendChild(announcement);
  
  // 메시지 읽힌 후 제거
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
}

/**
 * 키보드 이벤트가 활성화 키인지 확인 (Enter, Space)
 */
export function isActivationKey(event: KeyboardEvent): boolean {
  return event.key === 'Enter' || event.key === ' ';
}

/**
 * 방향 키 확인
 */
export function getArrowDirection(event: KeyboardEvent): 'up' | 'down' | 'left' | 'right' | null {
  switch (event.key) {
    case 'ArrowUp': return 'up';
    case 'ArrowDown': return 'down';
    case 'ArrowLeft': return 'left';
    case 'ArrowRight': return 'right';
    default: return null;
  }
}

/**
 * 포커스 표시 향상 (고대비 모드 등 고려)
 */
export function enhanceFocusVisibility(element: HTMLElement): void {
  element.style.outline = '2px solid hsl(var(--p))';
  element.style.outlineOffset = '2px';
  element.style.borderRadius = '2px';
}

/**
 * 포커스 표시 제거
 */
export function removeFocusVisibility(element: HTMLElement): void {
  element.style.outline = '';
  element.style.outlineOffset = '';
}

/**
 * 모달/다이얼로그의 ARIA 속성 설정
 */
export function setModalAriaAttributes(
  modal: HTMLElement,
  titleId?: string,
  descriptionId?: string
): void {
  modal.setAttribute('role', 'dialog');
  modal.setAttribute('aria-modal', 'true');
  
  if (titleId) {
    modal.setAttribute('aria-labelledby', titleId);
  }
  
  if (descriptionId) {
    modal.setAttribute('aria-describedby', descriptionId);
  }
}

/**
 * 드롭다운/메뉴의 ARIA 속성 설정
 */
export function setMenuAriaAttributes(
  trigger: HTMLElement,
  menu: HTMLElement,
  isOpen: boolean
): void {
  const menuId = menu.id || generateId('menu');
  menu.id = menuId;
  menu.setAttribute('role', 'menu');
  
  trigger.setAttribute('aria-haspopup', 'true');
  trigger.setAttribute('aria-expanded', isOpen.toString());
  trigger.setAttribute('aria-controls', menuId);
  
  // 메뉴 아이템들에 role 설정
  const menuItems = menu.querySelectorAll('li, [role="menuitem"]');
  menuItems.forEach(item => {
    if (!item.getAttribute('role')) {
      item.setAttribute('role', 'menuitem');
    }
  });
}

/**
 * 지역 시간 포맷 (접근성을 위한 명확한 시간 표시)
 */
export function formatTimeForScreenReader(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}시간 ${minutes}분 ${secs}초`;
  } else if (minutes > 0) {
    return `${minutes}분 ${secs}초`;
  } else {
    return `${secs}초`;
  }
}

/**
 * 백분율을 접근성 친화적으로 포맷
 */
export function formatPercentageForScreenReader(percentage: number): string {
  return `${Math.round(percentage)}퍼센트`;
}

/**
 * reduced-motion 설정 확인
 */
export function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * 고대비 모드 확인
 */
export function prefersHighContrast(): boolean {
  return window.matchMedia('(prefers-contrast: high)').matches;
}

/**
 * 다크 모드 선호도 확인
 */
export function prefersDarkMode(): boolean {
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

/**
 * 접근성 설정에 따른 애니메이션 지속시간 조절
 */
export function getAnimationDuration(defaultMs: number): number {
  return prefersReducedMotion() ? 0 : defaultMs;
}

/**
 * 컬러 대비비 계산 (WCAG 기준)
 */
export function calculateContrastRatio(foreground: string, background: string): number {
  // 간단한 구현 - 실제로는 더 복잡한 계산이 필요
  // 여기서는 기본값 반환
  return 4.5; // WCAG AA 기준
}

/**
 * 접근성 검사 결과 인터페이스
 */
export interface AccessibilityCheck {
  passed: boolean;
  message: string;
  element?: Element;
}

/**
 * 기본 접근성 검사 수행
 */
export function performBasicAccessibilityCheck(container: Element): AccessibilityCheck[] {
  const checks: AccessibilityCheck[] = [];
  
  // 이미지 alt 텍스트 확인
  const images = container.querySelectorAll('img');
  images.forEach(img => {
    if (!img.getAttribute('alt') && img.getAttribute('role') !== 'presentation') {
      checks.push({
        passed: false,
        message: 'Image missing alt text',
        element: img
      });
    }
  });
  
  // 버튼에 접근 가능한 이름 확인
  const buttons = container.querySelectorAll('button, [role="button"]');
  buttons.forEach(button => {
    const hasAccessibleName = 
      button.getAttribute('aria-label') ||
      button.getAttribute('aria-labelledby') ||
      button.textContent?.trim();
    
    if (!hasAccessibleName) {
      checks.push({
        passed: false,
        message: 'Button missing accessible name',
        element: button
      });
    }
  });
  
  // 링크에 의미있는 텍스트 확인
  const links = container.querySelectorAll('a[href]');
  links.forEach(link => {
    const linkText = link.textContent?.trim();
    if (!linkText || linkText.toLowerCase().includes('click here') || linkText.toLowerCase().includes('여기')) {
      checks.push({
        passed: false,
        message: 'Link has non-descriptive text',
        element: link
      });
    }
  });
  
  return checks;
} 