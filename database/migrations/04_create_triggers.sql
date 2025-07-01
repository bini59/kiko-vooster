-- Migration: 04_create_triggers.sql
-- Description: 자동화 트리거 및 검증 함수
-- Created: 2024-01-XX

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

-- 북마크 유효성 검증 함수
CREATE OR REPLACE FUNCTION validate_bookmark_target()
RETURNS TRIGGER AS $$
BEGIN
    -- 북마크 타입에 따라 해당 테이블에 target_id가 존재하는지 확인
    CASE NEW.bookmark_type
        WHEN 'script' THEN
            IF NOT EXISTS (SELECT 1 FROM scripts WHERE id = NEW.target_id) THEN
                RAISE EXCEPTION 'Script with id % does not exist', NEW.target_id;
            END IF;
        WHEN 'sentence' THEN
            IF NOT EXISTS (SELECT 1 FROM sentences WHERE id = NEW.target_id) THEN
                RAISE EXCEPTION 'Sentence with id % does not exist', NEW.target_id;
            END IF;
        WHEN 'word' THEN
            IF NOT EXISTS (SELECT 1 FROM words WHERE id = NEW.target_id) THEN
                RAISE EXCEPTION 'Word with id % does not exist', NEW.target_id;
            END IF;
        ELSE
            RAISE EXCEPTION 'Invalid bookmark type: %', NEW.bookmark_type;
    END CASE;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 북마크 유효성 트리거
CREATE TRIGGER validate_bookmark_target_trigger
    BEFORE INSERT OR UPDATE ON bookmarks
    FOR EACH ROW EXECUTE FUNCTION validate_bookmark_target();

-- 학습 통계 업데이트 함수
CREATE OR REPLACE FUNCTION update_learning_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- 스크립트 완료 시 통계 업데이트 로직
    -- 실제 구현에서는 별도 stats 테이블이나 materialized view 활용
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 학습 통계 트리거
CREATE TRIGGER update_learning_stats_trigger
    AFTER UPDATE OF completed ON user_scripts_progress
    FOR EACH ROW EXECUTE FUNCTION update_learning_stats();

-- 성공 메시지
SELECT 'Triggers and functions created successfully' as status; 