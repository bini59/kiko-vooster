-- Migration: 07_create_notification_tables.sql
-- Description: 학습 리마인더 알림 시스템 테이블 생성
-- Created: 2024-01-XX
-- Dependencies: 01_create_base_tables.sql

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- 1. NOTIFICATIONS 테이블
-- 개별 알림 레코드 (발송된 알림들의 이력)
-- =============================================================================

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 알림 기본 정보
    type VARCHAR(50) NOT NULL CHECK (type IN ('learning_reminder', 'achievement', 'vocabulary_review', 'streak_reminder', 'system_announcement')),
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('email', 'web_push', 'in_app')),
    
    -- 알림 내용
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    action_url VARCHAR(500), -- 클릭 시 이동할 URL
    
    -- 개인화 데이터
    template_variables JSONB DEFAULT '{}', -- 템플릿 변수들 (이름, 학습 통계 등)
    
    -- 발송 상태
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'opened', 'failed', 'cancelled')),
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    
    -- 실패/재시도 관리
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    failure_reason TEXT,
    
    -- 메타데이터
    metadata JSONB DEFAULT '{}', -- 추가 정보 (추적 ID, A/B 테스트 그룹 등)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 알림 테이블 코멘트
COMMENT ON TABLE notifications IS '개별 알림 발송 이력 및 상태 추적';
COMMENT ON COLUMN notifications.type IS '알림 유형: learning_reminder(학습 리마인더), achievement(성취 알림), vocabulary_review(복습 알림), streak_reminder(연속 학습), system_announcement(시스템 공지)';
COMMENT ON COLUMN notifications.channel IS '발송 채널: email(이메일), web_push(웹푸시), in_app(앱 내 알림)';
COMMENT ON COLUMN notifications.template_variables IS '템플릿 변수 JSON: {"user_name": "김영희", "days_streak": 5, "words_to_review": 12}';
COMMENT ON COLUMN notifications.metadata IS '추가 메타데이터: {"campaign_id": "winter_2024", "ab_test_group": "A"}';

-- =============================================================================
-- 2. NOTIFICATION_SCHEDULES 테이블
-- 사용자별 알림 스케줄 설정
-- =============================================================================

CREATE TABLE notification_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 스케줄 기본 정보
    type VARCHAR(50) NOT NULL CHECK (type IN ('learning_reminder', 'vocabulary_review', 'streak_reminder')),
    name VARCHAR(100) NOT NULL, -- 사용자 정의 스케줄 이름
    description TEXT,
    
    -- 스케줄 설정
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('daily', 'weekly', 'custom')),
    
    -- 시간 설정 
    preferred_time TIME NOT NULL DEFAULT '09:00:00', -- 선호 시간 (사용자 로컬 타임존)
    timezone VARCHAR(50) NOT NULL DEFAULT 'Asia/Seoul', -- 사용자 타임존
    
    -- 요일 설정 (weekly/custom용)
    days_of_week INTEGER[] DEFAULT '{1,2,3,4,5}', -- 1=월, 2=화, ..., 7=일
    
    -- 커스텀 간격 설정
    custom_interval_hours INTEGER, -- 커스텀 주기 (시간 단위)
    
    -- 다음 실행 시간
    next_execution TIMESTAMP WITH TIME ZONE,
    last_executed TIMESTAMP WITH TIME ZONE,
    
    -- 조건부 실행 설정
    conditions JSONB DEFAULT '{}', -- 실행 조건 {"min_inactive_hours": 24, "min_words_to_review": 5}
    
    -- 메타데이터
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 유니크 제약 (사용자당 유형별 하나의 스케줄)
    UNIQUE(user_id, type)
);

-- 스케줄 테이블 코멘트
COMMENT ON TABLE notification_schedules IS '사용자별 알림 스케줄 설정 및 관리';
COMMENT ON COLUMN notification_schedules.days_of_week IS '요일 배열 (1=월요일, 7=일요일)';
COMMENT ON COLUMN notification_schedules.conditions IS '실행 조건 JSON: {"min_inactive_hours": 24, "requires_review_words": true}';

-- =============================================================================
-- 3. NOTIFICATION_SUBSCRIPTIONS 테이블
-- 웹푸시 구독 정보 관리
-- =============================================================================

CREATE TABLE notification_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 구독 정보
    endpoint VARCHAR(500) NOT NULL, -- Push service endpoint
    p256dh_key VARCHAR(500) NOT NULL, -- Public key for encryption
    auth_key VARCHAR(500) NOT NULL, -- Authentication secret
    
    -- 브라우저/디바이스 정보
    user_agent TEXT,
    browser_name VARCHAR(50),
    browser_version VARCHAR(20),
    device_type VARCHAR(20) CHECK (device_type IN ('desktop', 'mobile', 'tablet')),
    
    -- 구독 설정
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    notification_types TEXT[] DEFAULT '{"learning_reminder", "vocabulary_review"}', -- 구독할 알림 유형들
    
    -- 권한 및 상태
    permission_granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 에러 추적
    error_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    last_error_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 유니크 제약 (같은 endpoint는 하나만)
    UNIQUE(endpoint)
);

-- 구독 테이블 코멘트
COMMENT ON TABLE notification_subscriptions IS '웹푸시 알림 구독 정보 및 권한 관리';
COMMENT ON COLUMN notification_subscriptions.endpoint IS 'Web Push API 엔드포인트 URL';
COMMENT ON COLUMN notification_subscriptions.p256dh_key IS '메시지 암호화용 공개키';
COMMENT ON COLUMN notification_subscriptions.auth_key IS '인증용 비밀키';

-- =============================================================================
-- 4. NOTIFICATION_TEMPLATES 테이블
-- 알림 템플릿 관리
-- =============================================================================

CREATE TABLE notification_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 템플릿 기본 정보
    type VARCHAR(50) NOT NULL,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('email', 'web_push', 'in_app')),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- 템플릿 내용
    subject_template VARCHAR(200), -- 이메일 제목 템플릿
    title_template VARCHAR(200) NOT NULL, -- 알림 제목 템플릿
    message_template TEXT NOT NULL, -- 메시지 본문 템플릿
    action_button_text VARCHAR(50), -- 액션 버튼 텍스트
    action_url_template VARCHAR(500), -- 액션 URL 템플릿
    
    -- 템플릿 설정
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    language VARCHAR(10) NOT NULL DEFAULT 'ko',
    version INTEGER NOT NULL DEFAULT 1,
    
    -- A/B 테스트 지원
    ab_test_group VARCHAR(10), -- 'A', 'B', 'control' 등
    traffic_percentage INTEGER NOT NULL DEFAULT 100 CHECK (traffic_percentage >= 0 AND traffic_percentage <= 100),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 유니크 제약
    UNIQUE(type, channel, language, version)
);

-- 템플릿 테이블 코멘트
COMMENT ON TABLE notification_templates IS '알림 템플릿 및 A/B 테스트 관리';
COMMENT ON COLUMN notification_templates.subject_template IS '템플릿 변수 사용 가능: "{{user_name}}님, 오늘의 학습을 시작해보세요!"';
COMMENT ON COLUMN notification_templates.traffic_percentage IS 'A/B 테스트용 트래픽 비율 (0-100%)';

-- =============================================================================
-- 5. 인덱스 생성
-- =============================================================================

-- notifications 테이블 인덱스
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_type_channel ON notifications(type, channel);
CREATE INDEX idx_notifications_sent_at ON notifications(sent_at DESC);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX idx_notifications_retry ON notifications(status, retry_count) WHERE status = 'failed';

-- notification_schedules 테이블 인덱스
CREATE INDEX idx_notification_schedules_user_id ON notification_schedules(user_id);
CREATE INDEX idx_notification_schedules_enabled ON notification_schedules(is_enabled) WHERE is_enabled = true;
CREATE INDEX idx_notification_schedules_execution ON notification_schedules(next_execution) WHERE is_enabled = true;
CREATE INDEX idx_notification_schedules_type ON notification_schedules(type);

-- notification_subscriptions 테이블 인덱스
CREATE INDEX idx_notification_subscriptions_user_id ON notification_subscriptions(user_id);
CREATE INDEX idx_notification_subscriptions_active ON notification_subscriptions(is_active) WHERE is_active = true;
CREATE INDEX idx_notification_subscriptions_endpoint ON notification_subscriptions(endpoint);
CREATE INDEX idx_notification_subscriptions_last_used ON notification_subscriptions(last_used_at DESC);

-- notification_templates 테이블 인덱스
CREATE INDEX idx_notification_templates_type_channel ON notification_templates(type, channel);
CREATE INDEX idx_notification_templates_active ON notification_templates(is_active) WHERE is_active = true;
CREATE INDEX idx_notification_templates_language ON notification_templates(language);

-- =============================================================================
-- 6. 트리거 및 함수
-- =============================================================================

-- updated_at 자동 갱신 트리거
CREATE TRIGGER update_notifications_updated_at 
    BEFORE UPDATE ON notifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_schedules_updated_at 
    BEFORE UPDATE ON notification_schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_subscriptions_updated_at 
    BEFORE UPDATE ON notification_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_templates_updated_at 
    BEFORE UPDATE ON notification_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 다음 실행 시간 자동 계산 함수
CREATE OR REPLACE FUNCTION calculate_next_notification_execution()
RETURNS TRIGGER AS $$
DECLARE
    next_exec TIMESTAMP WITH TIME ZONE;
BEGIN
    -- 빈도에 따른 다음 실행 시간 계산
    CASE NEW.frequency
        WHEN 'daily' THEN
            next_exec := (CURRENT_DATE + INTERVAL '1 day' + NEW.preferred_time) AT TIME ZONE NEW.timezone;
        WHEN 'weekly' THEN
            -- 다음 주 같은 요일로 설정 (복잡한 로직은 별도 함수로 분리 예정)
            next_exec := (CURRENT_DATE + INTERVAL '7 days' + NEW.preferred_time) AT TIME ZONE NEW.timezone;
        WHEN 'custom' THEN
            IF NEW.custom_interval_hours IS NOT NULL THEN
                next_exec := NOW() + (NEW.custom_interval_hours || ' hours')::INTERVAL;
            ELSE
                next_exec := (CURRENT_DATE + INTERVAL '1 day' + NEW.preferred_time) AT TIME ZONE NEW.timezone;
            END IF;
    END CASE;
    
    NEW.next_execution := next_exec;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 스케줄 실행 시간 계산 트리거
CREATE TRIGGER calculate_next_execution_trigger
    BEFORE INSERT OR UPDATE OF frequency, preferred_time, timezone, custom_interval_hours ON notification_schedules
    FOR EACH ROW EXECUTE FUNCTION calculate_next_notification_execution();

-- 구독 만료 관리 함수
CREATE OR REPLACE FUNCTION cleanup_expired_subscriptions()
RETURNS INTEGER AS $$
DECLARE
    expired_count INTEGER;
BEGIN
    -- 30일 이상 사용되지 않은 구독 비활성화
    UPDATE notification_subscriptions 
    SET is_active = false, 
        updated_at = NOW()
    WHERE is_active = true 
      AND last_used_at < NOW() - INTERVAL '30 days';
      
    GET DIAGNOSTICS expired_count = ROW_COUNT;
    
    -- 에러가 5번 이상 발생한 구독 비활성화
    UPDATE notification_subscriptions 
    SET is_active = false, 
        updated_at = NOW()
    WHERE is_active = true 
      AND error_count >= 5;
      
    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

-- 알림 발송 상태 업데이트 함수
CREATE OR REPLACE FUNCTION update_notification_status(
    notification_id UUID,
    new_status VARCHAR(20),
    error_message TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    success BOOLEAN := false;
BEGIN
    UPDATE notifications 
    SET 
        status = new_status,
        sent_at = CASE WHEN new_status = 'sent' THEN NOW() ELSE sent_at END,
        delivered_at = CASE WHEN new_status = 'delivered' THEN NOW() ELSE delivered_at END,
        opened_at = CASE WHEN new_status = 'opened' THEN NOW() ELSE opened_at END,
        failure_reason = CASE WHEN new_status = 'failed' THEN error_message ELSE failure_reason END,
        retry_count = CASE WHEN new_status = 'failed' THEN retry_count + 1 ELSE retry_count END,
        updated_at = NOW()
    WHERE id = notification_id;
    
    GET DIAGNOSTICS success = FOUND;
    RETURN success;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 7. 기본 데이터 삽입
-- =============================================================================

-- 기본 알림 템플릿 삽입
INSERT INTO notification_templates (type, channel, name, title_template, message_template, language) VALUES
-- 학습 리마인더 (이메일)
('learning_reminder', 'email', '일일 학습 리마인더', 
 '{{user_name}}님, 오늘의 일본어 학습을 시작해보세요! 📚', 
 '안녕하세요 {{user_name}}님!\n\n{{days_since_last_study}}일 동안 학습하지 않으셨네요. 꾸준한 학습이 실력 향상의 지름길입니다.\n\n오늘 {{suggested_study_minutes}}분만 투자해서 일본어 실력을 늘려보는 것은 어떨까요?\n\n지금 바로 시작하기: {{action_url}}',
 'ko'),

-- 학습 리마인더 (웹푸시)
('learning_reminder', 'web_push', '일일 학습 리마인더', 
 '일본어 학습 시간이에요! 🌸', 
 '{{user_name}}님, {{target_study_time}}에 학습하기로 하셨는데 아직 시작하지 않으셨네요. 지금 바로 시작해보세요!',
 'ko'),

-- 단어 복습 리마인더 (이메일)
('vocabulary_review', 'email', '단어 복습 리마인더',
 '{{user_name}}님, {{review_words_count}}개의 단어가 복습을 기다리고 있어요! 📝',
 '안녕하세요 {{user_name}}님!\n\n단어장에 {{review_words_count}}개의 단어가 복습 예정입니다. 기억을 되살려 장기 기억으로 만들어보세요!\n\n예정된 복습 단어들:\n{{sample_words}}\n\n지금 복습하기: {{action_url}}',
 'ko'),

-- 단어 복습 리마인더 (웹푸시)
('vocabulary_review', 'web_push', '단어 복습 리마인더',
 '복습할 단어 {{review_words_count}}개 📚',
 '단어장에서 {{review_words_count}}개 단어가 복습을 기다리고 있어요. 지금 바로 복습해보세요!',
 'ko'),

-- 연속 학습 격려 (웹푸시)
('streak_reminder', 'web_push', '연속 학습 격려',
 '{{streak_days}}일 연속 학습 중! 🔥',
 '{{user_name}}님이 {{streak_days}}일 연속으로 학습하고 계시네요! 오늘도 연속 기록을 이어가보세요.',
 'ko');

-- =============================================================================
-- 8. Row-Level Security (RLS) 정책
-- =============================================================================

-- notifications 테이블 RLS 활성화 및 정책
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY notifications_select_policy ON notifications
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY notifications_insert_policy ON notifications
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY notifications_update_policy ON notifications
    FOR UPDATE USING (user_id = auth.uid());

-- notification_schedules 테이블 RLS
ALTER TABLE notification_schedules ENABLE ROW LEVEL SECURITY;

CREATE POLICY notification_schedules_all_policy ON notification_schedules
    FOR ALL USING (user_id = auth.uid());

-- notification_subscriptions 테이블 RLS
ALTER TABLE notification_subscriptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY notification_subscriptions_all_policy ON notification_subscriptions
    FOR ALL USING (user_id = auth.uid());

-- notification_templates는 모든 사용자가 읽기 가능 (관리자만 수정)
ALTER TABLE notification_templates ENABLE ROW LEVEL SECURITY;

CREATE POLICY notification_templates_select_policy ON notification_templates
    FOR SELECT USING (is_active = true);

-- =============================================================================
-- 9. 검증 및 완료
-- =============================================================================

-- 테이블 생성 검증
SELECT 'Notification tables created: ' || COUNT(*) as status 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('notifications', 'notification_schedules', 'notification_subscriptions', 'notification_templates');

-- 인덱스 생성 검증
SELECT 'Notification indexes created: ' || COUNT(*) as status 
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND tablename LIKE 'notification%';

-- 함수 생성 검증
SELECT 'Notification functions created: ' || COUNT(*) as status 
FROM pg_proc 
WHERE proname LIKE '%notification%';

-- 성공 메시지
SELECT '🎉 Notification system tables created successfully!' as status; 