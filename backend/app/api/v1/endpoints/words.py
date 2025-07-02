"""
단어장 관련 API 엔드포인트

단어 검색, 사용자 단어장 관리, 복습 기능을 제공합니다.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer

from app.models.user import User
from app.models.word import (
    WordSearchRequest, WordSearchResponse,
    AddWordRequest, AddWordResponse,
    UpdateWordRequest, UpdateWordResponse,
    VocabularyStatsResponse, VocabularyTagsResponse,
    ReviewWordsRequest, ReviewWordsResponse,
    ReviewResultRequest, ReviewResultResponse,
    ReviewStatsResponse
)
from app.core.dependencies import get_current_user, get_database_manager
from app.core.database import DatabaseManager
from app.services.words import WordService, VocabularyService, ReviewService
from app.utils.japanese import validate_japanese_word

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# ===================
# 단어 검색 관련 엔드포인트
# ===================

@router.post("/search", response_model=WordSearchResponse)
async def search_words(
    request: WordSearchRequest,
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """
    단어 검색
    
    로컬 DB와 JMdict API를 활용하여 일본어 단어를 검색합니다.
    """
    try:
        word_service = WordService(db_manager)
        
        # 입력 검증
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="검색어를 입력해주세요.")
        
        # 일본어 검증 (선택적)
        if request.search_type in ["kanji", "hiragana"] and request.query:
            validation = validate_japanese_word(request.query)
            if not validation["is_japanese"]:
                logger.warning(f"⚠️ 비일본어 검색어: {request.query}")
        
        # 단어 검색 실행
        search_result = await word_service.search_words(
            query=request.query.strip(),
            search_type=request.search_type,
            limit=request.limit
        )
        
        logger.info(f"✅ 단어 검색 성공: '{request.query}' -> {len(search_result['results'])}개")
        
        return WordSearchResponse(
            results=search_result["results"],
            total=search_result["total"],
            query=search_result["query"],
            search_type=search_result["search_type"]
        )
        
    except Exception as e:
        logger.error(f"❌ 단어 검색 실패: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="단어 검색 중 오류가 발생했습니다."
        )

@router.get("/{word_id}")
async def get_word(
    word_id: str,
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """단어 상세 정보 조회"""
    try:
        word_service = WordService(db_manager)
        word = await word_service.get_word_by_id(word_id)
        
        if not word:
            raise HTTPException(status_code=404, detail="단어를 찾을 수 없습니다.")
        
        logger.info(f"✅ 단어 조회 성공: {word_id}")
        return word
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 단어 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="단어 조회 중 오류가 발생했습니다."
        )

# ===================
# 사용자 단어장 관련 엔드포인트
# ===================

@router.get("/vocabulary/list")
async def get_user_vocabulary(
    tags: Optional[List[str]] = Query(None, description="필터링할 태그"),
    mastery_level: Optional[int] = Query(None, ge=0, le=5, description="숙련도 필터"),
    limit: int = Query(50, ge=1, le=100, description="결과 개수 제한"),
    offset: int = Query(0, ge=0, description="오프셋"),
    current_user: User = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """사용자 단어장 조회"""
    try:
        vocabulary_service = VocabularyService(db_manager)
        
        result = await vocabulary_service.get_user_vocabulary(
            user_id=current_user.id,
            tags=tags,
            mastery_level=mastery_level,
            limit=limit,
            offset=offset
        )
        
        logger.info(f"✅ 단어장 조회 성공: {current_user.id}, {len(result['words'])}개")
        return result
        
    except Exception as e:
        logger.error(f"❌ 단어장 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="단어장 조회 중 오류가 발생했습니다."
        )

@router.post("/vocabulary/add", response_model=AddWordResponse)
async def add_word_to_vocabulary(
    request: AddWordRequest,
    current_user: User = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """단어장에 단어 추가"""
    try:
        vocabulary_service = VocabularyService(db_manager)
        
        # 입력 검증
        if not request.word_text.strip():
            raise HTTPException(status_code=400, detail="단어를 입력해주세요.")
        
        # 일본어 검증
        validation = validate_japanese_word(request.word_text)
        if not validation["is_valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"유효하지 않은 일본어 단어입니다: {', '.join(validation['errors'])}"
            )
        
        # 단어장에 추가
        result = await vocabulary_service.add_word_to_vocabulary(
            user_id=current_user.id,
            word_text=validation["cleaned_text"],
            tags=request.tags,
            notes=request.notes
        )
        
        logger.info(f"✅ 단어장 추가 성공: {current_user.id}, {request.word_text}")
        
        return AddWordResponse(
            message="단어가 단어장에 추가되었습니다.",
            word=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 단어장 추가 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="단어장 추가 중 오류가 발생했습니다."
        )

@router.put("/vocabulary/{word_id}", response_model=UpdateWordResponse)
async def update_vocabulary_word(
    word_id: str,
    request: UpdateWordRequest,
    current_user: User = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """단어장 단어 정보 업데이트"""
    try:
        vocabulary_service = VocabularyService(db_manager)
        
        # 입력 검증
        if request.mastery_level is not None and not (0 <= request.mastery_level <= 5):
            raise HTTPException(status_code=400, detail="숙련도는 0~5 사이의 값이어야 합니다.")
        
        # 단어 업데이트
        result = await vocabulary_service.update_vocabulary_word(
            user_id=current_user.id,
            word_id=word_id,
            mastery_level=request.mastery_level,
            tags=request.tags,
            notes=request.notes
        )
        
        logger.info(f"✅ 단어장 업데이트 성공: {current_user.id}, {word_id}")
        
        return UpdateWordResponse(
            message="단어 정보가 업데이트되었습니다.",
            word=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 단어장 업데이트 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="단어장 업데이트 중 오류가 발생했습니다."
        )

@router.delete("/vocabulary/{word_id}")
async def remove_word_from_vocabulary(
    word_id: str,
    current_user: User = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """단어장에서 단어 제거"""
    try:
        vocabulary_service = VocabularyService(db_manager)
        
        success = await vocabulary_service.remove_word_from_vocabulary(
            user_id=current_user.id,
            word_id=word_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="제거할 단어를 찾을 수 없습니다.")
        
        logger.info(f"✅ 단어장 제거 성공: {current_user.id}, {word_id}")
        
        return {"message": "단어가 단어장에서 제거되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 단어장 제거 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="단어장 제거 중 오류가 발생했습니다."
        )

@router.get("/vocabulary/stats", response_model=VocabularyStatsResponse)
async def get_vocabulary_stats(
    current_user: User = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """사용자 단어장 통계 조회"""
    try:
        vocabulary_service = VocabularyService(db_manager)
        
        stats = await vocabulary_service.get_vocabulary_stats(current_user.id)
        
        logger.info(f"✅ 단어장 통계 조회 성공: {current_user.id}")
        
        return VocabularyStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"❌ 단어장 통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="단어장 통계 조회 중 오류가 발생했습니다."
        )

@router.get("/vocabulary/tags", response_model=VocabularyTagsResponse)
async def get_vocabulary_tags(
    current_user: User = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """사용자 단어장 태그 목록 조회"""
    try:
        vocabulary_service = VocabularyService(db_manager)
        
        tags = await vocabulary_service.get_vocabulary_tags(current_user.id)
        
        logger.info(f"✅ 단어장 태그 조회 성공: {current_user.id}")
        
        return VocabularyTagsResponse(**tags)
        
    except Exception as e:
        logger.error(f"❌ 단어장 태그 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="단어장 태그 조회 중 오류가 발생했습니다."
        )

# ===================
# 복습 관련 엔드포인트
# ===================

@router.post("/review/words", response_model=ReviewWordsResponse)
async def get_review_words(
    request: ReviewWordsRequest,
    current_user: User = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """복습할 단어 목록 조회"""
    try:
        review_service = ReviewService(db_manager)
        
        # 입력 검증
        if request.count <= 0 or request.count > 50:
            raise HTTPException(status_code=400, detail="복습 단어 개수는 1~50 사이여야 합니다.")
        
        if request.mode not in ["new", "review", "mixed"]:
            raise HTTPException(status_code=400, detail="유효하지 않은 복습 모드입니다.")
        
        # 복습 단어 조회
        result = await review_service.get_review_words(
            user_id=current_user.id,
            count=request.count,
            mode=request.mode
        )
        
        logger.info(f"✅ 복습 단어 조회 성공: {current_user.id}, {len(result['words'])}개")
        
        return ReviewWordsResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 복습 단어 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="복습 단어 조회 중 오류가 발생했습니다."
        )

@router.post("/review/submit", response_model=ReviewResultResponse)
async def submit_review_result(
    request: ReviewResultRequest,
    current_user: User = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """복습 결과 제출"""
    try:
        review_service = ReviewService(db_manager)
        
        # 입력 검증
        if request.response_time is not None and request.response_time < 0:
            raise HTTPException(status_code=400, detail="응답 시간은 0 이상이어야 합니다.")
        
        # 복습 결과 제출
        result = await review_service.submit_review_result(
            user_id=current_user.id,
            word_id=request.word_id,
            correct=request.correct,
            response_time=request.response_time
        )
        
        logger.info(f"✅ 복습 결과 제출 성공: {current_user.id}, {request.word_id}")
        
        return ReviewResultResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 복습 결과 제출 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="복습 결과 제출 중 오류가 발생했습니다."
        )

@router.get("/review/stats", response_model=ReviewStatsResponse)
async def get_review_stats(
    current_user: User = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """사용자 복습 통계 조회"""
    try:
        review_service = ReviewService(db_manager)
        
        stats = await review_service.get_review_stats(current_user.id)
        
        logger.info(f"✅ 복습 통계 조회 성공: {current_user.id}")
        
        return ReviewStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"❌ 복습 통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="복습 통계 조회 중 오류가 발생했습니다."
        ) 