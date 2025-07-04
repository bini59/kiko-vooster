-- Migration: 08_create_recommendation_tables.sql
-- Description: 추천 라디오/애니 OST 시스템 테이블 생성
-- Created: 2024-01-XX
-- Dependencies: 01_create_base_tables.sql

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- 1. RECOMMENDATION_INTERACTIONS 테이블
-- 사용자의 추천 콘텐츠 상호작용 추적 (클릭, 재생, 북마크 등)
-- =============================================================================

CREATE TABLE recommendation_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    script_id UUID NOT NULL REFERENCES scripts(id) ON DELETE CASCADE,
    
    -- 추천 정보
    recommendation_type VARCHAR(50) NOT NULL CHECK (recommendation_type IN ('personalized', 'trending', 'similar', 'category_based', 'collaborative')),
    recommendation_score FLOAT NOT NULL DEFAULT 0.0 CHECK (recommendation_score >= 0.0 AND recommendation_score <= 1.0),
    algorithm_version VARCHAR(20) NOT NULL DEFAULT 'v1.0',
    
    -- 사용자 상호작용
    interaction_type VARCHAR(20) NOT NULL CHECK (interaction_type IN ('view', 'play', 'bookmark', 'skip', 'complete', 'share')),
    interaction_duration INTEGER, -- 상호작용 지속 시간 (초)
    interaction_quality FLOAT CHECK (interaction_quality >= 0.0 AND interaction_quality <= 1.0), -- 상호작용 품질 점수
    
    -- 컨텍스트 정보
    context_data JSONB DEFAULT '{}', -- 추천 당시의 컨텍스트 (시간, 디바이스, 위치 등)
    feedback_score INTEGER CHECK (feedback_score >= 1 AND feedback_score <= 5), -- 사용자 피드백 점수 (1-5)
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 추천 상호작용 테이블 코멘트
COMMENT ON TABLE recommendation_interactions IS '사용자의 추천 콘텐츠 상호작용 추적 테이블 - 추천 성능 분석용';
COMMENT ON COLUMN recommendation_interactions.recommendation_score IS '추천 점수 (0.0-1.0): 알고리즘이 계산한 추천 신뢰도';
COMMENT ON COLUMN recommendation_interactions.interaction_quality IS '상호작용 품질 점수: 재생 시간, 완료율 등을 종합한 품질 지표';
COMMENT ON COLUMN recommendation_interactions.context_data IS '추천 컨텍스트: {"time_of_day": "morning", "device": "mobile", "session_duration": 1800}';

-- =============================================================================
-- 2. EXTERNAL_CONTENT_SOURCES 테이블
-- 외부 API에서 가져온 콘텐츠 메타데이터 저장
-- =============================================================================

CREATE TABLE external_content_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 외부 소스 정보
    source_name VARCHAR(50) NOT NULL CHECK (source_name IN ('spotify', 'apple_music', 'youtube_music', 'nhk', 'jwave', 'last_fm')),
    external_id VARCHAR(200) NOT NULL,
    external_url VARCHAR(500),
    
    -- 콘텐츠 정보
    title VARCHAR(200) NOT NULL,
    artist VARCHAR(100),
    album VARCHAR(100),
    genre VARCHAR(50),
    duration INTEGER, -- 재생 시간 (초)
    release_date DATE,
    
    -- 메타데이터
    content_data JSONB NOT NULL DEFAULT '{}',
    popularity_score FLOAT CHECK (popularity_score >= 0.0 AND popularity_score <= 100.0),
    trend_factor FLOAT DEFAULT 1.0,
    
    -- 연결된 내부 콘텐츠
    linked_script_id UUID REFERENCES scripts(id) ON DELETE SET NULL,
    auto_matched BOOLEAN DEFAULT FALSE, -- 자동 매칭 여부
    match_confidence FLOAT CHECK (match_confidence >= 0.0 AND match_confidence <= 1.0),
    
    -- 동기화 정보
    last_synced TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sync_version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 유니크 제약조건
    UNIQUE(source_name, external_id)
);

-- 외부 콘텐츠 소스 테이블 코멘트
COMMENT ON TABLE external_content_sources IS '외부 API 콘텐츠 메타데이터 저장 테이블 - Spotify, NHK 등 외부 소스 연동';
COMMENT ON COLUMN external_content_sources.content_data IS '외부 소스별 추가 메타데이터: {"anime_title": "Attack on Titan", "season": 3, "chart_position": 15}';
COMMENT ON COLUMN external_content_sources.match_confidence IS '내부 콘텐츠 매칭 신뢰도: 자동 매칭 시 정확도 점수';

-- =============================================================================
-- 3. RECOMMENDATION_METRICS 테이블
-- 추천 알고리즘 성능 메트릭 저장
-- =============================================================================

CREATE TABLE recommendation_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 알고리즘 정보
    algorithm_version VARCHAR(20) NOT NULL,
    algorithm_type VARCHAR(50) NOT NULL CHECK (algorithm_type IN ('personalized', 'trending', 'similar', 'category_based', 'collaborative', 'hybrid')),
    
    -- 성능 메트릭
    click_through_rate FLOAT CHECK (click_through_rate >= 0.0 AND click_through_rate <= 1.0),
    completion_rate FLOAT CHECK (completion_rate >= 0.0 AND completion_rate <= 1.0),
    user_satisfaction_score FLOAT CHECK (user_satisfaction_score >= 1.0 AND user_satisfaction_score <= 5.0),
    
    -- 추가 지표
    precision_score FLOAT CHECK (precision_score >= 0.0 AND precision_score <= 1.0),
    recall_score FLOAT CHECK (recall_score >= 0.0 AND recall_score <= 1.0),
    diversity_score FLOAT CHECK (diversity_score >= 0.0 AND diversity_score <= 1.0),
    novelty_score FLOAT CHECK (novelty_score >= 0.0 AND novelty_score <= 1.0),
    
    -- 측정 정보
    measurement_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    measurement_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    sample_size INTEGER NOT NULL CHECK (sample_size > 0),
    
    -- 메타데이터
    metadata JSONB DEFAULT '{}',
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 제약조건
    CONSTRAINT valid_measurement_period CHECK (measurement_period_end > measurement_period_start)
);

-- 추천 메트릭 테이블 코멘트
COMMENT ON TABLE recommendation_metrics IS '추천 알고리즘 성능 메트릭 저장 테이블 - A/B 테스트 및 성능 모니터링용';
COMMENT ON COLUMN recommendation_metrics.diversity_score IS '추천 다양성 점수: 추천 목록의 카테고리/장르 다양성 측정';
COMMENT ON COLUMN recommendation_metrics.novelty_score IS '추천 신규성 점수: 사용자가 접하지 않은 새로운 콘텐츠 비율';

-- =============================================================================
-- 4. USER_RECOMMENDATION_PREFERENCES 테이블
-- 사용자별 추천 선호도 설정 및 학습된 선호도 저장
-- =============================================================================

CREATE TABLE user_recommendation_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 명시적 선호도 설정
    preferred_categories TEXT[] DEFAULT '{}',
    preferred_difficulty_levels TEXT[] DEFAULT '{}',
    preferred_duration_range INTEGER[] DEFAULT '{}', -- [최소분, 최대분]
    
    -- 학습된 선호도 (알고리즘 추론)
    learned_preferences JSONB DEFAULT '{}',
    preference_weights JSONB DEFAULT '{}', -- 각 요소별 가중치
    
    -- 추천 개인화 설정
    enable_personalization BOOLEAN DEFAULT TRUE,
    enable_trending BOOLEAN DEFAULT TRUE,
    enable_similar_content BOOLEAN DEFAULT TRUE,
    enable_collaborative BOOLEAN DEFAULT TRUE,
    
    -- 필터 설정
    exclude_categories TEXT[] DEFAULT '{}',
    exclude_explicit_content BOOLEAN DEFAULT FALSE,
    min_quality_score FLOAT DEFAULT 0.0,
    
    -- 메타데이터
    last_updated_by_user TIMESTAMP WITH TIME ZONE,
    last_learned_update TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 유니크 제약조건
    UNIQUE(user_id)
);

-- 사용자 추천 선호도 테이블 코멘트
COMMENT ON TABLE user_recommendation_preferences IS '사용자별 추천 선호도 설정 및 학습된 선호도 저장 테이블';
COMMENT ON COLUMN user_recommendation_preferences.learned_preferences IS '알고리즘이 학습한 선호도: {"genre_anime": 0.8, "time_morning": 0.6, "duration_short": 0.7}';
COMMENT ON COLUMN user_recommendation_preferences.preference_weights IS '선호도 요소별 가중치: {"category": 0.4, "difficulty": 0.3, "duration": 0.2, "time": 0.1}';

-- =============================================================================
-- 5. CONTENT_SIMILARITY_MATRIX 테이블
-- 콘텐츠 간 유사도 매트릭스 (콘텐츠 기반 추천용)
-- =============================================================================

CREATE TABLE content_similarity_matrix (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_script_id UUID NOT NULL REFERENCES scripts(id) ON DELETE CASCADE,
    target_script_id UUID NOT NULL REFERENCES scripts(id) ON DELETE CASCADE,
    
    -- 유사도 점수
    similarity_score FLOAT NOT NULL CHECK (similarity_score >= 0.0 AND similarity_score <= 1.0),
    similarity_type VARCHAR(50) NOT NULL CHECK (similarity_type IN ('category', 'difficulty', 'duration', 'metadata', 'user_behavior', 'hybrid')),
    
    -- 유사도 계산 정보
    calculation_method VARCHAR(50) NOT NULL, -- 'cosine', 'jaccard', 'euclidean', 'collaborative'
    calculation_version VARCHAR(20) DEFAULT 'v1.0',
    
    -- 유사도 세부사항
    feature_weights JSONB DEFAULT '{}', -- 유사도 계산에 사용된 피처별 가중치
    similarity_details JSONB DEFAULT '{}', -- 세부 유사도 점수들
    
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE, -- 유사도 만료 시간 (재계산 필요)
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 제약조건
    CONSTRAINT no_self_similarity CHECK (source_script_id != target_script_id),
    -- 중복 방지: (A,B)와 (B,A)는 같은 것으로 처리
    CONSTRAINT unique_similarity_pair UNIQUE (LEAST(source_script_id, target_script_id), GREATEST(source_script_id, target_script_id), similarity_type)
);

-- 콘텐츠 유사도 매트릭스 테이블 코멘트
COMMENT ON TABLE content_similarity_matrix IS '콘텐츠 간 유사도 매트릭스 테이블 - 콘텐츠 기반 추천 알고리즘용';
COMMENT ON COLUMN content_similarity_matrix.feature_weights IS '유사도 계산 피처 가중치: {"category": 0.3, "difficulty": 0.2, "duration": 0.2, "keywords": 0.3}';
COMMENT ON COLUMN content_similarity_matrix.similarity_details IS '세부 유사도 점수: {"category_sim": 0.9, "difficulty_sim": 0.7, "keyword_sim": 0.8}';

-- =============================================================================
-- 인덱스 생성 (성능 최적화)
-- =============================================================================

-- recommendation_interactions 테이블 인덱스
CREATE INDEX idx_rec_interactions_user_id ON recommendation_interactions(user_id);
CREATE INDEX idx_rec_interactions_script_id ON recommendation_interactions(script_id);
CREATE INDEX idx_rec_interactions_type ON recommendation_interactions(user_id, recommendation_type);
CREATE INDEX idx_rec_interactions_created_at ON recommendation_interactions(created_at DESC);
CREATE INDEX idx_rec_interactions_quality ON recommendation_interactions(user_id, interaction_quality DESC);

-- external_content_sources 테이블 인덱스
CREATE INDEX idx_external_content_source ON external_content_sources(source_name);
CREATE INDEX idx_external_content_external_id ON external_content_sources(external_id);
CREATE INDEX idx_external_content_popularity ON external_content_sources(popularity_score DESC);
CREATE INDEX idx_external_content_active ON external_content_sources(is_active, last_synced DESC);
CREATE INDEX idx_external_content_linked_script ON external_content_sources(linked_script_id);

-- recommendation_metrics 테이블 인덱스
CREATE INDEX idx_rec_metrics_algorithm ON recommendation_metrics(algorithm_version, algorithm_type);
CREATE INDEX idx_rec_metrics_measured_at ON recommendation_metrics(measured_at DESC);
CREATE INDEX idx_rec_metrics_period ON recommendation_metrics(measurement_period_start, measurement_period_end);

-- user_recommendation_preferences 테이블 인덱스
CREATE INDEX idx_user_rec_prefs_user_id ON user_recommendation_preferences(user_id);
CREATE INDEX idx_user_rec_prefs_categories ON user_recommendation_preferences USING gin(preferred_categories);
CREATE INDEX idx_user_rec_prefs_updated ON user_recommendation_preferences(last_learned_update DESC);

-- content_similarity_matrix 테이블 인덱스
CREATE INDEX idx_content_sim_source ON content_similarity_matrix(source_script_id);
CREATE INDEX idx_content_sim_target ON content_similarity_matrix(target_script_id);
CREATE INDEX idx_content_sim_score ON content_similarity_matrix(similarity_score DESC);
CREATE INDEX idx_content_sim_type ON content_similarity_matrix(similarity_type, is_active);
CREATE INDEX idx_content_sim_expires ON content_similarity_matrix(expires_at) WHERE expires_at IS NOT NULL;

-- =============================================================================
-- 트리거 및 함수 생성
-- =============================================================================

-- updated_at 자동 갱신 트리거
CREATE TRIGGER update_rec_interactions_updated_at 
    BEFORE UPDATE ON recommendation_interactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_external_content_updated_at 
    BEFORE UPDATE ON external_content_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_rec_prefs_updated_at 
    BEFORE UPDATE ON user_recommendation_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 추천 상호작용 품질 점수 자동 계산 함수
CREATE OR REPLACE FUNCTION calculate_interaction_quality()
RETURNS TRIGGER AS $$
BEGIN
    -- 상호작용 지속 시간과 타입에 기반한 품질 점수 계산
    CASE NEW.interaction_type
        WHEN 'view' THEN
            NEW.interaction_quality := LEAST(1.0, COALESCE(NEW.interaction_duration, 0) / 30.0); -- 30초 이상 = 1.0
        WHEN 'play' THEN
            NEW.interaction_quality := LEAST(1.0, COALESCE(NEW.interaction_duration, 0) / 60.0); -- 1분 이상 = 1.0
        WHEN 'complete' THEN
            NEW.interaction_quality := 1.0;
        WHEN 'bookmark' THEN
            NEW.interaction_quality := 0.8;
        WHEN 'share' THEN
            NEW.interaction_quality := 0.9;
        WHEN 'skip' THEN
            NEW.interaction_quality := 0.1;
        ELSE
            NEW.interaction_quality := 0.5;
    END CASE;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 상호작용 품질 점수 자동 계산 트리거
CREATE TRIGGER calculate_interaction_quality_trigger
    BEFORE INSERT OR UPDATE ON recommendation_interactions
    FOR EACH ROW EXECUTE FUNCTION calculate_interaction_quality();

-- 유사도 만료 시간 자동 설정 함수
CREATE OR REPLACE FUNCTION set_similarity_expiration()
RETURNS TRIGGER AS $$
BEGIN
    -- 유사도 계산 후 30일 후 만료 설정
    NEW.expires_at := NEW.calculated_at + INTERVAL '30 days';
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 유사도 만료 시간 설정 트리거
CREATE TRIGGER set_similarity_expiration_trigger
    BEFORE INSERT ON content_similarity_matrix
    FOR EACH ROW EXECUTE FUNCTION set_similarity_expiration();

-- 성공 메시지
SELECT '✅ 추천 시스템 테이블 생성 완료' as status,
       'recommendation_interactions, external_content_sources, recommendation_metrics, user_recommendation_preferences, content_similarity_matrix' as created_tables; 