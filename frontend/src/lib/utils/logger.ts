/**
 * 환경별 로깅 유틸리티
 * 개발 환경에서만 로그를 출력하고, 프로덕션에서는 에러만 출력
 */

import { dev } from '$app/environment';

export const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3
} as const;

type LogLevel = typeof LOG_LEVELS[keyof typeof LOG_LEVELS];

// 환경 변수 안전하게 가져오기
const getEnvVar = (key: string, defaultValue: string = ''): string => {
  try {
    if (typeof window !== 'undefined') {
      return (window as any).__env?.[key] || defaultValue;
    }
    return defaultValue;
  } catch {
    return defaultValue;
  }
};

const isDebugEnabled = dev || getEnvVar('PUBLIC_DEBUG', 'false') === 'true';
const logLevel = getEnvVar('PUBLIC_LOG_LEVEL', 'info').toLowerCase();
const currentLogLevel = LOG_LEVELS[logLevel.toUpperCase() as keyof typeof LOG_LEVELS] ?? LOG_LEVELS.INFO;

/**
 * 환경별 조건부 로깅
 */
export const logger = {
  debug: (...args: any[]) => {
    if (isDebugEnabled && currentLogLevel <= LOG_LEVELS.DEBUG) {
      console.debug('[DEBUG]', ...args);
    }
  },

  info: (...args: any[]) => {
    if (isDebugEnabled && currentLogLevel <= LOG_LEVELS.INFO) {
      console.info('[INFO]', ...args);
    }
  },

  warn: (...args: any[]) => {
    if (currentLogLevel <= LOG_LEVELS.WARN) {
      console.warn('[WARN]', ...args);
    }
  },

  error: (...args: any[]) => {
    console.error('[ERROR]', ...args);
  },

  log: (...args: any[]) => {
    if (isDebugEnabled) {
      console.log('[LOG]', ...args);
    }
  }
};

/**
 * 성능 측정을 위한 타이머
 */
export class PerformanceTimer {
  private startTime: number;
  private label: string;

  constructor(label: string) {
    this.label = label;
    this.startTime = performance.now();
    logger.debug(`⏱️ Timer started: ${label}`);
  }

  end(): number {
    const endTime = performance.now();
    const duration = endTime - this.startTime;
    logger.debug(`⏱️ Timer ended: ${this.label} (${duration.toFixed(2)}ms)`);
    return duration;
  }
}

/**
 * 디버그 모드에서만 실행되는 함수
 */
export const debugOnly = (fn: () => void) => {
  if (isDebugEnabled) {
    fn();
  }
};

/**
 * 에러를 구조화하여 로깅
 */
export const logError = (error: unknown, context?: string) => {
  const errorInfo = {
    message: error instanceof Error ? error.message : String(error),
    stack: error instanceof Error ? error.stack : undefined,
    context,
    timestamp: new Date().toISOString()
  };

  logger.error('Application Error:', errorInfo);
  
  // 프로덕션에서는 에러 리포팅 서비스로 전송
  if (!dev && typeof window !== 'undefined') {
    // TODO: Sentry 등 에러 리포팅 서비스 연동
  }
};

/**
 * API 호출 로깅
 */
export const logApiCall = (method: string, url: string, duration?: number) => {
  const message = duration 
    ? `${method} ${url} (${duration.toFixed(2)}ms)`
    : `${method} ${url}`;
  
  logger.debug('🌐 API Call:', message);
};

/**
 * 사용자 행동 로깅 (analytics용)
 */
export const logUserAction = (action: string, data?: Record<string, any>) => {
  const event = {
    action,
    data,
    timestamp: new Date().toISOString(),
    userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : 'server'
  };

  logger.info('👤 User Action:', event);
  
  // 프로덕션에서는 analytics 서비스로 전송
  if (!dev && typeof window !== 'undefined') {
    // TODO: Google Analytics 등 연동
  }
}; 