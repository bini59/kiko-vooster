/**
 * 키보드 탐색 헬퍼 유틸리티
 * 공통 키보드 단축키 및 탐색 패턴 제공
 */

import { getArrowDirection, isActivationKey } from './accessibility';

/**
 * 키보드 단축키 정의 인터페이스
 */
export interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  metaKey?: boolean;
  description: string;
  action: () => void;
}

/**
 * 방향 탐색 옵션
 */
export interface DirectionalNavigationOptions {
  wrap?: boolean; // 끝에서 처음으로 순환
  skipDisabled?: boolean; // 비활성화된 요소 건너뛰기
  vertical?: boolean; // 세로 탐색 (위/아래 화살표)
  horizontal?: boolean; // 가로 탐색 (좌/우 화살표)
  onNavigate?: (index: number, element: HTMLElement) => void;
  onActivate?: (index: number, element: HTMLElement) => void;
}

/**
 * 키보드 단축키 관리자
 */
export class KeyboardShortcutManager {
  private shortcuts: Map<string, KeyboardShortcut> = new Map();
  private isEnabled: boolean = true;
  private currentScope: string = 'global';

  /**
   * 단축키 등록
   */
  register(id: string, shortcut: KeyboardShortcut): void {
    this.shortcuts.set(`${this.currentScope}:${id}`, shortcut);
  }

  /**
   * 단축키 해제
   */
  unregister(id: string): void {
    this.shortcuts.delete(`${this.currentScope}:${id}`);
  }

  /**
   * 스코프 설정 (전역, 모달, 플레이어 등)
   */
  setScope(scope: string): void {
    this.currentScope = scope;
  }

  /**
   * 키보드 이벤트 처리
   */
  handleKeyEvent(event: KeyboardEvent): boolean {
    if (!this.isEnabled) return false;

    // 입력 요소에서는 일부 단축키 무시
    const target = event.target as HTMLElement;
    const isInputElement = target.matches('input, textarea, select, [contenteditable="true"]');

    for (const [key, shortcut] of this.shortcuts) {
      if (this.matchesShortcut(event, shortcut)) {
        // 입력 요소에서는 Ctrl/Cmd 조합만 허용
        if (isInputElement && !event.ctrlKey && !event.metaKey) {
          continue;
        }

        event.preventDefault();
        shortcut.action();
        return true;
      }
    }

    return false;
  }

  /**
   * 단축키 일치 확인
   */
  private matchesShortcut(event: KeyboardEvent, shortcut: KeyboardShortcut): boolean {
    return (
      event.key === shortcut.key &&
      !!event.ctrlKey === !!shortcut.ctrlKey &&
      !!event.shiftKey === !!shortcut.shiftKey &&
      !!event.altKey === !!shortcut.altKey &&
      !!event.metaKey === !!shortcut.metaKey
    );
  }

  /**
   * 단축키 활성화/비활성화
   */
  setEnabled(enabled: boolean): void {
    this.isEnabled = enabled;
  }

  /**
   * 현재 등록된 단축키 목록 반환
   */
  getShortcuts(): KeyboardShortcut[] {
    return Array.from(this.shortcuts.values());
  }

  /**
   * 스코프별 단축키 목록 반환
   */
  getShortcutsForScope(scope: string): KeyboardShortcut[] {
    return Array.from(this.shortcuts.entries())
      .filter(([key]) => key.startsWith(`${scope}:`))
      .map(([, shortcut]) => shortcut);
  }
}

/**
 * 방향 탐색 관리자
 */
export class DirectionalNavigator {
  private elements: HTMLElement[] = [];
  private currentIndex: number = -1;
  public options: DirectionalNavigationOptions;

  constructor(elements: HTMLElement[] | NodeList, options: DirectionalNavigationOptions = {}) {
    this.elements = Array.from(elements) as HTMLElement[];
    this.options = {
      wrap: true,
      skipDisabled: true,
      vertical: true,
      horizontal: true,
      ...options
    };
  }

  /**
   * 키보드 이벤트 처리
   */
  handleKeyEvent(event: KeyboardEvent): boolean {
    const direction = getArrowDirection(event);
    
    if (!direction) {
      // 활성화 키 (Enter, Space) 처리
      if (isActivationKey(event) && this.currentIndex >= 0) {
        event.preventDefault();
        this.activate(this.currentIndex);
        return true;
      }
      return false;
    }

    // 방향에 따른 탐색
    let handled = false;
    
    if ((direction === 'up' || direction === 'down') && this.options.vertical) {
      event.preventDefault();
      this.navigate(direction === 'down' ? 1 : -1);
      handled = true;
    } else if ((direction === 'left' || direction === 'right') && this.options.horizontal) {
      event.preventDefault();
      this.navigate(direction === 'right' ? 1 : -1);
      handled = true;
    }

    return handled;
  }

  /**
   * 특정 방향으로 탐색
   */
  navigate(delta: number): void {
    if (this.elements.length === 0) return;

    let newIndex = this.currentIndex + delta;

    // 순환 처리
    if (this.options.wrap) {
      if (newIndex >= this.elements.length) {
        newIndex = 0;
      } else if (newIndex < 0) {
        newIndex = this.elements.length - 1;
      }
    } else {
      newIndex = Math.max(0, Math.min(this.elements.length - 1, newIndex));
    }

    // 비활성화된 요소 건너뛰기
    if (this.options.skipDisabled) {
      let attempts = 0;
      while (
        attempts < this.elements.length && 
        this.isElementDisabled(this.elements[newIndex])
      ) {
        newIndex += delta;
        if (this.options.wrap) {
          if (newIndex >= this.elements.length) newIndex = 0;
          if (newIndex < 0) newIndex = this.elements.length - 1;
        } else {
          newIndex = Math.max(0, Math.min(this.elements.length - 1, newIndex));
        }
        attempts++;
      }
    }

    if (newIndex !== this.currentIndex) {
      this.setCurrentIndex(newIndex);
    }
  }

  /**
   * 현재 인덱스 설정
   */
  setCurrentIndex(index: number): void {
    this.currentIndex = index;
    const element = this.elements[index];
    
    if (element) {
      element.focus();
      this.options.onNavigate?.(index, element);
    }
  }

  /**
   * 현재 요소 활성화
   */
  activate(index: number = this.currentIndex): void {
    const element = this.elements[index];
    if (element) {
      this.options.onActivate?.(index, element);
      
      // 기본 클릭 동작 실행
      if (element.matches('button, a, [role="button"]')) {
        element.click();
      }
    }
  }

  /**
   * 요소가 비활성화되었는지 확인
   */
  private isElementDisabled(element: HTMLElement): boolean {
    return (
      element.hasAttribute('disabled') ||
      element.getAttribute('aria-disabled') === 'true' ||
      element.style.visibility === 'hidden' ||
      element.style.display === 'none'
    );
  }

  /**
   * 요소 목록 업데이트
   */
  updateElements(elements: HTMLElement[] | NodeList): void {
    this.elements = Array.from(elements) as HTMLElement[];
    this.currentIndex = -1;
  }

  /**
   * 첫 번째 요소로 이동
   */
  first(): void {
    this.setCurrentIndex(0);
  }

  /**
   * 마지막 요소로 이동
   */
  last(): void {
    this.setCurrentIndex(this.elements.length - 1);
  }
}

/**
 * 로빙 탐색 (탭 패널, 메뉴 등에 사용)
 */
export class RovingTabIndexManager {
  private elements: HTMLElement[] = [];
  private currentIndex: number = 0;

  constructor(elements: HTMLElement[] | NodeList) {
    this.elements = Array.from(elements) as HTMLElement[];
    this.init();
  }

  /**
   * 초기화
   */
  private init(): void {
    this.elements.forEach((element, index) => {
      element.setAttribute('tabindex', index === 0 ? '0' : '-1');
      element.addEventListener('focus', () => this.setCurrentIndex(index));
      element.addEventListener('keydown', (e) => this.handleKeydown(e));
    });
  }

  /**
   * 키보드 이벤트 처리
   */
  private handleKeydown(event: KeyboardEvent): void {
    const direction = getArrowDirection(event);
    if (!direction) return;

    event.preventDefault();
    
    switch (direction) {
      case 'left':
      case 'up':
        this.previous();
        break;
      case 'right':
      case 'down':
        this.next();
        break;
    }
  }

  /**
   * 다음 요소로 이동
   */
  next(): void {
    const nextIndex = (this.currentIndex + 1) % this.elements.length;
    this.setCurrentIndex(nextIndex);
  }

  /**
   * 이전 요소로 이동
   */
  previous(): void {
    const prevIndex = (this.currentIndex - 1 + this.elements.length) % this.elements.length;
    this.setCurrentIndex(prevIndex);
  }

  /**
   * 현재 인덱스 설정
   */
  setCurrentIndex(index: number): void {
    // 모든 요소의 tabindex를 -1로 설정
    this.elements.forEach(element => {
      element.setAttribute('tabindex', '-1');
    });

    // 현재 요소만 0으로 설정하고 포커스
    this.currentIndex = index;
    const currentElement = this.elements[index];
    currentElement.setAttribute('tabindex', '0');
    currentElement.focus();
  }

  /**
   * 요소 목록 업데이트
   */
  updateElements(elements: HTMLElement[] | NodeList): void {
    this.elements = Array.from(elements) as HTMLElement[];
    this.init();
  }
}

/**
 * 전역 키보드 단축키 관리자 인스턴스
 */
export const globalShortcutManager = new KeyboardShortcutManager();

/**
 * 공통 키보드 단축키 등록
 */
export function registerCommonShortcuts(manager: KeyboardShortcutManager = globalShortcutManager): void {
  manager.setScope('global');

  // 일반적인 접근성 단축키들
  manager.register('skipToMain', {
    key: 'Enter',
    description: '메인 콘텐츠로 바로가기 (스킵 링크에서)',
    action: () => {
      const mainContent = document.getElementById('main-content');
      mainContent?.focus();
    }
  });

  manager.register('showShortcuts', {
    key: '?',
    description: '키보드 단축키 도움말 표시',
    action: () => {
      // 키보드 단축키 도움말 모달 표시
      const event = new CustomEvent('showKeyboardHelp');
      window.dispatchEvent(event);
    }
  });
}

/**
 * Svelte action: 키보드 단축키
 */
export function keyboardShortcuts(
  node: HTMLElement, 
  shortcuts: Array<{ id: string; shortcut: KeyboardShortcut }>
) {
  const manager = new KeyboardShortcutManager();
  
  shortcuts.forEach(({ id, shortcut }) => {
    manager.register(id, shortcut);
  });

  function handleKeydown(event: KeyboardEvent) {
    manager.handleKeyEvent(event);
  }

  node.addEventListener('keydown', handleKeydown);

  return {
    destroy() {
      node.removeEventListener('keydown', handleKeydown);
    },
    update(newShortcuts: Array<{ id: string; shortcut: KeyboardShortcut }>) {
      // 기존 단축키 제거
      shortcuts.forEach(({ id }) => manager.unregister(id));
      
      // 새 단축키 등록
      newShortcuts.forEach(({ id, shortcut }) => {
        manager.register(id, shortcut);
      });
      
      shortcuts = newShortcuts;
    }
  };
}

/**
 * Svelte action: 방향 탐색
 */
export function directionalNavigation(
  node: HTMLElement,
  options: DirectionalNavigationOptions & { selector?: string } = {}
) {
  const { selector = '[tabindex]:not([tabindex="-1"]), button:not([disabled]), a[href]', ...navOptions } = options;
  
  function updateNavigator() {
    const elements = node.querySelectorAll(selector) as NodeListOf<HTMLElement>;
    return new DirectionalNavigator(elements, navOptions);
  }

  let navigator = updateNavigator();

  function handleKeydown(event: KeyboardEvent) {
    navigator.handleKeyEvent(event);
  }

  node.addEventListener('keydown', handleKeydown);

  return {
    destroy() {
      node.removeEventListener('keydown', handleKeydown);
    },
    update(newOptions: DirectionalNavigationOptions & { selector?: string }) {
      const { selector: newSelector = selector, ...newNavOptions } = newOptions;
      navigator = updateNavigator();
      Object.assign(navigator.options, newNavOptions);
    }
  };
} 