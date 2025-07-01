"""
오디오 재생 API 엔드포인트

라디오 오디오 스트리밍 및 재생 제어 API
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.models.audio import (
    StreamRequest, StreamResponse,
    PrepareRequest, PrepareResponse,
    PlayRequest, PlayResponse,
    ProgressUpdate, ProgressResponse,
    SeekRequest, SeekResponse,
    BookmarkRequest, BookmarkResponse,
    LoopRequest, LoopResponse,
    AudioError
)
from app.services.audio.audio_service import get_audio_service, AudioService
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.core.database import get_database

router = APIRouter()


# 의존성 함수
async def get_audio_service_dep() -> AudioService:
    """오디오 서비스 의존성"""
    return get_audio_service()


# 에러 응답 헬퍼
def audio_error_response(code: str, message: str, status_code: int = 400):
    """오디오 에러 응답 생성"""
    return JSONResponse(
        status_code=status_code,
        content=AudioError(error_code=code, message=message).dict()
    )


@router.get("/stream/{script_id}", response_model=StreamResponse)
async def get_stream(
    script_id: UUID,
    quality: str = Query(default="medium", regex="^(low|medium|high)$"),
    format: str = Query(default="hls", regex="^(hls|mp3)$"),
    current_user: Optional[User] = Depends(get_current_user),
    audio_service: AudioService = Depends(get_audio_service_dep)
):
    """
    오디오 스트림 URL 및 메타데이터 조회
    
    - **script_id**: 스크립트 ID
    - **quality**: 오디오 품질 (low, medium, high)
    - **format**: 스트리밍 형식 (hls, mp3)
    """
    try:
        user_id = current_user.id if current_user else None
        stream_info = await audio_service.get_stream_info(
            script_id=script_id,
            quality=quality,
            user_id=user_id
        )
        return stream_info
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/prepare/{script_id}", response_model=PrepareResponse)
async def prepare_audio(
    script_id: UUID,
    request: PrepareRequest,
    current_user: User = Depends(get_current_user),
    audio_service: AudioService = Depends(get_audio_service_dep)
):
    """
    오디오 파일 사전 처리 및 캐싱
    
    백그라운드에서 HLS 변환 및 세그먼트 생성을 시작합니다.
    """
    try:
        prepare_status = await audio_service.prepare_audio(
            script_id=script_id,
            priority=request.priority
        )
        return prepare_status
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preparation failed: {str(e)}")


@router.post("/play", response_model=PlayResponse)
async def start_playback(
    request: PlayRequest,
    current_user: User = Depends(get_current_user),
    audio_service: AudioService = Depends(get_audio_service_dep)
):
    """
    재생 시작 및 세션 생성
    
    새로운 재생 세션을 생성하고 스트림 URL을 반환합니다.
    """
    try:
        play_response = await audio_service.create_play_session(
            script_id=request.script_id,
            user_id=current_user.id,
            position=request.position,
            sentence_id=request.sentence_id
        )
        return play_response
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Playback start failed: {str(e)}")


@router.put("/progress", response_model=ProgressResponse)
async def update_progress(
    update: ProgressUpdate,
    current_user: User = Depends(get_current_user),
    audio_service: AudioService = Depends(get_audio_service_dep)
):
    """
    재생 진행 상황 업데이트
    
    현재 재생 위치와 상태를 서버에 동기화합니다.
    """
    try:
        progress_response = await audio_service.update_progress(
            session_id=update.session_id,
            position=update.position,
            sentence_id=update.sentence_id,
            playback_rate=update.playback_rate
        )
        return progress_response
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Progress update failed: {str(e)}")


@router.post("/seek", response_model=SeekResponse)
async def seek_position(
    request: SeekRequest,
    current_user: User = Depends(get_current_user),
    audio_service: AudioService = Depends(get_audio_service_dep)
):
    """
    특정 위치로 이동
    
    재생 위치를 지정된 시간으로 이동합니다.
    """
    try:
        seek_response = await audio_service.seek_position(
            session_id=request.session_id,
            position=request.position,
            sentence_id=request.sentence_id
        )
        return seek_response
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seek failed: {str(e)}")


@router.post("/bookmark", response_model=BookmarkResponse)
async def create_bookmark(
    request: BookmarkRequest,
    current_user: User = Depends(get_current_user),
    audio_service: AudioService = Depends(get_audio_service_dep)
):
    """
    재생 위치 북마크
    
    현재 재생 위치를 북마크로 저장합니다.
    """
    try:
        bookmark_response = await audio_service.create_bookmark(
            user_id=current_user.id,
            script_id=request.script_id,
            position=request.position,
            note=request.note
        )
        return bookmark_response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bookmark creation failed: {str(e)}")