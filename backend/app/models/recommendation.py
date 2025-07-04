"""
추천 시스템 관련 Pydantic 모델 정의

사용자 추천, 콘텐츠 기반 추천, 트렌드 분석 등의 데이터 모델을 포함합니다.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, validator, root_validator
from app.models.base import TimestampedModel


# =============================================================================
# 열거형 정의
# =============================================================================

class RecommendationType(str, Enum):
    """추천 타입"""
    PERSONALIZED = "personalized"
    TRENDING = "trending"
    SIMILAR = "similar"
    CATEGORY_BASED = "category_based"
    COLLABORATIVE = "collaborative"


class InteractionType(str, Enum):
    """사용자 상호작용 타입"""
    VIEW = "view"
    PLAY = "play"
    BOOKMARK = "bookmark"
    SKIP = "skip"
    COMPLETE = "complete"
    SHARE = "share"


class AlgorithmType(str, Enum):
    """추천 알고리즘 타입"""
    PERSONALIZED = "personalized"
    TRENDING = "trending"
    SIMILAR = "similar"
    CATEGORY_BASED = "category_based"
    COLLABORATIVE = "collaborative"
    HYBRID = "hybrid"


class ExternalSource(str, Enum):
    """외부 콘텐츠 소스"""
    SPOTIFY = "spotify"
    APPLE_MUSIC = "apple_music"
    YOUTUBE_MUSIC = "youtube_music"
    NHK = "nhk"
    JWAVE = "jwave"
    LAST_FM = "last_fm"


class SimilarityType(str, Enum):
    """유사도 계산 타입"""
    CATEGORY = "category"
    DIFFICULTY = "difficulty"
    DURATION = "duration"
    METADATA = "metadata"
    USER_BEHAVIOR = "user_behavior"
    HYBRID = "hybrid"


class CalculationMethod(str, Enum):
    """유사도 계산 방법"""
    COSINE = "cosine"
    JACCARD = "jaccard"
    EUCLIDEAN = "euclidean"
    COLLABORATIVE = "collaborative"


# =============================================================================
# 추천 상호작용 모델
# =============================================================================

class RecommendationInteractionBase(BaseModel):
    """추천 상호작용 기본 모델"""
    user_id: UUID
    script_id: UUID
    recommendation_type: RecommendationType
    recommendation_score: float = Field(ge=0.0, le=1.0)
    algorithm_version: str = "v1.0"
    interaction_type: InteractionType
    interaction_duration: Optional[int] = None
    context_data: Dict[str, Any] = Field(default_factory=dict)
    feedback_score: Optional[int] = Field(None, ge=1, le=5)


class RecommendationInteractionCreate(RecommendationInteractionBase):
    """추천 상호작용 생성 요청"""
    pass


class RecommendationInteractionUpdate(BaseModel):
    """추천 상호작용 업데이트 요청"""
    interaction_duration: Optional[int] = None
    feedback_score: Optional[int] = Field(None, ge=1, le=5)
    context_data: Optional[Dict[str, Any]] = None


class RecommendationInteractionResponse(RecommendationInteractionBase, TimestampedModel):
    """추천 상호작용 응답"""
    id: UUID
    interaction_quality: Optional[float] = Field(None, ge=0.0, le=1.0)


# =============================================================================
# 외부 콘텐츠 소스 모델
# =============================================================================

class ExternalContentSourceBase(BaseModel):
    """외부 콘텐츠 소스 기본 모델"""
    source_name: ExternalSource
    external_id: str
    external_url: Optional[str] = None
    title: str
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    duration: Optional[int] = None  # 초 단위
    release_date: Optional[date] = None
    content_data: Dict[str, Any] = Field(default_factory=dict)
    popularity_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    trend_factor: float = 1.0


class ExternalContentSourceCreate(ExternalContentSourceBase):
    """외부 콘텐츠 소스 생성 요청"""
    pass


class ExternalContentSourceUpdate(BaseModel):
    """외부 콘텐츠 소스 업데이트 요청"""
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    duration: Optional[int] = None
    release_date: Optional[date] = None
    content_data: Optional[Dict[str, Any]] = None
    popularity_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    trend_factor: Optional[float] = None
    linked_script_id: Optional[UUID] = None
    match_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_active: Optional[bool] = None


class ExternalContentSourceResponse(ExternalContentSourceBase, TimestampedModel):
    """외부 콘텐츠 소스 응답"""
    id: UUID
    linked_script_id: Optional[UUID] = None
    auto_matched: bool = False
    match_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    last_synced: datetime
    sync_version: int = 1
    is_active: bool = True


# =============================================================================
# 추천 메트릭 모델
# =============================================================================

class RecommendationMetricsBase(BaseModel):
    """추천 메트릭 기본 모델"""
    algorithm_version: str
    algorithm_type: AlgorithmType
    click_through_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    completion_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    user_satisfaction_score: Optional[float] = Field(None, ge=1.0, le=5.0)
    precision_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    recall_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    diversity_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    novelty_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    measurement_period_start: datetime
    measurement_period_end: datetime
    sample_size: int = Field(gt=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('measurement_period_end')
    def validate_period(cls, v, values):
        if 'measurement_period_start' in values and v <= values['measurement_period_start']:
            raise ValueError('measurement_period_end must be after measurement_period_start')
        return v


class RecommendationMetricsCreate(RecommendationMetricsBase):
    """추천 메트릭 생성 요청"""
    pass


class RecommendationMetricsResponse(RecommendationMetricsBase):
    """추천 메트릭 응답"""
    id: UUID
    measured_at: datetime


# =============================================================================
# 사용자 추천 선호도 모델
# =============================================================================

class UserRecommendationPreferencesBase(BaseModel):
    """사용자 추천 선호도 기본 모델"""
    preferred_categories: List[str] = Field(default_factory=list)
    preferred_difficulty_levels: List[str] = Field(default_factory=list)
    preferred_duration_range: List[int] = Field(default_factory=list)  # [최소분, 최대분]
    learned_preferences: Dict[str, Any] = Field(default_factory=dict)
    preference_weights: Dict[str, Any] = Field(default_factory=dict)
    enable_personalization: bool = True
    enable_trending: bool = True
    enable_similar_content: bool = True
    enable_collaborative: bool = True
    exclude_categories: List[str] = Field(default_factory=list)
    exclude_explicit_content: bool = False
    min_quality_score: float = 0.0

    @validator('preferred_duration_range')
    def validate_duration_range(cls, v):
        if v and len(v) == 2 and v[0] > v[1]:
            raise ValueError('Duration range: minimum must be less than maximum')
        return v


class UserRecommendationPreferencesCreate(UserRecommendationPreferencesBase):
    """사용자 추천 선호도 생성 요청"""
    user_id: UUID


class UserRecommendationPreferencesUpdate(BaseModel):
    """사용자 추천 선호도 업데이트 요청"""
    preferred_categories: Optional[List[str]] = None
    preferred_difficulty_levels: Optional[List[str]] = None
    preferred_duration_range: Optional[List[int]] = None
    enable_personalization: Optional[bool] = None
    enable_trending: Optional[bool] = None
    enable_similar_content: Optional[bool] = None
    enable_collaborative: Optional[bool] = None
    exclude_categories: Optional[List[str]] = None
    exclude_explicit_content: Optional[bool] = None
    min_quality_score: Optional[float] = None


class UserRecommendationPreferencesResponse(UserRecommendationPreferencesBase, TimestampedModel):
    """사용자 추천 선호도 응답"""
    id: UUID
    user_id: UUID
    last_updated_by_user: Optional[datetime] = None
    last_learned_update: datetime


# =============================================================================
# 콘텐츠 유사도 모델
# =============================================================================

class ContentSimilarityBase(BaseModel):
    """콘텐츠 유사도 기본 모델"""
    source_script_id: UUID
    target_script_id: UUID
    similarity_score: float = Field(ge=0.0, le=1.0)
    similarity_type: SimilarityType
    calculation_method: CalculationMethod
    calculation_version: str = "v1.0"
    feature_weights: Dict[str, Any] = Field(default_factory=dict)
    similarity_details: Dict[str, Any] = Field(default_factory=dict)

    @validator('target_script_id')
    def validate_different_scripts(cls, v, values):
        if 'source_script_id' in values and v == values['source_script_id']:
            raise ValueError('Source and target script IDs must be different')
        return v


class ContentSimilarityCreate(ContentSimilarityBase):
    """콘텐츠 유사도 생성 요청"""
    pass


class ContentSimilarityResponse(ContentSimilarityBase):
    """콘텐츠 유사도 응답"""
    id: UUID
    calculated_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# 추천 요청/응답 모델
# =============================================================================

class RecommendationRequest(BaseModel):
    """추천 요청"""
    user_id: Optional[UUID] = None
    limit: int = Field(10, ge=1, le=50)
    category: Optional[str] = None
    difficulty: Optional[str] = None
    min_duration: Optional[int] = Field(None, ge=0)
    max_duration: Optional[int] = Field(None, ge=0)
    exclude_completed: bool = True
    include_trending: bool = True

    @validator('max_duration')
    def validate_duration_range(cls, v, values):
        if v is not None and 'min_duration' in values and values['min_duration'] is not None:
            if v < values['min_duration']:
                raise ValueError('max_duration must be greater than min_duration')
        return v


class ScriptRecommendationItem(BaseModel):
    """추천 스크립트 아이템"""
    id: UUID
    title: str
    description: Optional[str] = None
    category: str
    difficulty_level: str
    duration: Optional[int] = None
    thumbnail_url: Optional[str] = None
    audio_url: Optional[str] = None
    
    # 추천 관련 정보
    recommendation_score: float = Field(ge=0.0, le=1.0)
    recommendation_reason: Optional[str] = None
    similarity_to_source: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # 메타데이터
    popularity_score: Optional[float] = None
    trending_factor: Optional[float] = None
    external_source_info: Optional[Dict[str, Any]] = None


class PersonalizedRecommendationResponse(BaseModel):
    """개인화 추천 응답"""
    user_id: UUID
    recommendations: List[ScriptRecommendationItem]
    algorithm_version: str = "v1.0"
    generated_at: datetime
    total_available: int
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


class TrendingContentResponse(BaseModel):
    """트렌딩 콘텐츠 응답"""
    trending_items: List[ScriptRecommendationItem]
    period: str  # day, week, month
    generated_at: datetime
    total_trending: int


class SimilarContentResponse(BaseModel):
    """유사 콘텐츠 추천 응답"""
    source_script_id: UUID
    similar_items: List[ScriptRecommendationItem]
    similarity_algorithm: str
    generated_at: datetime
    total_similar: int


# =============================================================================
# 추천 피드백 모델
# =============================================================================

class RecommendationFeedback(BaseModel):
    """추천 피드백"""
    user_id: UUID
    script_id: UUID
    recommendation_type: RecommendationType
    feedback_type: str  # 'like', 'dislike', 'not_interested', 'inappropriate'
    feedback_score: int = Field(ge=1, le=5)
    feedback_comment: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class RecommendationFeedbackResponse(RecommendationFeedback):
    """추천 피드백 응답"""
    id: UUID
    processed_at: datetime
    impact_on_future_recommendations: str  # 'high', 'medium', 'low'


# =============================================================================
# 배치 처리 모델
# =============================================================================

class BatchRecommendationRequest(BaseModel):
    """배치 추천 요청"""
    user_ids: List[UUID] = Field(min_items=1, max_items=100)
    recommendation_types: List[RecommendationType] = Field(min_items=1)
    limit_per_user: int = Field(10, ge=1, le=20)
    common_filters: Optional[Dict[str, Any]] = None


class BatchRecommendationResponse(BaseModel):
    """배치 추천 응답"""
    results: Dict[str, PersonalizedRecommendationResponse]  # user_id -> recommendations
    batch_id: str
    processed_at: datetime
    processing_time_ms: int
    success_count: int
    failure_count: int
    failures: List[Dict[str, str]] = Field(default_factory=list)  # user_id -> error_message


# =============================================================================
# 성능 분석 모델
# =============================================================================

class RecommendationPerformanceAnalysis(BaseModel):
    """추천 성능 분석"""
    algorithm_type: AlgorithmType
    time_period: str
    metrics: Dict[str, float]
    top_performing_categories: List[str]
    user_engagement_trends: Dict[str, Any]
    recommendation_distribution: Dict[str, int]
    quality_scores: Dict[str, float]


class ABTestResult(BaseModel):
    """A/B 테스트 결과"""
    test_name: str
    variant_a: str
    variant_b: str
    sample_size_a: int
    sample_size_b: int
    conversion_rate_a: float
    conversion_rate_b: float
    statistical_significance: float
    confidence_interval: List[float]
    recommendation: str  # 'use_a', 'use_b', 'no_difference', 'need_more_data'


# =============================================================================
# 검색 및 필터링 모델
# =============================================================================

class RecommendationSearchFilters(BaseModel):
    """추천 검색 필터"""
    categories: Optional[List[str]] = None
    difficulty_levels: Optional[List[str]] = None
    duration_range: Optional[List[int]] = None  # [min_minutes, max_minutes]
    genres: Optional[List[str]] = None
    sources: Optional[List[ExternalSource]] = None
    min_popularity_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    min_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    exclude_explicit: bool = False
    only_trending: bool = False
    date_range: Optional[List[date]] = None  # [start_date, end_date]

    @validator('duration_range')
    def validate_duration_range(cls, v):
        if v and len(v) == 2 and v[0] > v[1]:
            raise ValueError('Duration range: minimum must be less than maximum')
        return v

    @validator('date_range')
    def validate_date_range(cls, v):
        if v and len(v) == 2 and v[0] > v[1]:
            raise ValueError('Date range: start_date must be before end_date')
        return v


class RecommendationSearchRequest(BaseModel):
    """추천 검색 요청"""
    user_id: Optional[UUID] = None
    query: Optional[str] = None
    filters: Optional[RecommendationSearchFilters] = None
    sort_by: str = "recommendation_score"  # recommendation_score, popularity, release_date, duration
    sort_order: str = Field("desc", regex="^(asc|desc)$")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class RecommendationSearchResponse(BaseModel):
    """추천 검색 응답"""
    items: List[ScriptRecommendationItem]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    filters_applied: Optional[RecommendationSearchFilters] = None
    search_query: Optional[str] = None
    search_time_ms: int 