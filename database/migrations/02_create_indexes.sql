-- Migration: 02_create_indexes.sql
-- Description: 성능 최적화 인덱스 생성
-- Created: 2024-01-XX

-- users 테이블 인덱스
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_japanese_level ON users(japanese_level);
CREATE INDEX idx_users_last_login ON users(last_login);

-- scripts 테이블 인덱스
CREATE INDEX idx_scripts_category ON scripts(category);
CREATE INDEX idx_scripts_difficulty ON scripts(difficulty_level);
CREATE INDEX idx_scripts_created_at ON scripts(created_at DESC);
CREATE INDEX idx_scripts_duration ON scripts(duration);
CREATE INDEX idx_scripts_category_difficulty ON scripts(category, difficulty_level, created_at DESC);

-- sentences 테이블 인덱스
CREATE INDEX idx_sentences_script_id ON sentences(script_id);
CREATE INDEX idx_sentences_order ON sentences(script_id, order_index);
CREATE INDEX idx_sentences_time_range ON sentences(script_id, start_time, end_time);
CREATE INDEX idx_sentences_difficulty ON sentences(difficulty_level);
CREATE INDEX idx_sentences_script_time ON sentences(script_id, start_time);

-- words 테이블 인덱스
CREATE INDEX idx_words_text ON words(text);
CREATE INDEX idx_words_reading ON words(reading);
CREATE INDEX idx_words_difficulty ON words(difficulty_level);
CREATE INDEX idx_words_part_of_speech ON words(part_of_speech);

-- 전문 검색을 위한 GIN 인덱스 (PostgreSQL 15 지원)
CREATE INDEX idx_words_text_search ON words 
USING gin(to_tsvector('japanese', coalesce(text, '') || ' ' || coalesce(reading, '') || ' ' || coalesce(meaning, '')));

-- user_words 테이블 인덱스
CREATE INDEX idx_user_words_user_id ON user_words(user_id);
CREATE INDEX idx_user_words_mastery ON user_words(user_id, mastery_level);
CREATE INDEX idx_user_words_review_due ON user_words(user_id, next_review);
CREATE INDEX idx_user_words_tags ON user_words USING gin(tags);
CREATE INDEX idx_user_words_added_at ON user_words(user_id, added_at DESC);
CREATE INDEX idx_user_words_review_schedule ON user_words(user_id, next_review, mastery_level);

-- user_scripts_progress 테이블 인덱스
CREATE INDEX idx_progress_user_id ON user_scripts_progress(user_id);
CREATE INDEX idx_progress_script_id ON user_scripts_progress(script_id);
CREATE INDEX idx_progress_last_played ON user_scripts_progress(user_id, last_played DESC);
CREATE INDEX idx_progress_completed ON user_scripts_progress(user_id, completed);
CREATE INDEX idx_progress_stats ON user_scripts_progress(user_id, completed, last_played DESC);

-- bookmarks 테이블 인덱스
CREATE INDEX idx_bookmarks_user_id ON bookmarks(user_id);
CREATE INDEX idx_bookmarks_type ON bookmarks(user_id, bookmark_type);
CREATE INDEX idx_bookmarks_created_at ON bookmarks(user_id, created_at DESC);

-- 성공 메시지
SELECT 'Indexes created successfully' as status; 