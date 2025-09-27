"""Redis 분산 캐시를 활용한 URL 단축 전략"""

import time
from typing import Optional
from .base import URLStrategy
from .indexed import IndexedStrategy
from cache.redis_cache import RedisCache


class RedisStrategy(URLStrategy):
    """Redis 분산 캐시를 활용하는 URL 단축 전략"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.cache = RedisCache()
        self.fallback = IndexedStrategy()
        # 캐시 통계
        self.hit_count = 0
        self.miss_count = 0
        self.fallback_count = 0
        # 네거티브 캐시 TTL (짧게 설정)
        self.negative_cache_ttl = 30
        # 정상 캐시 TTL (1일)
        self.cache_ttl = 86400
        # 네거티브 캐시 마커
        self.miss_marker = "__MISS__"
    
    def _get_cache_stats(self) -> str:
        """캐시 통계 정보를 반환합니다."""
        total = self.hit_count + self.miss_count
        if total == 0:
            return "hit_rate: 0% (0/0)"
        hit_rate = (self.hit_count / total) * 100
        return f"hit_rate: {hit_rate:.1f}% ({self.hit_count}/{total})"
    
    def create_short_url(self, original_url: str, short_code: Optional[str] = None) -> dict:
        """원본 URL을 단축 URL로 변환합니다 (fallback 사용)."""
        print("[Redis] create_short_url: fallback으로 단축 URL 생성")
        self.fallback_count += 1
        
        # fallback으로 단축 URL 생성
        result = self.fallback.create_short_url(original_url, short_code)
        short_code = result["short_code"]
        
        # Redis에 캐시 저장 (TTL: 1일)
        cache_key = f"url:{short_code}"
        cache_success = self.cache.set(cache_key, original_url, self.cache_ttl)
        
        if cache_success:
            print(f"[Redis] 캐시 저장 성공: {short_code} (TTL: {self.cache_ttl}s)")
        else:
            print(f"[Redis] 캐시 저장 실패: {short_code}")
        
        return result
    
    def resolve(self, short_code: str) -> Optional[str]:
        """단축 코드를 원본 URL로 해석합니다 (Redis 캐시 우선)."""
        start_time = time.time()
        cache_key = f"url:{short_code}"
        
        # 1. Redis에서 조회
        cached_value = self.cache.get(cache_key)
        
        if cached_value is not None:
            # 캐시 히트
            if cached_value == self.miss_marker:
                # 네거티브 캐시 히트 (존재하지 않는 코드)
                elapsed_ms = (time.time() - start_time) * 1000
                print(f"[Redis] negative hit: {short_code} (elapsed_ms: {elapsed_ms:.2f})")
                self.hit_count += 1
                print(f"[Redis] 캐시 통계: {self._get_cache_stats()}")
                return None
            else:
                # 정상 캐시 히트
                elapsed_ms = (time.time() - start_time) * 1000
                print(f"[Redis] hit: {short_code} (elapsed_ms: {elapsed_ms:.2f})")
                self.hit_count += 1
                print(f"[Redis] 캐시 통계: {self._get_cache_stats()}")
                return cached_value
        
        # 2. 캐시 미스 - fallback으로 DB 조회
        print(f"[Redis] miss: {short_code} - fallback 실행")
        self.miss_count += 1
        
        original_url = self.fallback.resolve(short_code)
        
        if original_url is not None:
            # DB에서 찾은 경우 - Redis에 저장
            cache_success = self.cache.set(cache_key, original_url, self.cache_ttl)
            if cache_success:
                print(f"[Redis] 캐시 저장: {short_code} (TTL: {self.cache_ttl}s)")
            else:
                print(f"[Redis] 캐시 저장 실패: {short_code}")
        else:
            # DB에서도 찾지 못한 경우 - 네거티브 캐시 저장
            cache_success = self.cache.set(cache_key, self.miss_marker, self.negative_cache_ttl)
            if cache_success:
                print(f"[Redis] 네거티브 캐시 저장: {short_code} (TTL: {self.negative_cache_ttl}s)")
            else:
                print(f"[Redis] 네거티브 캐시 저장 실패: {short_code}")
        
        elapsed_ms = (time.time() - start_time) * 1000
        print(f"[Redis] fallback 완료: {short_code} (elapsed_ms: {elapsed_ms:.2f})")
        print(f"[Redis] 캐시 통계: {self._get_cache_stats()}")
        
        return original_url
