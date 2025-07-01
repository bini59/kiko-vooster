-- 05_create_audio_tables.sql
-- 오디오 재생 관련 테이블 생성

-- 오디오 세션 테이블
CREATE TABLE IF NOT EXISTS audio_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    script_id UUID NOT NULL REFERENCES scripts(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_position FLOAT NOT NULL DEFAULT 0,
    last_sentence_id UUID REFERENCES sentences(id),
    total_duration FLOAT,
    playback_rate DECIMAL(2,1) NOT NULL DEFAULT 1.0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 오디오 북마크 테이블  
CREATE TABLE IF NOT EXISTS audio_bookmarks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    script_id UUID NOT NULL REFERENCES scripts(id) ON DELETE CASCADE,
    position FLOAT NOT NULL,
    sentence_id UUID REFERENCES sentences(id),
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 오디오 세션 인덱스
CREATE INDEX IF NOT EXISTS idx_audio_sessions_user_id ON audio_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_audio_sessions_script_id ON audio_sessions(script_id);
CREATE INDEX IF NOT EXISTS idx_audio_sessions_active ON audio_sessions(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_audio_sessions_started_at ON audio_sessions(started_at DESC);

-- 오디오 북마크 인덱스
CREATE INDEX IF NOT EXISTS idx_audio_bookmarks_user_id ON audio_bookmarks(user_id);
CREATE INDEX IF NOT EXISTS idx_audio_bookmarks_script_id ON audio_bookmarks(script_id);
CREATE INDEX IF NOT EXISTS idx_audio_bookmarks_position ON audio_bookmarks(position);

-- 복합 인덱스
CREATE INDEX IF NOT EXISTS idx_audio_sessions_user_script ON audio_sessions(user_id, script_id);
CREATE INDEX IF NOT EXISTS idx_audio_bookmarks_user_script ON audio_bookmarks(user_id, script_id);

-- 오디오 세션 업데이트 트리거
CREATE OR REPLACE FUNCTION update_audio_session_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_audio_sessions_updated_at
    BEFORE UPDATE ON audio_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_audio_session_timestamp();

-- 오디오 북마크 업데이트 트리거
CREATE TRIGGER update_audio_bookmarks_updated_at
    BEFORE UPDATE ON audio_bookmarks
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- 오디오 세션 RLS 정책
ALTER TABLE audio_sessions ENABLE ROW LEVEL SECURITY;

-- 사용자는 자신의 세션만 조회 가능
CREATE POLICY audio_sessions_select_policy ON audio_sessions
    FOR SELECT USING (auth.uid() = user_id);

-- 사용자는 자신의 세션만 생성 가능
CREATE POLICY audio_sessions_insert_policy ON audio_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- 사용자는 자신의 세션만 수정 가능
CREATE POLICY audio_sessions_update_policy ON audio_sessions
    FOR UPDATE USING (auth.uid() = user_id);

-- 사용자는 자신의 세션만 삭제 가능
CREATE POLICY audio_sessions_delete_policy ON audio_sessions
    FOR DELETE USING (auth.uid() = user_id);

-- 오디오 북마크 RLS 정책
ALTER TABLE audio_bookmarks ENABLE ROW LEVEL SECURITY;

-- 사용자는 자신의 북마크만 조회 가능
CREATE POLICY audio_bookmarks_select_policy ON audio_bookmarks
    FOR SELECT USING (auth.uid() = user_id);

-- 사용자는 자신의 북마크만 생성 가능
CREATE POLICY audio_bookmarks_insert_policy ON audio_bookmarks
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- 사용자는 자신의 북마크만 수정 가능
CREATE POLICY audio_bookmarks_update_policy ON audio_bookmarks
    FOR UPDATE USING (auth.uid() = user_id);

-- 사용자는 자신의 북마크만 삭제 가능
CREATE POLICY audio_bookmarks_delete_policy ON audio_bookmarks
    FOR DELETE USING (auth.uid() = user_id);

-- 함수: 활성 세션 종료
CREATE OR REPLACE FUNCTION end_active_sessions(p_user_id UUID, p_script_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE audio_sessions
    SET is_active = false,
        ended_at = NOW()
    WHERE user_id = p_user_id
      AND script_id = p_script_id
      AND is_active = true;
END;
$$ LANGUAGE plpgsql;

-- 함수: 세션 통계 조회
CREATE OR REPLACE FUNCTION get_session_stats(p_user_id UUID)
RETURNS TABLE (
    total_sessions BIGINT,
    total_listening_time FLOAT,
    unique_scripts BIGINT,
    avg_session_duration FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_sessions,
        SUM(COALESCE(last_position, 0))::FLOAT as total_listening_time,
        COUNT(DISTINCT script_id)::BIGINT as unique_scripts,
        AVG(COALESCE(last_position, 0))::FLOAT as avg_session_duration
    FROM audio_sessions
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- 코멘트 추가
COMMENT ON TABLE audio_sessions IS '오디오 재생 세션 추적';
COMMENT ON TABLE audio_bookmarks IS '사용자 오디오 북마크';
COMMENT ON COLUMN audio_sessions.playback_rate IS '재생 속도 (0.5 ~ 2.0)';
COMMENT ON COLUMN audio_sessions.is_active IS '현재 활성 세션 여부';
COMMENT ON COLUMN audio_bookmarks.position IS '북마크 위치 (초 단위)'; 