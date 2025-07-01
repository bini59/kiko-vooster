"""
스토리지 매니저

파일 스토리지 백엔드 추상화 및 관리
"""

from abc import ABC, abstractmethod
from typing import Optional, BinaryIO, List
import mimetypes
import logging
from io import BytesIO
from app.core.config import settings
from app.core.database import get_database

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """스토리지 백엔드 추상 클래스"""
    
    @abstractmethod
    async def upload(self, path: str, file: BinaryIO, content_type: Optional[str] = None) -> str:
        """파일 업로드"""
        pass
    
    @abstractmethod
    async def download(self, path: str) -> bytes:
        """파일 다운로드"""
        pass
    
    @abstractmethod
    async def delete(self, path: str):
        """파일 삭제"""
        pass
    
    @abstractmethod
    async def get_url(self, path: str, expires_in: int = 3600) -> str:
        """서명된 URL 생성"""
        pass
    
    @abstractmethod
    async def exists(self, path: str) -> bool:
        """파일 존재 여부 확인"""
        pass
    
    @abstractmethod
    async def list_files(self, prefix: str) -> List[str]:
        """파일 목록 조회"""
        pass


class SupabaseStorageBackend(StorageBackend):
    """Supabase Storage 백엔드 구현"""
    
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self._client = None
    
    async def _get_client(self):
        """Supabase 클라이언트 획득"""
        if not self._client:
            db = await get_database()
            self._client = db.client
        return self._client
    
    async def upload(self, path: str, file: BinaryIO, content_type: Optional[str] = None) -> str:
        """Supabase Storage에 파일 업로드"""
        try:
            client = await self._get_client()
            
            if not content_type:
                content_type = mimetypes.guess_type(path)[0] or 'application/octet-stream'
            
            # 파일 읽기
            file_data = file.read()
            file.seek(0)  # 포인터 리셋
            
            # Supabase Storage 업로드
            response = client.storage.from_(self.bucket_name).upload(
                path,
                file_data,
                {"content-type": content_type, "cache-control": "max-age=86400"}
            )
            
            # 업로드 성공 확인
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Upload failed: {response.error}")
            
            logger.info(f"✅ File uploaded: {path}")
            return path
            
        except Exception as e:
            logger.error(f"❌ Upload error: {str(e)}")
            raise
    
    async def download(self, path: str) -> bytes:
        """Supabase Storage에서 파일 다운로드"""
        try:
            client = await self._get_client()
            
            response = client.storage.from_(self.bucket_name).download(path)
            
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Download failed: {response.error}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Download error: {str(e)}")
            raise
    
    async def delete(self, path: str):
        """Supabase Storage에서 파일 삭제"""
        try:
            client = await self._get_client()
            
            response = client.storage.from_(self.bucket_name).remove([path])
            
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Delete failed: {response.error}")
            
            logger.info(f"✅ File deleted: {path}")
            
        except Exception as e:
            logger.error(f"❌ Delete error: {str(e)}")
            raise
    
    async def get_url(self, path: str, expires_in: int = 3600) -> str:
        """서명된 URL 생성"""
        try:
            client = await self._get_client()
            
            response = client.storage.from_(self.bucket_name).create_signed_url(
                path,
                expires_in
            )
            
            if hasattr(response, 'error') and response.error:
                raise Exception(f"URL generation failed: {response.error}")
            
            return response['signedURL']
            
        except Exception as e:
            logger.error(f"❌ URL generation error: {str(e)}")
            raise
    
    async def exists(self, path: str) -> bool:
        """파일 존재 여부 확인"""
        try:
            client = await self._get_client()
            
            # 파일 목록에서 확인
            response = client.storage.from_(self.bucket_name).list(
                path=path.rsplit('/', 1)[0] if '/' in path else ''
            )
            
            if hasattr(response, 'error') and response.error:
                return False
            
            filename = path.split('/')[-1]
            return any(f['name'] == filename for f in response)
            
        except Exception as e:
            logger.error(f"❌ Exists check error: {str(e)}")
            return False
    
    async def list_files(self, prefix: str) -> List[str]:
        """파일 목록 조회"""
        try:
            client = await self._get_client()
            
            response = client.storage.from_(self.bucket_name).list(path=prefix)
            
            if hasattr(response, 'error') and response.error:
                raise Exception(f"List failed: {response.error}")
            
            return [f"{prefix}/{f['name']}" for f in response]
            
        except Exception as e:
            logger.error(f"❌ List error: {str(e)}")
            raise


class StorageManager:
    """스토리지 관리자 - 파일 관리 로직"""
    
    def __init__(self, backend: StorageBackend):
        self.backend = backend
    
    async def store_audio(self, script_id: str, file: BinaryIO, filename: str) -> str:
        """오디오 파일 저장"""
        path = f"audio/{script_id}/{filename}"
        return await self.backend.upload(path, file)
    
    async def store_segment(self, script_id: str, segment_num: int, data: bytes) -> str:
        """HLS 세그먼트 저장"""
        path = f"segments/{script_id}/segment_{segment_num:03d}.ts"
        file_obj = BytesIO(data)
        return await self.backend.upload(path, file_obj, content_type="video/mp2t")
    
    async def store_manifest(self, script_id: str, manifest_content: str) -> str:
        """HLS 매니페스트 저장"""
        path = f"manifests/{script_id}/playlist.m3u8"
        file_obj = BytesIO(manifest_content.encode('utf-8'))
        return await self.backend.upload(path, file_obj, content_type="application/x-mpegURL")
    
    async def get_audio_url(self, script_id: str, filename: str) -> str:
        """오디오 파일 URL 생성"""
        path = f"audio/{script_id}/{filename}"
        return await self.backend.get_url(path, expires_in=settings.STORAGE_SIGNED_URL_EXPIRES)
    
    async def get_segment_url(self, script_id: str, segment_num: int) -> str:
        """세그먼트 URL 생성"""
        path = f"segments/{script_id}/segment_{segment_num:03d}.ts"
        return await self.backend.get_url(path, expires_in=settings.STORAGE_SIGNED_URL_EXPIRES)
    
    async def get_manifest_url(self, script_id: str) -> str:
        """매니페스트 URL 생성"""
        path = f"manifests/{script_id}/playlist.m3u8"
        return await self.backend.get_url(path, expires_in=settings.STORAGE_SIGNED_URL_EXPIRES)
    
    async def download_audio(self, script_id: str, filename: str) -> bytes:
        """오디오 파일 다운로드"""
        path = f"audio/{script_id}/{filename}"
        return await self.backend.download(path)
    
    async def delete_script_files(self, script_id: str):
        """스크립트 관련 모든 파일 삭제"""
        # 오디오 파일 삭제
        audio_files = await self.backend.list_files(f"audio/{script_id}")
        for file in audio_files:
            await self.backend.delete(file)
        
        # 세그먼트 파일 삭제
        segment_files = await self.backend.list_files(f"segments/{script_id}")
        for file in segment_files:
            await self.backend.delete(file)
        
        # 매니페스트 파일 삭제
        manifest_files = await self.backend.list_files(f"manifests/{script_id}")
        for file in manifest_files:
            await self.backend.delete(file)
    
    async def validate_audio_file(self, file: BinaryIO, filename: str) -> bool:
        """오디오 파일 유효성 검증"""
        # 파일 크기 확인
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        
        if size > settings.MAX_FILE_SIZE:
            raise ValueError(f"File size {size} exceeds maximum {settings.MAX_FILE_SIZE}")
        
        # 파일 확장자 확인
        ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in settings.ALLOWED_FILE_TYPES:
            raise ValueError(f"File type {ext} not allowed. Allowed types: {settings.ALLOWED_FILE_TYPES}")
        
        return True


# 의존성 주입을 위한 전역 인스턴스
_storage_manager: Optional[StorageManager] = None


def get_storage_manager() -> Optional[StorageManager]:
    """스토리지 매니저 인스턴스 반환"""
    return _storage_manager


def set_storage_manager(storage_manager: StorageManager):
    """스토리지 매니저 인스턴스 설정"""
    global _storage_manager
    _storage_manager = storage_manager 