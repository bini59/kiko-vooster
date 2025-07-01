-- Test Migration Script
-- 모든 마이그레이션을 순서대로 실행하는 통합 스크립트
-- Created: 2024-01-XX

\echo '🚀 Starting database migration...'

-- ====================
-- 01. CREATE BASE TABLES
-- ====================
\echo '📋 Creating base tables...'

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. users 테이블
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    japanese_level VARCHAR(20) DEFAULT 'beginner' CHECK (japanese_level IN ('beginner', 'intermediate', 'advanced')),
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- 2. scripts 테이블
CREATE TABLE IF NOT EXISTS scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    audio_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    duration INTEGER NOT NULL,
    difficulty_level VARCHAR(20) DEFAULT 'beginner' CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
    category VARCHAR(50) NOT NULL,
    language VARCHAR(10) DEFAULT 'japanese',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 제약조건
    CONSTRAINT valid_duration CHECK (duration > 0)
);

-- 3. sentences 테이블
CREATE TABLE IF NOT EXISTS sentences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    script_id UUID NOT NULL REFERENCES scripts(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    reading TEXT,
    translation TEXT NOT NULL,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    difficulty_level VARCHAR(20) DEFAULT 'beginner' CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
    order_index INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 제약조건
    CONSTRAINT valid_time_range CHECK (end_time > start_time),
    CONSTRAINT valid_order_index CHECK (order_index >= 0)
);

-- 4. words 테이블
CREATE TABLE IF NOT EXISTS words (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text VARCHAR(100) NOT NULL,
    reading VARCHAR(200),
    meaning TEXT NOT NULL,
    part_of_speech VARCHAR(50) NOT NULL,
    difficulty_level VARCHAR(20) DEFAULT 'beginner' CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
    example_sentence TEXT,
    example_translation TEXT,
    audio_url VARCHAR(500),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 유니크 제약조건
    UNIQUE(text, reading, meaning)
);

-- 5. user_words 테이블
CREATE TABLE IF NOT EXISTS user_words (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    word_id UUID NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    mastery_level INTEGER DEFAULT 0 CHECK (mastery_level >= 0 AND mastery_level <= 5),
    review_count INTEGER DEFAULT 0,
    tags TEXT[] DEFAULT '{}',
    notes TEXT,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_reviewed TIMESTAMP WITH TIME ZONE,
    next_review TIMESTAMP WITH TIME ZONE,
    
    -- 유니크 제약조건
    UNIQUE(user_id, word_id)
);

-- 6. user_scripts_progress 테이블
CREATE TABLE IF NOT EXISTS user_scripts_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    script_id UUID NOT NULL REFERENCES scripts(id) ON DELETE CASCADE,
    current_time FLOAT DEFAULT 0,
    completed_sentences UUID[] DEFAULT '{}',
    completed BOOLEAN DEFAULT FALSE,
    last_played TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 유니크 제약조건
    UNIQUE(user_id, script_id),
    
    -- 제약조건
    CONSTRAINT valid_current_time CHECK (current_time >= 0)
);

-- 7. bookmarks 테이블
CREATE TABLE IF NOT EXISTS bookmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bookmark_type VARCHAR(20) NOT NULL CHECK (bookmark_type IN ('script', 'sentence', 'word')),
    target_id UUID NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 유니크 제약조건
    UNIQUE(user_id, bookmark_type, target_id)
);

\echo '✅ Base tables created'

-- ====================
-- 02. CREATE INDEXES
-- ====================
\echo '🔍 Creating performance indexes...'

-- users 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_japanese_level ON users(japanese_level);
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login);

-- scripts 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_scripts_category ON scripts(category);
CREATE INDEX IF NOT EXISTS idx_scripts_difficulty ON scripts(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_scripts_created_at ON scripts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scripts_duration ON scripts(duration);
CREATE INDEX IF NOT EXISTS idx_scripts_category_difficulty ON scripts(category, difficulty_level, created_at DESC);

-- sentences 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_sentences_script_id ON sentences(script_id);
CREATE INDEX IF NOT EXISTS idx_sentences_order ON sentences(script_id, order_index);
CREATE INDEX IF NOT EXISTS idx_sentences_time_range ON sentences(script_id, start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_sentences_difficulty ON sentences(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_sentences_script_time ON sentences(script_id, start_time);

-- words 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_words_text ON words(text);
CREATE INDEX IF NOT EXISTS idx_words_reading ON words(reading);
CREATE INDEX IF NOT EXISTS idx_words_difficulty ON words(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_words_part_of_speech ON words(part_of_speech);

-- user_words 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_user_words_user_id ON user_words(user_id);
CREATE INDEX IF NOT EXISTS idx_user_words_mastery ON user_words(user_id, mastery_level);
CREATE INDEX IF NOT EXISTS idx_user_words_review_due ON user_words(user_id, next_review);
CREATE INDEX IF NOT EXISTS idx_user_words_tags ON user_words USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_user_words_added_at ON user_words(user_id, added_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_words_review_schedule ON user_words(user_id, next_review, mastery_level);

-- user_scripts_progress 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_progress_user_id ON user_scripts_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_progress_script_id ON user_scripts_progress(script_id);
CREATE INDEX IF NOT EXISTS idx_progress_last_played ON user_scripts_progress(user_id, last_played DESC);
CREATE INDEX IF NOT EXISTS idx_progress_completed ON user_scripts_progress(user_id, completed);
CREATE INDEX IF NOT EXISTS idx_progress_stats ON user_scripts_progress(user_id, completed, last_played DESC);

-- bookmarks 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_bookmarks_user_id ON bookmarks(user_id);
CREATE INDEX IF NOT EXISTS idx_bookmarks_type ON bookmarks(user_id, bookmark_type);
CREATE INDEX IF NOT EXISTS idx_bookmarks_created_at ON bookmarks(user_id, created_at DESC);

\echo '✅ Indexes created'

-- ====================
-- 03. FUNCTIONS AND TRIGGERS  
-- ====================
\echo '⚡ Creating functions and triggers...'

-- updated_at 자동 갱신 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- updated_at 트리거 생성
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scripts_updated_at 
    BEFORE UPDATE ON scripts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_words_updated_at 
    BEFORE UPDATE ON words
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_progress_updated_at 
    BEFORE UPDATE ON user_scripts_progress
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 문장 시간 범위 검증 함수
CREATE OR REPLACE FUNCTION validate_sentence_time_range()
RETURNS TRIGGER AS $$
BEGIN
    -- 스크립트 총 재생 시간 내에 있는지 확인
    IF EXISTS (
        SELECT 1 FROM scripts 
        WHERE id = NEW.script_id 
        AND NEW.end_time > duration
    ) THEN
        RAISE EXCEPTION 'Sentence end time (%) exceeds script duration', NEW.end_time;
    END IF;
    
    -- 시작 시간이 0 이상인지 확인
    IF NEW.start_time < 0 THEN
        RAISE EXCEPTION 'Sentence start time cannot be negative';
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 문장 시간 검증 트리거
CREATE TRIGGER validate_sentence_time 
    BEFORE INSERT OR UPDATE ON sentences
    FOR EACH ROW EXECUTE FUNCTION validate_sentence_time_range();

-- 복습 스케줄 자동 계산 함수
CREATE OR REPLACE FUNCTION calculate_next_review()
RETURNS TRIGGER AS $$
DECLARE
    interval_days INTEGER;
BEGIN
    -- 숙련도에 따른 복습 간격 계산 (간격 반복 학습법)
    CASE NEW.mastery_level
        WHEN 0 THEN interval_days := 1;    -- 1일
        WHEN 1 THEN interval_days := 3;    -- 3일
        WHEN 2 THEN interval_days := 7;    -- 1주
        WHEN 3 THEN interval_days := 14;   -- 2주
        WHEN 4 THEN interval_days := 30;   -- 1달
        WHEN 5 THEN interval_days := 90;   -- 3달
        ELSE interval_days := 1;
    END CASE;
    
    -- 다음 복습 날짜 설정
    NEW.next_review := NOW() + (interval_days || ' days')::INTERVAL;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 복습 스케줄 트리거
CREATE TRIGGER calculate_next_review_trigger
    BEFORE INSERT OR UPDATE OF mastery_level ON user_words
    FOR EACH ROW EXECUTE FUNCTION calculate_next_review();

\echo '✅ Functions and triggers created'

-- ====================
-- 04. VALIDATION QUERIES
-- ====================
\echo '🧪 Running validation queries...'

-- 테이블 생성 확인
SELECT 'Table count: ' || COUNT(*) as status FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name IN ('users', 'scripts', 'sentences', 'words', 'user_words', 'user_scripts_progress', 'bookmarks');

-- 인덱스 생성 확인
SELECT 'Index count: ' || COUNT(*) as status FROM pg_indexes 
WHERE schemaname = 'public';

-- 함수 생성 확인  
SELECT 'Function count: ' || COUNT(*) as status FROM pg_proc 
WHERE proname LIKE 'update_%' OR proname LIKE 'validate_%' OR proname LIKE 'calculate_%';

\echo '🎉 Migration completed successfully!'
\echo ''
\echo '✅ All tables, indexes, and triggers have been created.'
\echo '📊 Database schema is ready for application use.' 