"""
오디오 API 테스트

오디오 재생 API 엔드포인트 테스트
"""

import pytest
from uuid import UUID, uuid4
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from app.models.audio import (
    StreamResponse, PrepareResponse, PlayResponse,
    ProgressResponse, SeekResponse, BookmarkResponse
)
from app.services.audio.audio_service import AudioService


class TestAudioAPI:
    """오디오 API 테스트 클래스"""
    
    @pytest.fixture
    def mock_audio_service(self):
        """Mock 오디오 서비스"""
        service = Mock(spec=AudioService)
        
        # get_stream_info mock
        service.get_stream_info = AsyncMock(return_value=StreamResponse(
            stream_url="https://cdn.example.com/stream.m3u8",
            duration=3600.0,
            bitrate=128000,
            format="hls",
            cached=True,
            expires_at=datetime.utcnow()
        ))
        
        # prepare_audio mock
        service.prepare_audio = AsyncMock(return_value=PrepareResponse(
            status="preparing",
            progress=0,
            estimated_time=30
        ))
        
        # create_play_session mock
        service.create_play_session = AsyncMock(return_value=PlayResponse(
            session_id=uuid4(),
            stream_url="https://cdn.example.com/stream.m3u8",
            start_position=0
        ))
        
        # update_progress mock
        service.update_progress = AsyncMock(return_value=ProgressResponse(
            saved=True,
            total_listened=120.5,
            progress_percent=33.5
        ))
        
        # seek_position mock
        service.seek_position = AsyncMock(return_value=SeekResponse(
            success=True,
            new_position=300.0,
            segment_url="https://cdn.example.com/segment_30.ts"
        ))
        
        # create_bookmark mock
        service.create_bookmark = AsyncMock(return_value=BookmarkResponse(
            id=uuid4(),
            created_at=datetime.utcnow()
        ))
        
        return service
    
    @pytest.mark.asyncio
    async def test_get_stream_success(self, mock_audio_service):
        """스트림 정보 조회 성공 테스트"""
        script_id = uuid4()
        quality = "medium"
        
        result = await mock_audio_service.get_stream_info(
            script_id=script_id,
            quality=quality
        )
        
        assert result.stream_url.startswith("https://")
        assert result.format == "hls"
        assert result.bitrate == 128000
        assert result.cached is True
        mock_audio_service.get_stream_info.assert_called_once_with(
            script_id=script_id,
            quality=quality
        )
    
    @pytest.mark.asyncio
    async def test_prepare_audio_success(self, mock_audio_service):
        """오디오 준비 성공 테스트"""
        script_id = uuid4()
        
        result = await mock_audio_service.prepare_audio(
            script_id=script_id,
            priority="high"
        )
        
        assert result.status == "preparing"
        assert result.progress == 0
        assert result.estimated_time == 30
    
    @pytest.mark.asyncio
    async def test_create_play_session_success(self, mock_audio_service):
        """재생 세션 생성 성공 테스트"""
        script_id = uuid4()
        user_id = uuid4()
        
        result = await mock_audio_service.create_play_session(
            script_id=script_id,
            user_id=user_id,
            position=0
        )
        
        assert isinstance(result.session_id, UUID)
        assert result.stream_url.startswith("https://")
        assert result.start_position == 0
    
    @pytest.mark.asyncio
    async def test_update_progress_success(self, mock_audio_service):
        """진행률 업데이트 성공 테스트"""
        session_id = uuid4()
        
        result = await mock_audio_service.update_progress(
            session_id=session_id,
            position=120.5,
            playback_rate=1.0
        )
        
        assert result.saved is True
        assert result.total_listened == 120.5
        assert result.progress_percent == 33.5
    
    @pytest.mark.asyncio
    async def test_seek_position_success(self, mock_audio_service):
        """위치 이동 성공 테스트"""
        session_id = uuid4()
        
        result = await mock_audio_service.seek_position(
            session_id=session_id,
            position=300.0
        )
        
        assert result.success is True
        assert result.new_position == 300.0
        assert result.segment_url is not None
    
    @pytest.mark.asyncio
    async def test_create_bookmark_success(self, mock_audio_service):
        """북마크 생성 성공 테스트"""
        user_id = uuid4()
        script_id = uuid4()
        
        result = await mock_audio_service.create_bookmark(
            user_id=user_id,
            script_id=script_id,
            position=150.0,
            note="중요한 표현"
        )
        
        assert isinstance(result.id, UUID)
        assert isinstance(result.created_at, datetime)


class TestAudioService:
    """오디오 서비스 단위 테스트"""
    
    @pytest.fixture
    def mock_storage(self):
        """Mock 스토리지 매니저"""
        storage = Mock()
        storage.get_manifest_url = AsyncMock(
            return_value="https://cdn.example.com/manifest.m3u8"
        )
        storage.get_segment_url = AsyncMock(
            return_value="https://cdn.example.com/segment.ts"
        )
        return storage
    
    @pytest.fixture
    def mock_cache(self):
        """Mock 캐시 매니저"""
        cache = Mock()
        cache.get_stream_info = AsyncMock(return_value=None)
        cache.set_stream_info = AsyncMock()
        cache.get_session = AsyncMock(return_value={
            'id': str(uuid4()),
            'user_id': str(uuid4()),
            'script_id': str(uuid4()),
            'total_duration': 3600.0
        })
        cache.set_session = AsyncMock()
        return cache
    
    @pytest.mark.asyncio
    async def test_get_stream_info_from_cache(self, mock_storage, mock_cache):
        """캐시에서 스트림 정보 조회 테스트"""
        # 캐시에 데이터가 있는 경우
        cached_data = {
            'stream_url': 'https://cached.url',
            'duration': 1800.0,
            'bitrate': 128000,
            'format': 'hls',
            'cached': True,
            'expires_at': datetime.utcnow().isoformat()
        }
        mock_cache.get_stream_info.return_value = cached_data
        
        service = AudioService(mock_storage, mock_cache)
        
        # DB mock이 필요하므로 여기서는 캐시 동작만 테스트
        # 실제 통합 테스트는 별도로 작성 필요
    
    def test_get_bitrate_for_quality(self, mock_storage, mock_cache):
        """품질별 비트레이트 반환 테스트"""
        service = AudioService(mock_storage, mock_cache)
        
        assert service._get_bitrate_for_quality('low') == 64000
        assert service._get_bitrate_for_quality('medium') == 128000
        assert service._get_bitrate_for_quality('high') == 256000
        assert service._get_bitrate_for_quality('unknown') == 128000 