"""
일본어 텍스트 처리 유틸리티

일본어 문자 검증, 변환, 분석 등의 기능을 제공합니다.
"""

import re
from typing import Optional, Dict, Any


def is_hiragana(text: str) -> bool:
    """텍스트가 히라가나인지 확인"""
    if not text:
        return False
    return all(0x3040 <= ord(char) <= 0x309F for char in text)


def is_katakana(text: str) -> bool:
    """텍스트가 가타카나인지 확인"""
    if not text:
        return False
    return all(0x30A0 <= ord(char) <= 0x30FF for char in text)


def is_kanji(text: str) -> bool:
    """텍스트가 한자인지 확인"""
    if not text:
        return False
    return all(0x4E00 <= ord(char) <= 0x9FAF for char in text)


def is_japanese(text: str) -> bool:
    """텍스트가 일본어인지 확인"""
    if not text:
        return False
    
    japanese_chars = 0
    total_chars = len(text)
    
    for char in text:
        char_code = ord(char)
        # 히라가나, 가타카나, 한자, 일본어 구두점
        if (0x3040 <= char_code <= 0x309F or  # 히라가나
            0x30A0 <= char_code <= 0x30FF or  # 가타카나
            0x4E00 <= char_code <= 0x9FAF or  # 한자
            0x3000 <= char_code <= 0x303F):   # 일본어 구두점/기호
            japanese_chars += 1
    
    # 50% 이상이 일본어 문자이면 일본어로 판단
    return japanese_chars / total_chars >= 0.5


def has_kanji(text: str) -> bool:
    """텍스트에 한자가 포함되어 있는지 확인"""
    if not text:
        return False
    return any(0x4E00 <= ord(char) <= 0x9FAF for char in text)


def count_character_types(text: str) -> Dict[str, int]:
    """텍스트의 문자 유형별 개수 계산"""
    counts = {
        "hiragana": 0,
        "katakana": 0,
        "kanji": 0,
        "ascii": 0,
        "other": 0
    }
    
    for char in text:
        char_code = ord(char)
        if 0x3040 <= char_code <= 0x309F:
            counts["hiragana"] += 1
        elif 0x30A0 <= char_code <= 0x30FF:
            counts["katakana"] += 1
        elif 0x4E00 <= char_code <= 0x9FAF:
            counts["kanji"] += 1
        elif 0x0000 <= char_code <= 0x007F:
            counts["ascii"] += 1
        else:
            counts["other"] += 1
    
    return counts


def normalize_japanese_text(text: str) -> str:
    """일본어 텍스트 정규화"""
    if not text:
        return ""
    
    # 앞뒤 공백 제거
    text = text.strip()
    
    # 전각 공백을 반각 공백으로 변환
    text = text.replace("　", " ")
    
    # 연속된 공백을 하나로 합치기
    text = re.sub(r"\s+", " ", text)
    
    # 특수 문자 정리 (선택적)
    # text = re.sub(r"[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\u3000-\u303F\w\s]", "", text)
    
    return text


def extract_reading_from_text(text: str) -> Optional[str]:
    """
    텍스트에서 읽기(후리가나) 추출
    괄호 안의 히라가나를 읽기로 간주
    예: "漢字(かんじ)" -> "かんじ"
    """
    # 괄호 안의 히라가나 찾기
    pattern = r"[（(]([あ-ん]+)[）)]"
    match = re.search(pattern, text)
    
    if match:
        reading = match.group(1)
        if is_hiragana(reading):
            return reading
    
    return None


def clean_word_text(text: str) -> str:
    """단어 텍스트에서 불필요한 부분 제거"""
    if not text:
        return ""
    
    # 괄호와 그 안의 내용 제거 (읽기 정보 등)
    text = re.sub(r"[（(][^）)]*[）)]", "", text)
    
    # 특수 문자 제거 (일본어 문자와 기본 구두점만 남김)
    text = re.sub(r"[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF・]", "", text)
    
    return normalize_japanese_text(text)


def estimate_word_difficulty(word: str) -> str:
    """
    단어 난이도 추정
    
    Args:
        word: 일본어 단어
        
    Returns:
        난이도 레벨 (beginner, intermediate, advanced)
    """
    if not word or not is_japanese(word):
        return "beginner"
    
    char_counts = count_character_types(word)
    total_chars = len(word)
    
    # 히라가나/가타카나만 있는 경우
    if char_counts["kanji"] == 0:
        if total_chars <= 3:
            return "beginner"
        elif total_chars <= 6:
            return "intermediate"
        else:
            return "advanced"
    
    # 한자가 포함된 경우
    kanji_ratio = char_counts["kanji"] / total_chars
    
    if kanji_ratio <= 0.3 and total_chars <= 3:
        return "beginner"
    elif kanji_ratio <= 0.5 and total_chars <= 5:
        return "intermediate"
    else:
        return "advanced"


def split_japanese_text(text: str) -> Dict[str, str]:
    """
    일본어 텍스트를 문자 유형별로 분리
    
    Args:
        text: 일본어 텍스트
        
    Returns:
        문자 유형별 분리된 텍스트
    """
    result = {
        "hiragana": "",
        "katakana": "",
        "kanji": "",
        "other": ""
    }
    
    for char in text:
        char_code = ord(char)
        if 0x3040 <= char_code <= 0x309F:
            result["hiragana"] += char
        elif 0x30A0 <= char_code <= 0x30FF:
            result["katakana"] += char
        elif 0x4E00 <= char_code <= 0x9FAF:
            result["kanji"] += char
        else:
            result["other"] += char
    
    return result


def validate_japanese_word(word: str) -> Dict[str, Any]:
    """
    일본어 단어 유효성 검증
    
    Args:
        word: 검증할 단어
        
    Returns:
        검증 결과
    """
    result = {
        "is_valid": False,
        "is_japanese": False,
        "char_types": {},
        "estimated_difficulty": "beginner",
        "cleaned_text": "",
        "reading": None,
        "errors": []
    }
    
    try:
        if not word:
            result["errors"].append("빈 텍스트입니다")
            return result
        
        # 텍스트 정규화
        cleaned = normalize_japanese_text(word)
        result["cleaned_text"] = cleaned
        
        if len(cleaned) == 0:
            result["errors"].append("정규화 후 빈 텍스트입니다")
            return result
        
        # 일본어 여부 확인
        result["is_japanese"] = is_japanese(cleaned)
        if not result["is_japanese"]:
            result["errors"].append("일본어 텍스트가 아닙니다")
        
        # 문자 유형 분석
        result["char_types"] = count_character_types(cleaned)
        
        # 길이 확인
        if len(cleaned) > 50:
            result["errors"].append("단어가 너무 깁니다 (50자 제한)")
        
        # 읽기 추출
        result["reading"] = extract_reading_from_text(word)
        
        # 난이도 추정
        result["estimated_difficulty"] = estimate_word_difficulty(cleaned)
        
        # 유효성 판단
        result["is_valid"] = len(result["errors"]) == 0
        
    except Exception as e:
        result["errors"].append(f"검증 중 오류 발생: {str(e)}")
    
    return result


# 상수 정의
JLPT_DIFFICULTY_MAP = {
    "N5": "beginner",
    "N4": "beginner", 
    "N3": "intermediate",
    "N2": "intermediate",
    "N1": "advanced"
}

PART_OF_SPEECH_MAP = {
    "noun": "명사",
    "verb": "동사",
    "adjective": "형용사",
    "adverb": "부사",
    "particle": "조사",
    "interjection": "감탄사",
    "conjunction": "접속사",
    "pronoun": "대명사",
    "auxiliary": "보조사",
    "counter": "수사",
    "prefix": "접두사",
    "suffix": "접미사"
} 