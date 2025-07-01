-- Migration: 03_setup_rls.sql
-- Description: Row-Level Security 정책 설정
-- Created: 2024-01-XX

-- RLS 활성화
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_words ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_scripts_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookmarks ENABLE ROW LEVEL SECURITY;

-- 공개 테이블은 RLS 비활성화 (모든 사용자가 읽기 가능)
ALTER TABLE scripts DISABLE ROW LEVEL SECURITY;
ALTER TABLE sentences DISABLE ROW LEVEL SECURITY;
ALTER TABLE words DISABLE ROW LEVEL SECURITY;

-- 사용자 테이블 정책
CREATE POLICY "users_own_data" ON users
    FOR ALL USING (auth.uid() = id);

-- 사용자 단어장 정책
CREATE POLICY "user_words_own_data" ON user_words
    FOR ALL USING (auth.uid() = user_id);

-- 학습 진행률 정책
CREATE POLICY "progress_own_data" ON user_scripts_progress
    FOR ALL USING (auth.uid() = user_id);

-- 북마크 정책
CREATE POLICY "bookmarks_own_data" ON bookmarks
    FOR ALL USING (auth.uid() = user_id);

-- 공개 콘텐츠 읽기 정책 (RLS가 비활성화되어 있지만 명시적으로 설정)
CREATE POLICY "scripts_read_all" ON scripts FOR SELECT USING (true);
CREATE POLICY "sentences_read_all" ON sentences FOR SELECT USING (true);
CREATE POLICY "words_read_all" ON words FOR SELECT USING (true);

-- 관리자 전용 쓰기 정책 (공개 콘텐츠)
CREATE POLICY "scripts_admin_write" ON scripts 
    FOR INSERT WITH CHECK (auth.jwt() ->> 'role' = 'admin');
CREATE POLICY "scripts_admin_update" ON scripts 
    FOR UPDATE USING (auth.jwt() ->> 'role' = 'admin');
CREATE POLICY "scripts_admin_delete" ON scripts 
    FOR DELETE USING (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "sentences_admin_write" ON sentences 
    FOR INSERT WITH CHECK (auth.jwt() ->> 'role' = 'admin');
CREATE POLICY "sentences_admin_update" ON sentences 
    FOR UPDATE USING (auth.jwt() ->> 'role' = 'admin');
CREATE POLICY "sentences_admin_delete" ON sentences 
    FOR DELETE USING (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "words_admin_write" ON words 
    FOR INSERT WITH CHECK (auth.jwt() ->> 'role' = 'admin');
CREATE POLICY "words_admin_update" ON words 
    FOR UPDATE USING (auth.jwt() ->> 'role' = 'admin');
CREATE POLICY "words_admin_delete" ON words 
    FOR DELETE USING (auth.jwt() ->> 'role' = 'admin');

-- 성공 메시지
SELECT 'RLS policies created successfully' as status; 