/**
 * 포커스 트랩 유틸리티
 * 모달, 드롭다운 등에서 키보드 포커스를 특정 요소 내에 가두는 기능
 */

import { getFocusableElements } from './accessibility';

export interface FocusTrapOptions {
  initialFocus?: HTMLElement | string;
  fallbackFocus?: HTMLElement | string;
  escapeDeactivates?: boolean;
  returnFocusOnDeactivate?: boolean;
  allowOutsideClick?: boolean;
  onActivate?: () => void;
  onDeactivate?: () => void;
  onEscape?: () => void;
}

export class FocusTrap {
  private container: HTMLElement;
  public options: FocusTrapOptions;
  private isActive: boolean = false;
  private previousActiveElement: Element | null = null;
  private focusableElements: Element[] = [];
  private firstFocusableElement: HTMLElement | null = null;
  private lastFocusableElement: HTMLElement | null = null;

  constructor(container: HTMLElement | string, options: FocusTrapOptions = {}) {
    this.container = typeof container === 'string' 
      ? document.querySelector(container) as HTMLElement
      : container;
    
    if (!this.container) {
      throw new Error('FocusTrap: Container element not found');
    }

    this.options = {
      escapeDeactivates: true,
      returnFocusOnDeactivate: true,
      allowOutsideClick: false,
      ...options
    };

    // 이벤트 핸들러 바인딩
    this.handleKeydown = this.handleKeydown.bind(this);
    this.handleClick = this.handleClick.bind(this);
  }

  /**
   * 포커스 트랩 활성화
   */
  activate(): void {
    if (this.isActive) return;

    // 현재 포커스된 요소 저장
    this.previousActiveElement = document.activeElement;

    // 포커스 가능한 요소들 업데이트
    this.updateFocusableElements();

    // 이벤트 리스너 등록
    document.addEventListener('keydown', this.handleKeydown, true);
    if (!this.options.allowOutsideClick) {
      document.addEventListener('click', this.handleClick, true);
    }

    // 초기 포커스 설정
    this.setInitialFocus();

    this.isActive = true;
    this.options.onActivate?.();
  }

  /**
   * 포커스 트랩 비활성화
   */
  deactivate(): void {
    if (!this.isActive) return;

    // 이벤트 리스너 제거
    document.removeEventListener('keydown', this.handleKeydown, true);
    document.removeEventListener('click', this.handleClick, true);

    // 이전 포커스 복원
    if (this.options.returnFocusOnDeactivate && this.previousActiveElement) {
      (this.previousActiveElement as HTMLElement).focus();
    }

    this.isActive = false;
    this.options.onDeactivate?.();
  }

  /**
   * 포커스 가능한 요소들 업데이트
   */
  updateFocusableElements(): void {
    this.focusableElements = getFocusableElements(this.container);
    this.firstFocusableElement = this.focusableElements[0] as HTMLElement || null;
    this.lastFocusableElement = this.focusableElements[this.focusableElements.length - 1] as HTMLElement || null;
  }

  /**
   * 초기 포커스 설정
   */
  private setInitialFocus(): void {
    let elementToFocus: HTMLElement | null = null;

    // 옵션에서 지정된 초기 포커스 요소
    if (this.options.initialFocus) {
      if (typeof this.options.initialFocus === 'string') {
        elementToFocus = this.container.querySelector(this.options.initialFocus) as HTMLElement;
      } else {
        elementToFocus = this.options.initialFocus;
      }
    }

    // autofocus 속성이 있는 요소
    if (!elementToFocus) {
      elementToFocus = this.container.querySelector('[autofocus]') as HTMLElement;
    }

    // 첫 번째 포커스 가능한 요소
    if (!elementToFocus) {
      elementToFocus = this.firstFocusableElement;
    }

    // 폴백 포커스 요소
    if (!elementToFocus && this.options.fallbackFocus) {
      if (typeof this.options.fallbackFocus === 'string') {
        elementToFocus = document.querySelector(this.options.fallbackFocus) as HTMLElement;
      } else {
        elementToFocus = this.options.fallbackFocus;
      }
    }

    // 컨테이너 자체에 포커스 (마지막 수단)
    if (!elementToFocus) {
      elementToFocus = this.container;
      this.container.setAttribute('tabindex', '-1');
    }

    elementToFocus?.focus();
  }

  /**
   * 키보드 이벤트 처리
   */
  private handleKeydown(event: KeyboardEvent): void {
    if (!this.isActive) return;

    // ESC 키 처리
    if (event.key === 'Escape' && this.options.escapeDeactivates) {
      event.preventDefault();
      this.options.onEscape?.();
      this.deactivate();
      return;
    }

    // Tab 키 처리 (포커스 순환)
    if (event.key === 'Tab') {
      this.handleTabKey(event);
    }
  }

  /**
   * Tab 키 처리 (포커스 순환)
   */
  private handleTabKey(event: KeyboardEvent): void {
    if (this.focusableElements.length === 0) {
      event.preventDefault();
      return;
    }

    const currentFocusIndex = this.focusableElements.indexOf(document.activeElement as Element);

    if (event.shiftKey) {
      // Shift + Tab (역방향)
      if (currentFocusIndex === 0 || currentFocusIndex === -1) {
        event.preventDefault();
        this.lastFocusableElement?.focus();
      }
    } else {
      // Tab (정방향)
      if (currentFocusIndex === this.focusableElements.length - 1 || currentFocusIndex === -1) {
        event.preventDefault();
        this.firstFocusableElement?.focus();
      }
    }
  }

  /**
   * 클릭 이벤트 처리 (외부 클릭 방지)
   */
  private handleClick(event: MouseEvent): void {
    if (!this.isActive) return;

    const target = event.target as Element;
    if (!this.container.contains(target)) {
      event.preventDefault();
      event.stopPropagation();
      
      // 컨테이너 내 첫 번째 요소에 포커스
      this.firstFocusableElement?.focus();
    }
  }

  /**
   * 활성 상태 확인
   */
  get active(): boolean {
    return this.isActive;
  }

  /**
   * 컨테이너 요소 반환
   */
  get element(): HTMLElement {
    return this.container;
  }
}

/**
 * 간단한 포커스 트랩 생성 헬퍼 함수
 */
export function createFocusTrap(
  container: HTMLElement | string,
  options?: FocusTrapOptions
): FocusTrap {
  return new FocusTrap(container, options);
}

/**
 * 모달용 포커스 트랩 생성 (미리 설정된 옵션)
 */
export function createModalFocusTrap(
  modal: HTMLElement | string,
  options: Partial<FocusTrapOptions> = {}
): FocusTrap {
  return new FocusTrap(modal, {
    escapeDeactivates: true,
    returnFocusOnDeactivate: true,
    allowOutsideClick: false,
    ...options
  });
}

/**
 * 드롭다운용 포커스 트랩 생성 (미리 설정된 옵션)
 */
export function createDropdownFocusTrap(
  dropdown: HTMLElement | string,
  options: Partial<FocusTrapOptions> = {}
): FocusTrap {
  return new FocusTrap(dropdown, {
    escapeDeactivates: true,
    returnFocusOnDeactivate: true,
    allowOutsideClick: true,
    ...options
  });
}

/**
 * Svelte action으로 사용할 수 있는 포커스 트랩
 */
export function focusTrap(node: HTMLElement, options: FocusTrapOptions = {}) {
  const trap = new FocusTrap(node, options);
  trap.activate();

  return {
    destroy() {
      trap.deactivate();
    },
    update(newOptions: FocusTrapOptions) {
      trap.deactivate();
      // 새 옵션으로 다시 생성하는 대신 기존 인스턴스 업데이트
      Object.assign(trap.options, newOptions);
      trap.activate();
    }
  };
} 