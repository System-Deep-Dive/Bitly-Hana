"""Redis 캐시 유틸리티"""

import redis
import logging
from typing import Optional, Union
from settings import REDIS_HOST, REDIS_PORT, REDIS_DB

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis 캐시 클래스"""
    
    def __init__(self):
        """Redis 연결 초기화"""
        try:
            self.redis_client = redis.StrictRedis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # 연결 테스트
            self.redis_client.ping()
            logger.info(f"Redis 연결 성공: {REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
        except redis.ConnectionError as e:
            logger.error(f"Redis 연결 실패: {e}")
            raise
        except Exception as e:
            logger.error(f"Redis 초기화 오류: {e}")
            raise
    
    def get(self, key: str) -> Optional[str]:
        """키에 해당하는 값을 가져옵니다."""
        try:
            value = self.redis_client.get(key)
            if value is None:
                logger.debug(f"Redis GET miss: {key}")
                return None
            else:
                logger.debug(f"Redis GET hit: {key}")
                return value
        except redis.RedisError as e:
            logger.error(f"Redis GET 오류 {key}: {e}")
            return None
    
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """키-값을 저장합니다 (TTL 옵션)."""
        try:
            if ttl is not None:
                result = self.redis_client.setex(key, ttl, value)
                logger.debug(f"Redis SETEX {key} (TTL: {ttl}s): {result}")
            else:
                result = self.redis_client.set(key, value)
                logger.debug(f"Redis SET {key}: {result}")
            return result
        except redis.RedisError as e:
            logger.error(f"Redis SET 오류 {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """키의 존재 여부를 확인합니다."""
        try:
            result = self.redis_client.exists(key)
            logger.debug(f"Redis EXISTS {key}: {bool(result)}")
            return bool(result)
        except redis.RedisError as e:
            logger.error(f"Redis EXISTS 오류 {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """키를 삭제합니다."""
        try:
            result = self.redis_client.delete(key)
            logger.debug(f"Redis DELETE {key}: {bool(result)}")
            return bool(result)
        except redis.RedisError as e:
            logger.error(f"Redis DELETE 오류 {key}: {e}")
            return False
    
    def ping(self) -> bool:
        """Redis 연결 상태를 확인합니다."""
        try:
            result = self.redis_client.ping()
            return result
        except redis.RedisError:
            return False
