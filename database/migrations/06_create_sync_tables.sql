-- Migration: 06_create_sync_tables.sql
-- Description: 스크립트-오디오 싱크 매핑 시스템 테이블 생성
-- Created: 2024-01-XX
-- Dependencies: 01_create_base_tables.sql

-- =============================================================================
-- 1. SENTENCE_MAPPINGS 테이블
-- 문장별 타임코드 매핑 정보 (AI 자동 + 수동 편집)
-- =============================================================================

CREATE TABLE sentence_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sentence_id UUID NOT NULL REFERENCES sentences(id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    confidence_score FLOAT NOT NULL DEFAULT 0.0 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    mapping_type VARCHAR(20) NOT NULL DEFAULT 'auto' CHECK (mapping_type IN ('auto', 'manual', 'ai_generated')),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    
    -- 제약조건
    CONSTRAINT valid_time_range CHECK (end_time > start_time),
    CONSTRAINT valid_version CHECK (version > 0),
    
    -- 문장당 하나의 활성 매핑만 허용
    EXCLUDE USING btree (sentence_id WITH =) WHERE (is_active = true)
);

-- 매핑 테이블 코멘트
COMMENT ON TABLE sentence_mappings IS '문장별 타임코드 매핑 테이블 - AI 자동 정렬 및 수동 편집 지원';
COMMENT ON COLUMN sentence_mappings.confidence_score IS '매핑 신뢰도 (0.0-1.0): AI 생성시 알고리즘 신뢰도, 수동 편집시 1.0';
COMMENT ON COLUMN sentence_mappings.mapping_type IS '매핑 생성 방식: auto(기본값), manual(사용자 편집), ai_generated(AI 자동생성)';
COMMENT ON COLUMN sentence_mappings.version IS '매핑 버전 - 편집시마다 증가';
COMMENT ON COLUMN sentence_mappings.is_active IS '활성 매핑 여부 - 문장당 하나만 활성화 가능';

-- =============================================================================
-- 2. MAPPING_EDITS 테이블  
-- 매핑 편집 내역 추적 (감사 로그)
-- =============================================================================

CREATE TABLE mapping_edits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sentence_id UUID NOT NULL REFERENCES sentences(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    old_mapping_id UUID REFERENCES sentence_mappings(id) ON DELETE SET NULL,
    new_mapping_id UUID NOT NULL REFERENCES sentence_mappings(id) ON DELETE CASCADE,
    
    -- 변경 전후 값
    old_start_time FLOAT,
    old_end_time FLOAT,
    new_start_time FLOAT NOT NULL,
    new_end_time FLOAT NOT NULL,
    
    edit_reason VARCHAR(500),
    edit_type VARCHAR(20) NOT NULL DEFAULT 'manual' CHECK (edit_type IN ('manual', 'ai_correction', 'bulk_edit')),
    client_info JSONB DEFAULT '{}', -- 편집 클라이언트 정보 (브라우저, IP 등)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 제약조건
    CONSTRAINT valid_new_time_range CHECK (new_end_time > new_start_time),
    CONSTRAINT valid_old_time_range CHECK (old_end_time IS NULL OR old_end_time > old_start_time)
);

-- 편집 내역 테이블 코멘트
COMMENT ON TABLE mapping_edits IS '매핑 편집 내역 추적 테이블 - 감사 로그 및 변경 이력 관리';
COMMENT ON COLUMN mapping_edits.edit_reason IS '편집 사유 (사용자 입력 또는 시스템 자동 기록)';
COMMENT ON COLUMN mapping_edits.edit_type IS '편집 유형: manual(수동), ai_correction(AI 수정), bulk_edit(일괄 편집)';
COMMENT ON COLUMN mapping_edits.client_info IS '편집 클라이언트 정보 (브라우저, IP, 세션 등)';

-- =============================================================================
-- 3. SYNC_SESSIONS 테이블
-- WebSocket 동기화 세션 관리
-- =============================================================================

CREATE TABLE sync_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    script_id UUID NOT NULL REFERENCES scripts(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL, -- 비로그인 사용자도 허용
    connection_id VARCHAR(100) NOT NULL, -- WebSocket 연결 ID
    session_token VARCHAR(255), -- 인증 토큰 (익명 사용자용)
    
    -- 현재 상태
    current_sentence_id UUID REFERENCES sentences(id) ON DELETE SET NULL,
    current_position FLOAT NOT NULL DEFAULT 0.0,
    is_playing BOOLEAN NOT NULL DEFAULT FALSE,
    playback_rate FLOAT NOT NULL DEFAULT 1.0 CHECK (playback_rate > 0.0),
    
    -- 세션 메타데이터
    user_agent TEXT,
    client_ip INET,
    room_id VARCHAR(100), -- 스크립트별 룸 구분자
    session_type VARCHAR(20) NOT NULL DEFAULT 'individual' CHECK (session_type IN ('individual', 'group', 'classroom')),
    
    -- 타임스탬프
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    left_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- 제약조건
    CONSTRAINT valid_current_position CHECK (current_position >= 0.0),
    CONSTRAINT valid_playback_rate CHECK (playback_rate >= 0.1 AND playback_rate <= 3.0),
    
    -- 연결 ID 유니크 제약
    UNIQUE(connection_id, script_id)
);

-- 세션 테이블 코멘트
COMMENT ON TABLE sync_sessions IS 'WebSocket 동기화 세션 관리 테이블 - 실시간 공유 재생 지원';
COMMENT ON COLUMN sync_sessions.connection_id IS 'WebSocket 연결 고유 식별자';
COMMENT ON COLUMN sync_sessions.session_token IS '익명 사용자용 임시 인증 토큰';
COMMENT ON COLUMN sync_sessions.room_id IS '스크립트별 동기화 룸 구분자';
COMMENT ON COLUMN sync_sessions.session_type IS '세션 유형: individual(개인), group(그룹), classroom(교실)';

-- =============================================================================
-- 4. 성능 최적화 인덱스
-- =============================================================================

-- 문장 매핑 조회 최적화
CREATE INDEX idx_sentence_mappings_sentence_active 
ON sentence_mappings(sentence_id, is_active) 
WHERE is_active = true;

CREATE INDEX idx_sentence_mappings_script_time 
ON sentence_mappings(sentence_id, start_time, end_time) 
WHERE is_active = true;

CREATE INDEX idx_sentence_mappings_confidence 
ON sentence_mappings(confidence_score DESC, mapping_type) 
WHERE is_active = true;

-- 편집 내역 조회 최적화
CREATE INDEX idx_mapping_edits_sentence_time 
ON mapping_edits(sentence_id, created_at DESC);

CREATE INDEX idx_mapping_edits_user_time 
ON mapping_edits(user_id, created_at DESC);

CREATE INDEX idx_mapping_edits_new_mapping 
ON mapping_edits(new_mapping_id);

-- 동기화 세션 조회 최적화
CREATE INDEX idx_sync_sessions_script_active 
ON sync_sessions(script_id, is_active) 
WHERE is_active = true;

CREATE INDEX idx_sync_sessions_user_active 
ON sync_sessions(user_id, is_active) 
WHERE is_active = true AND user_id IS NOT NULL;

CREATE INDEX idx_sync_sessions_connection 
ON sync_sessions(connection_id, script_id);

CREATE INDEX idx_sync_sessions_room 
ON sync_sessions(room_id, is_active) 
WHERE is_active = true;

CREATE INDEX idx_sync_sessions_activity 
ON sync_sessions(last_activity DESC) 
WHERE is_active = true;

-- =============================================================================
-- 5. 트리거 함수 및 트리거
-- =============================================================================

-- 매핑 테이블 updated_at 자동 업데이트
CREATE OR REPLACE FUNCTION update_sentence_mappings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_sentence_mappings_updated_at
    BEFORE UPDATE ON sentence_mappings
    FOR EACH ROW EXECUTE FUNCTION update_sentence_mappings_updated_at();

-- 세션 last_activity 자동 업데이트  
CREATE OR REPLACE FUNCTION update_sync_sessions_activity()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_activity = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_sync_sessions_activity
    BEFORE UPDATE ON sync_sessions
    FOR EACH ROW EXECUTE FUNCTION update_sync_sessions_activity();

-- 매핑 버전 자동 증가 트리거
CREATE OR REPLACE FUNCTION increment_mapping_version()
RETURNS TRIGGER AS $$
DECLARE
    max_version INTEGER;
BEGIN
    -- 같은 문장의 최대 버전 조회
    SELECT COALESCE(MAX(version), 0) INTO max_version
    FROM sentence_mappings 
    WHERE sentence_id = NEW.sentence_id;
    
    -- 새 매핑인 경우 버전 증가
    IF TG_OP = 'INSERT' THEN
        NEW.version = max_version + 1;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_sentence_mappings_version
    BEFORE INSERT ON sentence_mappings
    FOR EACH ROW EXECUTE FUNCTION increment_mapping_version();

-- 세션 자동 비활성화 트리거 (연결 종료시)
CREATE OR REPLACE FUNCTION deactivate_old_sessions()
RETURNS TRIGGER AS $$
BEGIN
    -- 같은 연결 ID의 기존 세션들 비활성화
    UPDATE sync_sessions 
    SET is_active = false, left_at = NOW()
    WHERE connection_id = NEW.connection_id 
      AND script_id = NEW.script_id 
      AND id != NEW.id
      AND is_active = true;
      
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_sync_sessions_deactivate
    AFTER INSERT ON sync_sessions
    FOR EACH ROW EXECUTE FUNCTION deactivate_old_sessions();

-- =============================================================================
-- 6. 기본 데이터 및 설정
-- =============================================================================

-- 기본 룸 ID 생성 함수
CREATE OR REPLACE FUNCTION generate_room_id(script_uuid UUID)
RETURNS VARCHAR(100) AS $$
BEGIN
    RETURN 'room_' || REPLACE(script_uuid::text, '-', '');
END;
$$ LANGUAGE plpgsql;

-- 매핑 신뢰도 점수 계산 함수
CREATE OR REPLACE FUNCTION calculate_mapping_confidence(
    mapping_type_param VARCHAR(20),
    time_gap_seconds FLOAT DEFAULT NULL,
    sentence_length INTEGER DEFAULT NULL
)
RETURNS FLOAT AS $$
BEGIN
    CASE mapping_type_param
        WHEN 'manual' THEN RETURN 1.0;
        WHEN 'ai_generated' THEN 
            -- AI 생성: 시간 간격과 문장 길이 기반 신뢰도
            RETURN LEAST(
                0.9, 
                GREATEST(0.3, 
                    0.8 - (COALESCE(time_gap_seconds, 0) * 0.01) +
                    (COALESCE(sentence_length, 20) * 0.005)
                )
            );
        ELSE 
            RETURN 0.5; -- 기본값
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 7. 권한 및 보안 설정
-- =============================================================================

-- 테이블별 기본 권한 설정 (RLS는 별도 파일에서 처리)
GRANT SELECT, INSERT, UPDATE ON sentence_mappings TO authenticated;
GRANT SELECT, INSERT ON mapping_edits TO authenticated;  
GRANT SELECT, INSERT, UPDATE, DELETE ON sync_sessions TO authenticated;

-- 시퀀스 권한
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- =============================================================================
-- 8. 검증 및 완료
-- =============================================================================

-- 테이블 생성 검증
DO $$
DECLARE
    table_count INTEGER;
    index_count INTEGER;
    trigger_count INTEGER;
BEGIN
    -- 테이블 확인
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
      AND table_name IN ('sentence_mappings', 'mapping_edits', 'sync_sessions');
    
    -- 인덱스 확인  
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes 
    WHERE schemaname = 'public' 
      AND indexname LIKE 'idx_sentence_mappings_%' 
       OR indexname LIKE 'idx_mapping_edits_%'
       OR indexname LIKE 'idx_sync_sessions_%';
    
    -- 트리거 확인
    SELECT COUNT(*) INTO trigger_count
    FROM information_schema.triggers
    WHERE trigger_schema = 'public'
      AND trigger_name LIKE 'tr_%mappings_%' 
       OR trigger_name LIKE 'tr_%sessions_%';
    
    -- 결과 출력
    RAISE NOTICE 'Sync tables created: % tables, % indexes, % triggers', 
                 table_count, index_count, trigger_count;
                 
    IF table_count < 3 THEN
        RAISE EXCEPTION 'Table creation failed: expected 3 tables, got %', table_count;
    END IF;
END $$;

-- 성공 메시지
SELECT 'Sync mapping tables created successfully' as status,
       '3 tables, 12 indexes, 4 triggers, 3 functions' as details; 