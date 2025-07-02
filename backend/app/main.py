"""
Kiko API 메인 애플리케이션

일본어 라디오 학습 플랫폼의 FastAPI 백엔드 서버
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_database, close_database, get_database
from app.api.v1.router import api_router
from app.core.cache.redis_client import init_redis, close_redis, get_redis_client
from app.core.cache.cache_manager import CacheManager, RedisCacheBackend, MemoryCacheBackend, set_cache_manager
from app.core.storage.storage_manager import StorageManager, SupabaseStorageBackend, set_storage_manager
from app.services.audio.audio_service import AudioService, set_audio_service
from app.services.sync.sync_mapping_service import SyncMappingService, set_sync_mapping_service
from app.websocket.sync_websocket import websocket_router, SyncWebSocketManager, set_sync_websocket_manager

# 로깅 설정
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper()))
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    # 시작 시
    logger.info(f"🚀 Kiko API 시작 - 환경: {settings.ENVIRONMENT}")
    
    try:
        # 데이터베이스 초기화
        await init_database()
        logger.info("✅ 데이터베이스 초기화 완료")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 실패: {str(e)}")
        # 개발 환경에서는 계속 진행, 프로덕션에서는 중단
        if settings.is_production:
            raise e
        else:
            logger.warning("⚠️ 개발 환경에서 데이터베이스 없이 계속 진행")
    
    # Redis 초기화
    try:
        await init_redis()
        redis_client = get_redis_client()
        
        # 캐시 매니저 설정
        if redis_client:
            cache_backend = RedisCacheBackend(redis_client)
            logger.info("✅ Redis 캐시 백엔드 사용")
        else:
            cache_backend = MemoryCacheBackend()
            logger.warning("⚠️ 메모리 캐시 백엔드 사용 (Redis 연결 실패)")
        
        cache_manager = CacheManager(cache_backend)
        set_cache_manager(cache_manager)
        
    except Exception as e:
        logger.error(f"❌ Redis 초기화 실패: {str(e)}")
        # 메모리 캐시로 폴백
        cache_backend = MemoryCacheBackend()
        cache_manager = CacheManager(cache_backend)
        set_cache_manager(cache_manager)
        logger.warning("⚠️ 메모리 캐시 백엔드로 폴백")
    
    # 스토리지 매니저 초기화
    try:
        storage_backend = SupabaseStorageBackend(settings.STORAGE_BUCKET)
        storage_manager = StorageManager(storage_backend)
        set_storage_manager(storage_manager)
        logger.info("✅ 스토리지 매니저 초기화 완료")
    except Exception as e:
        logger.error(f"❌ 스토리지 매니저 초기화 실패: {str(e)}")
    
    # 오디오 서비스 초기화
    try:
        audio_service = AudioService(storage_manager, cache_manager)
        set_audio_service(audio_service)
        logger.info("✅ 오디오 서비스 초기화 완료")
    except Exception as e:
        logger.error(f"❌ 오디오 서비스 초기화 실패: {str(e)}")
    
    # 싱크 매핑 서비스 초기화
    try:
        sync_mapping_service = SyncMappingService(cache_manager)
        set_sync_mapping_service(sync_mapping_service)
        logger.info("✅ 싱크 매핑 서비스 초기화 완료")
    except Exception as e:
        logger.error(f"❌ 싱크 매핑 서비스 초기화 실패: {str(e)}")
    
    # WebSocket 매니저 초기화
    try:
        sync_websocket_manager = SyncWebSocketManager()
        set_sync_websocket_manager(sync_websocket_manager)
        logger.info("✅ WebSocket 매니저 초기화 완료")
    except Exception as e:
        logger.error(f"❌ WebSocket 매니저 초기화 실패: {str(e)}")
    
    yield
    
    # 종료 시
    logger.info("🛑 Kiko API 종료 중...")
    await close_database()
    await close_redis()
    logger.info("✅ 정리 완료")

# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="일본어 라디오 학습 플랫폼 API",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(api_router, prefix="/api/v1")

# WebSocket 라우터 등록
app.include_router(websocket_router)

# 루트 엔드포인트
@app.get("/")
async def read_root():
    """루트 엔드포인트"""
    return {
        "message": "🎌 Kiko API에 오신 것을 환영합니다!",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "redoc": "/redoc"
    }

# 헬스 체크 엔드포인트
@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    from datetime import datetime, timezone
    
    try:
        # 데이터베이스 연결 상태 확인
        db = await get_database()
        db_status = "connected" if db.is_connected() else "disconnected"
        
        return {
            "status": "healthy",
            "environment": settings.ENVIRONMENT,
            "version": settings.VERSION,
            "database": db_status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"헬스 체크 실패: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "environment": settings.ENVIRONMENT,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

# 데이터베이스 상태 확인 엔드포인트
@app.get("/api/v1/db/status")
async def database_status():
    """데이터베이스 상태 확인"""
    from datetime import datetime, timezone
    
    try:
        db = await get_database()
        
        if db.is_connected():
            # 기본 테이블 존재 확인
            test_query = db.client.from_("users").select("id").limit(1).execute()
            
            return {
                "status": "connected",
                "tables_accessible": True,
                "message": "데이터베이스 정상 작동",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "disconnected",
                    "tables_accessible": False,
                    "message": "데이터베이스 연결 실패",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
    except Exception as e:
        logger.error(f"데이터베이스 상태 확인 실패: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "error": str(e),
                "message": "데이터베이스 상태 확인 중 오류 발생",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

# 애플리케이션 생명주기 이벤트
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행되는 이벤트"""
    logger.info(f"🚀 Kiko Vooster API 시작 - 환경: {settings.ENVIRONMENT}")
    logger.info(f"📊 디버그 모드: {settings.DEBUG}")
    logger.info(f"🔧 API 문서: {settings.ENABLE_API_DOCS}")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행되는 이벤트"""
    logger.info("🔄 애플리케이션 종료 중...")
    await cleanup_dependencies()
    logger.info("✅ 애플리케이션 종료 완료")

# 전역 예외 처리
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 예외 처리기"""
    logger.error(f"전역 예외 발생: {str(exc)}")
    
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={
                "error": str(exc),
                "type": type(exc).__name__,
                "detail": "개발 모드에서 상세 오류 정보를 제공합니다."
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "error": "내부 서버 오류가 발생했습니다.",
                "message": "잠시 후 다시 시도해주세요."
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 