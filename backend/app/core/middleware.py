"""
미들웨어 모듈

애플리케이션 전역 미들웨어들을 정의합니다.
- 에러 처리 미들웨어
- 로깅 미들웨어
- 보안 미들웨어
- 성능 모니터링 미들웨어
"""

import time
import uuid
import traceback
from typing import Any, Dict
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

from app.core.config import settings

# 로거 설정
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    요청/응답 로깅 미들웨어
    
    모든 API 요청과 응답을 구조화된 형태로 로그에 기록합니다.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # 요청 ID 생성
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 요청 시작 시간
        start_time = time.time()
        
        # 요청 정보 로깅
        logger.info(
            "요청 시작",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "user_agent": request.headers.get("user-agent"),
                "client_ip": request.client.host if request.client else None,
                "timestamp": start_time
            }
        )
        
        try:
            # 요청 처리
            response = await call_next(request)
            
            # 처리 시간 계산
            process_time = time.time() - start_time
            
            # 응답 정보 로깅
            logger.info(
                "요청 완료",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time": f"{process_time:.4f}s",
                    "response_size": response.headers.get("content-length", "unknown")
                }
            )
            
            # 응답 헤더에 요청 ID 추가
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # 에러 로깅
            logger.error(
                "요청 처리 중 에러",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "process_time": f"{process_time:.4f}s",
                    "traceback": traceback.format_exc() if settings.DEBUG else None
                }
            )
            
            # 에러 응답 반환
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal Server Error",
                    "request_id": request_id,
                    "timestamp": time.time()
                },
                headers={"X-Request-ID": request_id}
            )


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    전역 에러 처리 미들웨어
    
    애플리케이션에서 발생하는 모든 에러를 catch하고 적절한 응답을 반환합니다.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # FastAPI HTTPException은 그대로 전달
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "detail": e.detail,
                    "error_code": "HTTP_EXCEPTION",
                    "request_id": getattr(request.state, 'request_id', None),
                    "timestamp": time.time()
                }
            )
            
        except ValueError as e:
            # 값 에러 (잘못된 입력 등)
            logger.warning(f"ValueError: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "잘못된 요청 데이터입니다.",
                    "error_code": "INVALID_INPUT",
                    "request_id": getattr(request.state, 'request_id', None),
                    "timestamp": time.time()
                }
            )
            
        except PermissionError as e:
            # 권한 에러
            logger.warning(f"PermissionError: {str(e)}")
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "권한이 없습니다.",
                    "error_code": "PERMISSION_DENIED",
                    "request_id": getattr(request.state, 'request_id', None),
                    "timestamp": time.time()
                }
            )
            
        except ConnectionError as e:
            # 연결 에러 (DB, 외부 API 등)
            logger.error(f"ConnectionError: {str(e)}")
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "서비스를 일시적으로 사용할 수 없습니다.",
                    "error_code": "SERVICE_UNAVAILABLE",
                    "request_id": getattr(request.state, 'request_id', None),
                    "timestamp": time.time()
                }
            )
            
        except Exception as e:
            # 예상치 못한 에러
            request_id = getattr(request.state, 'request_id', 'unknown')
            logger.error(
                f"Unexpected error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                }
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "내부 서버 오류가 발생했습니다." if not settings.DEBUG else str(e),
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "request_id": request_id,
                    "timestamp": time.time()
                }
            )


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    보안 미들웨어
    
    기본적인 보안 헤더들을 추가합니다.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # 보안 헤더 추가
        if not settings.DEBUG:
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # API 버전 헤더
        response.headers["X-API-Version"] = settings.VERSION
        
        return response


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    성능 모니터링 미들웨어
    
    느린 요청들을 감지하고 로그에 기록합니다.
    """
    
    SLOW_REQUEST_THRESHOLD = 2.0  # 2초 이상이면 느린 요청으로 간주
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # 느린 요청 감지
        if process_time > self.SLOW_REQUEST_THRESHOLD:
            logger.warning(
                "느린 요청 감지",
                extra={
                    "request_id": getattr(request.state, 'request_id', None),
                    "method": request.method,
                    "url": str(request.url),
                    "process_time": f"{process_time:.4f}s",
                    "threshold": f"{self.SLOW_REQUEST_THRESHOLD}s"
                }
            )
        
        return response


def setup_middleware(app):
    """
    애플리케이션에 미들웨어들을 등록합니다.
    
    Args:
        app: FastAPI 애플리케이션 인스턴스
    """
    # 미들웨어는 역순으로 적용되므로 주의
    # 마지막에 등록된 것이 가장 먼저 실행됨
    
    # 1. 성능 모니터링 (가장 안쪽)
    app.add_middleware(PerformanceMiddleware)
    
    # 2. 에러 처리
    app.add_middleware(ErrorHandlingMiddleware)
    
    # 3. 로깅
    app.add_middleware(LoggingMiddleware)
    
    # 4. 보안 헤더 (가장 바깥쪽)
    app.add_middleware(SecurityMiddleware)
    
    logger.info("미들웨어 설정 완료")


# 표준 API 응답 형식
class StandardResponse:
    """
    표준화된 API 응답 형식
    """
    
    @staticmethod
    def success(data: Any = None, message: str = "성공", meta: Dict = None) -> Dict:
        """성공 응답"""
        response = {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": time.time()
        }
        
        if meta:
            response["meta"] = meta
            
        return response
    
    @staticmethod
    def error(message: str, error_code: str = "ERROR", details: Any = None) -> Dict:
        """에러 응답"""
        response = {
            "success": False,
            "message": message,
            "error_code": error_code,
            "timestamp": time.time()
        }
        
        if details and settings.DEBUG:
            response["details"] = details
            
        return response
    
    @staticmethod
    def paginated(data: list, total: int, page: int, limit: int, **kwargs) -> Dict:
        """페이지네이션 응답"""
        has_next = (page * limit) < total
        has_prev = page > 1
        
        return StandardResponse.success(
            data=data,
            meta={
                "pagination": {
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "has_next": has_next,
                    "has_prev": has_prev,
                    **kwargs
                }
            }
        ) 