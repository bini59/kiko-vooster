-- Seed Data: 01_sample_data.sql
-- Description: 테스트 및 개발용 샘플 데이터
-- Created: 2024-01-XX

\echo '🌱 샘플 데이터 생성 중...'

-- ====================
-- 샘플 사용자 데이터
-- ====================

INSERT INTO users (id, email, name, japanese_level, preferences) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'demo@kiko.dev', '데모 사용자', 'beginner', '{"theme": "light", "language": "ko"}'),
('550e8400-e29b-41d4-a716-446655440002', 'test@example.com', '테스트 사용자', 'intermediate', '{"theme": "dark", "language": "ko"}'),
('550e8400-e29b-41d4-a716-446655440003', 'advanced@example.com', '고급 사용자', 'advanced', '{"theme": "auto", "language": "ko"}')
ON CONFLICT (email) DO NOTHING;

-- ====================
-- 샘플 스크립트 데이터
-- ====================

INSERT INTO scripts (id, title, description, audio_url, thumbnail_url, duration, difficulty_level, category, metadata) VALUES
('660e8400-e29b-41d4-a716-446655440001', 
 'NHK 뉴스 - 오늘의 날씨', 
 '일본 전국의 오늘 날씨 예보를 알려드립니다.',
 'https://example.com/audio/weather-news.mp3',
 'https://example.com/thumbnails/weather.jpg',
 300,
 'beginner',
 'news',
 '{"original_broadcast": "2024-01-15", "region": "nationwide"}'),

('660e8400-e29b-41d4-a716-446655440002',
 'ラジオ体操 - 기본 운동',
 '아침 라디오 체조의 기본 동작을 배워보세요.',
 'https://example.com/audio/radio-exercise.mp3', 
 'https://example.com/thumbnails/exercise.jpg',
 600,
 'beginner',
 'exercise',
 '{"instructor": "田中先生", "type": "basic"}'),

('660e8400-e29b-41d4-a716-446655440003',
 '아니메 OST - 봄의 멜로디',
 '인기 애니메이션의 오프닝 테마 해설과 함께 듣기.',
 'https://example.com/audio/anime-ost.mp3',
 'https://example.com/thumbnails/anime.jpg', 
 450,
 'intermediate',
 'anime',
 '{"anime_title": "Spring Melody", "season": "1", "episode": "opening"}')
ON CONFLICT (id) DO NOTHING;

-- ====================
-- 샘플 문장 데이터 (첫 번째 스크립트)
-- ====================

INSERT INTO sentences (script_id, text, reading, translation, start_time, end_time, order_index) VALUES
('660e8400-e29b-41d4-a716-446655440001', 
 'おはようございます。', 
 'おはようございます。',
 '안녕하세요.',
 0.0, 2.5, 0),

('660e8400-e29b-41d4-a716-446655440001',
 '今日の天気予報をお伝えします。',
 'きょうのてんきよほうをおつたえします。', 
 '오늘의 날씨 예보를 전해드립니다.',
 2.5, 6.8, 1),

('660e8400-e29b-41d4-a716-446655440001',
 '東京は晴れ時々曇りです。',
 'とうきょうははれときどきくもりです。',
 '도쿄는 맑음 가끔 흐림입니다.',
 6.8, 11.2, 2),

('660e8400-e29b-41d4-a716-446655440001',
 '最高気温は25度の予想です。',
 'さいこうきおんは25どのよそうです。',
 '최고기온은 25도로 예상됩니다.',
 11.2, 15.9, 3),

('660e8400-e29b-41d4-a716-446655440001',
 'お出かけの際は軽い上着をお持ちください。',
 'おでかけのさいはかるいうわぎをおもちください。',
 '외출 시에는 가벼운 겉옷을 가져가세요.',
 15.9, 21.3, 4);

-- 두 번째 스크립트 문장들
INSERT INTO sentences (script_id, text, reading, translation, start_time, end_time, order_index) VALUES
('660e8400-e29b-41d4-a716-446655440002',
 'みなさん、おはようございます。',
 'みなさん、おはようございます。',
 '여러분, 안녕하세요.',
 0.0, 3.2, 0),

('660e8400-e29b-41d4-a716-446655440002', 
 'ラジオ体操を始めましょう。',
 'ラジオたいそうをはじめましょう。',
 '라디오 체조를 시작합시다.',
 3.2, 6.8, 1),

('660e8400-e29b-41d4-a716-446655440002',
 '腕を大きく回してください。',
 'うでをおおきくまわしてください。',
 '팔을 크게 돌려주세요.',
 6.8, 10.5, 2);

-- ====================
-- 샘플 단어 데이터
-- ====================

INSERT INTO words (text, reading, meaning, part_of_speech, difficulty_level, example_sentence, example_translation) VALUES
('天気', 'てんき', '날씨', '명사', 'beginner', '今日の天気はいいです。', '오늘 날씨가 좋습니다.'),
('予報', 'よほう', '예보', '명사', 'beginner', '天気予報を見ます。', '날씨 예보를 봅니다.'),
('晴れ', 'はれ', '맑음', '명사', 'beginner', '今日は晴れです。', '오늘은 맑습니다.'),
('曇り', 'くもり', '흐림', '명사', 'beginner', '空が曇りです。', '하늘이 흐립니다.'),
('気温', 'きおん', '기온', '명사', 'intermediate', '今日の気温は高いです。', '오늘 기온이 높습니다.'),
('上着', 'うわぎ', '겉옷', '명사', 'intermediate', '寒いので上着を着ます。', '추우니까 겉옷을 입습니다.'),
('体操', 'たいそう', '체조', '명사', 'beginner', '毎朝体操をします。', '매일 아침 체조를 합니다.'),
('運動', 'うんどう', '운동', '명사', 'beginner', '運動は体にいいです。', '운동은 몸에 좋습니다.'),
('回す', 'まわす', '돌리다', '동사', 'intermediate', '腕を回します。', '팔을 돌립니다.'),
('始める', 'はじめる', '시작하다', '동사', 'beginner', '勉強を始めます。', '공부를 시작합니다.')
ON CONFLICT (text, reading, meaning) DO NOTHING;

-- ====================
-- 샘플 사용자 단어 데이터
-- ====================

INSERT INTO user_words (user_id, word_id, mastery_level, tags) VALUES 
-- 데모 사용자의 단어장
('550e8400-e29b-41d4-a716-446655440001', 
 (SELECT id FROM words WHERE text = '天気' LIMIT 1),
 2, ARRAY['날씨', '기초']),

('550e8400-e29b-41d4-a716-446655440001',
 (SELECT id FROM words WHERE text = '晴れ' LIMIT 1), 
 1, ARRAY['날씨', '기초']),

('550e8400-e29b-41d4-a716-446655440001',
 (SELECT id FROM words WHERE text = '体操' LIMIT 1),
 3, ARRAY['운동', '일상'])
ON CONFLICT (user_id, word_id) DO NOTHING;

-- ====================
-- 샘플 진행률 데이터
-- ====================

INSERT INTO user_scripts_progress (user_id, script_id, current_time, completed_sentences, completed) VALUES
('550e8400-e29b-41d4-a716-446655440001',
 '660e8400-e29b-41d4-a716-446655440001',
 11.2,
 ARRAY[(SELECT id FROM sentences WHERE script_id = '660e8400-e29b-41d4-a716-446655440001' AND order_index = 0 LIMIT 1),
       (SELECT id FROM sentences WHERE script_id = '660e8400-e29b-41d4-a716-446655440001' AND order_index = 1 LIMIT 1)],
 false),

('550e8400-e29b-41d4-a716-446655440002', 
 '660e8400-e29b-41d4-a716-446655440002',
 6.8,
 ARRAY[(SELECT id FROM sentences WHERE script_id = '660e8400-e29b-41d4-a716-446655440002' AND order_index = 0 LIMIT 1)],
 false)
ON CONFLICT (user_id, script_id) DO NOTHING;

-- ====================
-- 샘플 북마크 데이터  
-- ====================

INSERT INTO bookmarks (user_id, bookmark_type, target_id, notes) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'script', '660e8400-e29b-41d4-a716-446655440001', '날씨 뉴스 - 기초 학습용'),
('550e8400-e29b-41d4-a716-446655440001', 'word', (SELECT id FROM words WHERE text = '天気' LIMIT 1), '일상에서 자주 사용'),
('550e8400-e29b-41d4-a716-446655440002', 'sentence', (SELECT id FROM sentences WHERE text = 'ラジオ体操を始めましょう。' LIMIT 1), '좋은 표현')
ON CONFLICT (user_id, bookmark_type, target_id) DO NOTHING;

-- 성공 메시지
SELECT '✅ 샘플 데이터 생성 완료' as status,
       (SELECT COUNT(*) FROM users) as users_count,
       (SELECT COUNT(*) FROM scripts) as scripts_count, 
       (SELECT COUNT(*) FROM sentences) as sentences_count,
       (SELECT COUNT(*) FROM words) as words_count; 