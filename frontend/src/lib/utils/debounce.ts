/**
 * 함수 호출을 지연시키는 debounce 유틸리티
 * 
 * @param func 실행할 함수
 * @param delay 지연 시간 (밀리초)
 * @returns debounced 함수
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
} 