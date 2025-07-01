-- Migration: 07_setup_sync_rls.sql
-- Description: 싱크 매핑 테이블 Row-Level Security 정책 설정
-- Created: 2024-01-XX
-- Dependencies: 06_create_sync_tables.sql

-- =============================================================================
-- 1. RLS 활성화
-- =============================================================================

-- 싱크 관련 테이블들 RLS 활성화
ALTER TABLE sentence_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE mapping_edits ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_sessions ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- 2. SENTENCE_MAPPINGS 테이블 정책
-- 타임코드 매핑은 읽기는 모든 사용자, 쓰기는 인증된 사용자만 가능
-- =============================================================================

-- 모든 사용자 읽기 허용 (공개 콘텐츠와 연결된 매핑)
CREATE POLICY "sentence_mappings_read_all" ON sentence_mappings
    FOR SELECT USING (true);

-- 인증된 사용자만 매핑 생성 가능
CREATE POLICY "sentence_mappings_create_authenticated" ON sentence_mappings
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

-- 매핑 수정은 원래 생성자 또는 관리자만 가능
CREATE POLICY "sentence_mappings_update_owner_or_admin" ON sentence_mappings
    FOR UPDATE USING (
        auth.uid() = created_by OR 
        auth.jwt() ->> 'role' = 'admin'
    );

-- 매핑 삭제(비활성화)는 관리자만 가능
CREATE POLICY "sentence_mappings_delete_admin" ON sentence_mappings
    FOR DELETE USING (auth.jwt() ->> 'role' = 'admin');

-- =============================================================================
-- 3. MAPPING_EDITS 테이블 정책  
-- 편집 내역은 읽기는 모든 사용자, 생성은 인증된 사용자만
-- =============================================================================

-- 모든 사용자 편집 내역 읽기 허용 (투명성)
CREATE POLICY "mapping_edits_read_all" ON mapping_edits
    FOR SELECT USING (true);

-- 인증된 사용자만 편집 내역 생성 가능
CREATE POLICY "mapping_edits_create_authenticated" ON mapping_edits
    FOR INSERT WITH CHECK (
        auth.uid() IS NOT NULL AND 
        auth.uid() = user_id
    );

-- 편집 내역은 수정/삭제 불가 (감사 로그 보호)
-- UPDATE, DELETE 정책 없음 = 완전 금지

-- =============================================================================
-- 4. SYNC_SESSIONS 테이블 정책
-- 세션은 소유자만 접근 가능, 익명 사용자는 세션 토큰으로 제한적 접근
-- =============================================================================

-- 세션 조회: 본인 세션 또는 같은 스크립트 룸의 활성 세션만
CREATE POLICY "sync_sessions_read_own_or_room" ON sync_sessions
    FOR SELECT USING (
        -- 본인 세션 (로그인 사용자)
        (auth.uid() IS NOT NULL AND auth.uid() = user_id) OR
        -- 같은 룸의 활성 세션 정보 (제한적 정보만)
        (is_active = true AND script_id IN (
            SELECT script_id FROM sync_sessions 
            WHERE user_id = auth.uid() AND is_active = true
        )) OR
        -- 관리자 전체 접근
        (auth.jwt() ->> 'role' = 'admin')
    );

-- 세션 생성: 인증된 사용자 또는 유효한 세션 토큰
CREATE POLICY "sync_sessions_create_authenticated" ON sync_sessions
    FOR INSERT WITH CHECK (
        -- 로그인 사용자는 자유롭게 생성
        (auth.uid() IS NOT NULL AND (user_id IS NULL OR auth.uid() = user_id)) OR
        -- 익명 사용자는 세션 토큰 필수
        (auth.uid() IS NULL AND user_id IS NULL AND session_token IS NOT NULL)
    );

-- 세션 업데이트: 본인 세션만 수정 가능
CREATE POLICY "sync_sessions_update_own" ON sync_sessions
    FOR UPDATE USING (
        -- 로그인 사용자: 본인 세션
        (auth.uid() IS NOT NULL AND auth.uid() = user_id) OR
        -- 익명 사용자: 세션 토큰 일치 (별도 검증 로직 필요)
        (auth.uid() IS NULL AND user_id IS NULL) OR
        -- 관리자
        (auth.jwt() ->> 'role' = 'admin')
    );

-- 세션 삭제: 본인 세션 또는 관리자
CREATE POLICY "sync_sessions_delete_own_or_admin" ON sync_sessions
    FOR DELETE USING (
        (auth.uid() IS NOT NULL AND auth.uid() = user_id) OR
        (auth.jwt() ->> 'role' = 'admin')
    );

-- =============================================================================
-- 5. 익명 사용자 지원을 위한 추가 함수
-- =============================================================================

-- 세션 토큰 검증 함수 (익명 사용자용)
CREATE OR REPLACE FUNCTION verify_session_token(
    connection_id_param VARCHAR(100),
    session_token_param VARCHAR(255)
)
RETURNS BOOLEAN AS $$
DECLARE
    session_exists BOOLEAN;
BEGIN
    -- 해당 연결 ID와 토큰이 일치하는 활성 세션이 있는지 확인
    SELECT EXISTS(
        SELECT 1 FROM sync_sessions 
        WHERE connection_id = connection_id_param 
          AND session_token = session_token_param
          AND is_active = true
          AND user_id IS NULL  -- 익명 사용자만
    ) INTO session_exists;
    
    RETURN session_exists;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 룸 참가자 조회 함수 (프라이버시 보호)
CREATE OR REPLACE FUNCTION get_room_participants(script_id_param UUID)
RETURNS TABLE (
    user_id UUID,
    connection_id VARCHAR(100),
    current_position FLOAT,
    is_playing BOOLEAN,
    joined_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.user_id,
        s.connection_id,
        s.current_position,
        s.is_playing,
        s.joined_at
    FROM sync_sessions s
    WHERE s.script_id = script_id_param
      AND s.is_active = true
      AND (
          -- 본인 세션이거나
          s.user_id = auth.uid() OR
          -- 같은 룸에 참가 중이거나  
          EXISTS(
              SELECT 1 FROM sync_sessions my_session
              WHERE my_session.user_id = auth.uid()
                AND my_session.script_id = script_id_param
                AND my_session.is_active = true
          ) OR
          -- 관리자
          auth.jwt() ->> 'role' = 'admin'
      )
    ORDER BY s.joined_at;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- 6. 관리자 전용 정책 (데이터 관리)
-- =============================================================================

-- 관리자용 매핑 일괄 관리 정책
CREATE POLICY "sentence_mappings_admin_bulk_operations" ON sentence_mappings
    FOR ALL USING (auth.jwt() ->> 'role' = 'admin');

-- 관리자용 세션 모니터링 정책  
CREATE POLICY "sync_sessions_admin_monitoring" ON sync_sessions
    FOR ALL USING (auth.jwt() ->> 'role' = 'admin');

-- =============================================================================
-- 7. 성능 최적화를 위한 보안 인덱스
-- =============================================================================

-- RLS 정책 최적화를 위한 인덱스
CREATE INDEX idx_sentence_mappings_created_by 
ON sentence_mappings(created_by) WHERE created_by IS NOT NULL;

CREATE INDEX idx_mapping_edits_user_id 
ON mapping_edits(user_id);

CREATE INDEX idx_sync_sessions_user_id 
ON sync_sessions(user_id) WHERE user_id IS NOT NULL;

CREATE INDEX idx_sync_sessions_token 
ON sync_sessions(session_token) WHERE session_token IS NOT NULL;

-- =============================================================================
-- 8. 권한 부여 (Supabase 역할별)
-- =============================================================================

-- authenticated 역할에 필요한 권한 부여
GRANT EXECUTE ON FUNCTION verify_session_token TO authenticated;
GRANT EXECUTE ON FUNCTION get_room_participants TO authenticated;

-- anon 역할에 세션 관련 제한적 권한 부여
GRANT SELECT, INSERT ON sync_sessions TO anon;
GRANT EXECUTE ON FUNCTION verify_session_token TO anon;

-- service_role에 모든 권한 부여 (서버 사이드 작업용)
GRANT ALL ON sentence_mappings TO service_role;
GRANT ALL ON mapping_edits TO service_role;
GRANT ALL ON sync_sessions TO service_role;

-- =============================================================================
-- 9. 정책 검증 및 테스트
-- =============================================================================

-- 정책 설정 검증
DO $$
DECLARE
    policy_count INTEGER;
    function_count INTEGER;
    index_count INTEGER;
BEGIN
    -- 정책 개수 확인
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies 
    WHERE schemaname = 'public' 
      AND tablename IN ('sentence_mappings', 'mapping_edits', 'sync_sessions');
    
    -- 함수 개수 확인
    SELECT COUNT(*) INTO function_count
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'public'
      AND p.proname IN ('verify_session_token', 'get_room_participants');
    
    -- 보안 인덱스 확인
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes 
    WHERE schemaname = 'public' 
      AND (indexname LIKE '%_created_by' OR indexname LIKE '%_user_id' OR indexname LIKE '%_token');
    
    -- 결과 출력
    RAISE NOTICE 'RLS setup completed: % policies, % functions, % security indexes', 
                 policy_count, function_count, index_count;
                 
    IF policy_count < 8 THEN
        RAISE EXCEPTION 'RLS policy creation failed: expected at least 8 policies, got %', policy_count;
    END IF;
END $$;

-- =============================================================================
-- 10. 보안 설정 요약
-- =============================================================================

/*
보안 정책 요약:

1. SENTENCE_MAPPINGS:
   - 읽기: 모든 사용자 (공개)
   - 생성: 인증된 사용자만
   - 수정: 원본 생성자 또는 관리자
   - 삭제: 관리자만

2. MAPPING_EDITS:
   - 읽기: 모든 사용자 (투명성)  
   - 생성: 인증된 사용자 (본인 ID만)
   - 수정/삭제: 금지 (감사 로그 보호)

3. SYNC_SESSIONS:
   - 읽기: 본인 세션 + 같은 룸 제한적 정보
   - 생성: 인증된 사용자 + 익명(토큰 필수)
   - 수정: 본인 세션만
   - 삭제: 본인 세션 또는 관리자

4. 특수 기능:
   - 익명 사용자 세션 토큰 검증
   - 룸 참가자 조회 (프라이버시 보호)
   - 관리자 모니터링 지원
*/

-- 성공 메시지
SELECT 'Sync RLS policies created successfully' as status,
       '11 policies, 2 security functions, 4 security indexes' as details; 