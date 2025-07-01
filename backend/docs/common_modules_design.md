# 오디오 재생 API 공통 모듈 설계

## 1. 개요

라디오 오디오 재생 기능을 위한 재사용 가능한 공통 모듈 설계입니다.
각 모듈은 단일 책임 원칙을 따르며, 테스트 가능하고 확장 가능한 구조로 설계되었습니다.

## 2. 모듈 구조

```
backend/app/
├── core/
│   ├── cache/
│   │   ├── __init__.py
│   │   ├── redis_client.py    # Redis 연결 관리
│   │   └── cache_manager.py   # 캐시 추상화 레이어
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── supabase_client.py # Supabase Storage 클라이언트
│   │   └── storage_manager.py  # 스토리지 추상화 레이어
│   └── streaming/
│       ├── __init__.py
│       ├── hls_processor.py    # HLS 처리
│       └── ffmpeg_wrapper.py   # FFmpeg 래퍼
├── services/
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── audio_service.py    # 오디오 비즈니스 로직
│   │   ├── session_service.py  # 재생 세션 관리
│   │   └── progress_service.py # 진행률 추적
│   └── cdn/
│       ├── __init__.py
│       └── cloudflare_service.py # CDN 서비스
└── utils/
    ├── audio/
    │   ├── __init__.py
    │   ├── validators.py       # 오디오 파일 검증
    │   └── metadata.py         # 메타데이터 추출
    └── security/
        ├── __init__.py
        └── url_signer.py       # URL 서명 유틸리티
```

## 3. 핵심 모듈 상세 설계

### 3.1 Cache Manager

```python
# app/core/cache/cache_manager.py
from abc import ABC, abstractmethod
from typing import Optional, Any
import json

class CacheBackend(ABC):
    """캐시 백엔드 추상 클래스"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        pass

    @abstractmethod
    async def delete(self, key: str):
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass

class RedisCacheBackend(CacheBackend):
    """Redis 캐시 백엔드 구현"""

    def __init__(self, redis_client):
        self.redis = redis_client

    async def get(self, key: str) -> Optional[Any]:
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        serialized = json.dumps(value)
        if ttl:
            await self.redis.setex(key, ttl, serialized)
        else:
            await self.redis.set(key, serialized)

    async def delete(self, key: str):
        await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        return await self.redis.exists(key)

class CacheManager:
    """캐시 관리자"""

    def __init__(self, backend: CacheBackend):
        self.backend = backend
        self.default_ttl = 3600  # 1시간

    async def get_stream_info(self, script_id: str, quality: str) -> Optional[dict]:
        """스트림 정보 캐시 조회"""
        key = f"stream:{script_id}:{quality}"
        return await self.backend.get(key)

    async def set_stream_info(self, script_id: str, quality: str, info: dict):
        """스트림 정보 캐시 저장"""
        key = f"stream:{script_id}:{quality}"
        await self.backend.set(key, info, ttl=86400)  # 24시간

    async def get_session(self, session_id: str) -> Optional[dict]:
        """세션 정보 조회"""
        key = f"session:{session_id}"
        return await self.backend.get(key)

    async def set_session(self, session_id: str, data: dict):
        """세션 정보 저장"""
        key = f"session:{session_id}"
        await self.backend.set(key, data, ttl=7200)  # 2시간
```

### 3.2 Storage Manager

```python
# app/core/storage/storage_manager.py
from abc import ABC, abstractmethod
from typing import Optional, BinaryIO
import mimetypes

class StorageBackend(ABC):
    """스토리지 백엔드 추상 클래스"""

    @abstractmethod
    async def upload(self, path: str, file: BinaryIO, content_type: Optional[str] = None) -> str:
        pass

    @abstractmethod
    async def download(self, path: str) -> bytes:
        pass

    @abstractmethod
    async def delete(self, path: str):
        pass

    @abstractmethod
    async def get_url(self, path: str, expires_in: int = 3600) -> str:
        pass

class SupabaseStorageBackend(StorageBackend):
    """Supabase Storage 백엔드 구현"""

    def __init__(self, supabase_client, bucket_name: str):
        self.client = supabase_client
        self.bucket = bucket_name

    async def upload(self, path: str, file: BinaryIO, content_type: Optional[str] = None) -> str:
        if not content_type:
            content_type = mimetypes.guess_type(path)[0] or 'application/octet-stream'

        response = self.client.storage.from_(self.bucket).upload(
            path,
            file,
            {"content-type": content_type}
        )
        return response.get('path')

    async def download(self, path: str) -> bytes:
        return self.client.storage.from_(self.bucket).download(path)

    async def delete(self, path: str):
        self.client.storage.from_(self.bucket).remove([path])

    async def get_url(self, path: str, expires_in: int = 3600) -> str:
        return self.client.storage.from_(self.bucket).create_signed_url(
            path,
            expires_in
        )

class StorageManager:
    """스토리지 관리자"""

    def __init__(self, backend: StorageBackend):
        self.backend = backend

    async def store_audio(self, script_id: str, file: BinaryIO, filename: str) -> str:
        """오디오 파일 저장"""
        path = f"audio/{script_id}/{filename}"
        return await self.backend.upload(path, file)

    async def store_segment(self, script_id: str, segment_num: int, data: bytes) -> str:
        """HLS 세그먼트 저장"""
        path = f"segments/{script_id}/segment_{segment_num}.ts"
        return await self.backend.upload(path, data)

    async def get_audio_url(self, script_id: str, filename: str) -> str:
        """오디오 파일 URL 생성"""
        path = f"audio/{script_id}/{filename}"
        return await self.backend.get_url(path, expires_in=14400)  # 4시간
```

### 3.3 HLS Processor

```python
# app/core/streaming/hls_processor.py
import asyncio
import tempfile
import os
from typing import List, Tuple
import ffmpeg

class HLSProcessor:
    """HLS 스트리밍 처리기"""

    def __init__(self, segment_duration: int = 10):
        self.segment_duration = segment_duration

    async def process_audio(self, input_path: str, output_dir: str) -> Tuple[str, List[str]]:
        """오디오 파일을 HLS로 변환"""
        manifest_path = os.path.join(output_dir, "playlist.m3u8")

        # FFmpeg 명령 구성
        stream = ffmpeg.input(input_path)
        stream = ffmpeg.output(
            stream,
            manifest_path,
            format='hls',
            hls_time=self.segment_duration,
            hls_list_size=0,
            hls_segment_filename=os.path.join(output_dir, 'segment_%03d.ts'),
            audio_bitrate='128k',
            acodec='aac'
        )

        # 비동기 실행
        process = await asyncio.create_subprocess_exec(
            *ffmpeg.compile(stream),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"FFmpeg error: {stderr.decode()}")

        # 생성된 세그먼트 파일 목록
        segments = [f for f in os.listdir(output_dir) if f.endswith('.ts')]
        segments.sort()

        return manifest_path, segments

    async def extract_metadata(self, file_path: str) -> dict:
        """오디오 파일 메타데이터 추출"""
        probe = ffmpeg.probe(file_path)

        audio_stream = next(
            (stream for stream in probe['streams'] if stream['codec_type'] == 'audio'),
            None
        )

        if not audio_stream:
            raise ValueError("No audio stream found")

        return {
            'duration': float(probe['format']['duration']),
            'bitrate': int(probe['format']['bit_rate']),
            'codec': audio_stream['codec_name'],
            'sample_rate': int(audio_stream['sample_rate']),
            'channels': audio_stream['channels']
        }

    def generate_manifest(self, segments: List[str], duration: int = 10) -> str:
        """HLS manifest 생성"""
        manifest = [
            "#EXTM3U",
            "#EXT-X-VERSION:3",
            f"#EXT-X-TARGETDURATION:{duration}",
            "#EXT-X-MEDIA-SEQUENCE:0"
        ]

        for segment in segments:
            manifest.extend([
                f"#EXTINF:{duration}.0,",
                segment
            ])

        manifest.append("#EXT-X-ENDLIST")
        return "\n".join(manifest)
```

### 3.4 Audio Service

```python
# app/services/audio/audio_service.py
from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime

class AudioService:
    """오디오 서비스 - 비즈니스 로직"""

    def __init__(self, storage_manager, cache_manager, hls_processor):
        self.storage = storage_manager
        self.cache = cache_manager
        self.hls = hls_processor

    async def get_stream_info(self, script_id: UUID, quality: str = "medium") -> dict:
        """스트림 정보 조회"""
        # 캐시 확인
        cached = await self.cache.get_stream_info(str(script_id), quality)
        if cached:
            return cached

        # DB에서 스크립트 정보 조회
        script = await self._get_script(script_id)
        if not script:
            raise ValueError(f"Script {script_id} not found")

        # 스트림 URL 생성
        stream_info = {
            'stream_url': await self._generate_stream_url(script_id, quality),
            'duration': script.duration,
            'bitrate': self._get_bitrate_for_quality(quality),
            'format': 'hls',
            'cached': False,
            'expires_at': datetime.utcnow().timestamp() + 14400  # 4시간
        }

        # 캐시 저장
        await self.cache.set_stream_info(str(script_id), quality, stream_info)

        return stream_info

    async def prepare_audio(self, script_id: UUID, priority: str = "normal") -> dict:
        """오디오 사전 처리"""
        # 이미 처리중인지 확인
        status_key = f"prepare:{script_id}"
        existing = await self.cache.backend.get(status_key)
        if existing:
            return existing

        # 처리 시작
        status = {
            'status': 'preparing',
            'progress': 0,
            'estimated_time': 30
        }
        await self.cache.backend.set(status_key, status, ttl=300)

        # 비동기 처리 시작
        asyncio.create_task(self._process_audio_background(script_id))

        return status

    async def _process_audio_background(self, script_id: UUID):
        """백그라운드 오디오 처리"""
        try:
            # 임시 디렉토리 생성
            with tempfile.TemporaryDirectory() as temp_dir:
                # 원본 오디오 다운로드
                audio_path = await self._download_original_audio(script_id, temp_dir)

                # HLS 변환
                manifest_path, segments = await self.hls.process_audio(
                    audio_path,
                    temp_dir
                )

                # 세그먼트 업로드
                for i, segment in enumerate(segments):
                    segment_path = os.path.join(temp_dir, segment)
                    with open(segment_path, 'rb') as f:
                        await self.storage.store_segment(
                            str(script_id),
                            i,
                            f.read()
                        )

                    # 진행률 업데이트
                    progress = int((i + 1) / len(segments) * 100)
                    await self._update_prepare_status(script_id, progress)

                # 완료 상태 업데이트
                await self._update_prepare_status(script_id, 100, 'ready')

        except Exception as e:
            # 실패 상태 업데이트
            await self._update_prepare_status(script_id, 0, 'failed', str(e))
            raise

    def _get_bitrate_for_quality(self, quality: str) -> int:
        """품질별 비트레이트 반환"""
        bitrates = {
            'low': 64000,
            'medium': 128000,
            'high': 256000
        }
        return bitrates.get(quality, 128000)
```

## 4. 유틸리티 모듈

### 4.1 Audio Validators

```python
# app/utils/audio/validators.py
import magic
from typing import BinaryIO

class AudioValidator:
    """오디오 파일 검증 유틸리티"""

    ALLOWED_MIME_TYPES = {
        'audio/mpeg',
        'audio/mp4',
        'audio/wav',
        'audio/x-wav',
        'audio/aac'
    }

    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

    @classmethod
    def validate_file(cls, file: BinaryIO, filename: str) -> bool:
        """파일 유효성 검증"""
        # 파일 크기 확인
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)

        if size > cls.MAX_FILE_SIZE:
            raise ValueError(f"File size {size} exceeds maximum {cls.MAX_FILE_SIZE}")

        # MIME 타입 확인
        mime = magic.from_buffer(file.read(2048), mime=True)
        file.seek(0)

        if mime not in cls.ALLOWED_MIME_TYPES:
            raise ValueError(f"Invalid mime type: {mime}")

        return True

    @classmethod
    def validate_duration(cls, duration: float) -> bool:
        """재생 시간 검증"""
        # 최소 10초, 최대 4시간
        if duration < 10 or duration > 14400:
            raise ValueError(f"Invalid duration: {duration}")
        return True
```

### 4.2 URL Signer

```python
# app/utils/security/url_signer.py
import hmac
import hashlib
from urllib.parse import urlparse, parse_qs, urlencode
from datetime import datetime, timedelta

class URLSigner:
    """URL 서명 유틸리티"""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def sign_url(self, url: str, expires_in: int = 3600) -> str:
        """URL에 서명 추가"""
        expires_at = int((datetime.utcnow() + timedelta(seconds=expires_in)).timestamp())

        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        params['expires'] = [str(expires_at)]

        # 서명 생성
        base_string = f"{parsed.path}?{urlencode(params, doseq=True)}"
        signature = hmac.new(
            self.secret_key.encode(),
            base_string.encode(),
            hashlib.sha256
        ).hexdigest()

        params['signature'] = [signature]

        signed_url = parsed._replace(query=urlencode(params, doseq=True)).geturl()
        return signed_url

    def verify_url(self, url: str) -> bool:
        """URL 서명 검증"""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        # 만료 시간 확인
        expires = params.get('expires', [None])[0]
        if not expires or int(expires) < datetime.utcnow().timestamp():
            return False

        # 서명 확인
        signature = params.pop('signature', [None])[0]
        if not signature:
            return False

        base_string = f"{parsed.path}?{urlencode(params, doseq=True)}"
        expected_signature = hmac.new(
            self.secret_key.encode(),
            base_string.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)
```

## 5. 의존성 주입 설정

```python
# app/core/dependencies.py
from functools import lru_cache
from app.core.cache.redis_client import get_redis_client
from app.core.cache.cache_manager import CacheManager, RedisCacheBackend
from app.core.storage.supabase_client import get_supabase_client
from app.core.storage.storage_manager import StorageManager, SupabaseStorageBackend
from app.core.streaming.hls_processor import HLSProcessor
from app.services.audio.audio_service import AudioService

@lru_cache()
def get_cache_manager() -> CacheManager:
    """캐시 매니저 싱글톤"""
    redis = get_redis_client()
    backend = RedisCacheBackend(redis)
    return CacheManager(backend)

@lru_cache()
def get_storage_manager() -> StorageManager:
    """스토리지 매니저 싱글톤"""
    supabase = get_supabase_client()
    backend = SupabaseStorageBackend(supabase, "audio-files")
    return StorageManager(backend)

@lru_cache()
def get_hls_processor() -> HLSProcessor:
    """HLS 프로세서 싱글톤"""
    return HLSProcessor()

@lru_cache()
def get_audio_service() -> AudioService:
    """오디오 서비스 싱글톤"""
    return AudioService(
        get_storage_manager(),
        get_cache_manager(),
        get_hls_processor()
    )
```

## 6. 테스트 가능성

모든 모듈은 의존성 주입을 통해 테스트 가능하도록 설계되었습니다:

```python
# tests/test_audio_service.py
import pytest
from unittest.mock import Mock, AsyncMock

async def test_get_stream_info_from_cache():
    """캐시에서 스트림 정보 조회 테스트"""
    # Given
    cache_manager = Mock()
    cache_manager.get_stream_info = AsyncMock(return_value={'cached': True})

    service = AudioService(Mock(), cache_manager, Mock())

    # When
    result = await service.get_stream_info(uuid4(), "medium")

    # Then
    assert result['cached'] is True
    cache_manager.get_stream_info.assert_called_once()
```
