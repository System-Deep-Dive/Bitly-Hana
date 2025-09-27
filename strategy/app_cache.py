import time
from typing import Optional
from .base import URLStrategy
from .indexed import IndexedStrategy
from cache.lru_cache import LRUCache


class AppCacheStrategy(URLStrategy):
    """애플리케이션 LRU 캐시를 활용하는 URL 단축 전략"""
    
    def __init__(self, cache_capacity: int = 10000):
        """
        AppCacheStrategy를 초기화합니다.
        
        Args:
            cache_capacity: LRU 캐시의 최대 크기
        """
        self.cache = LRUCache(capacity=cache_capacity)
        self.fallback = IndexedStrategy()
        self.base_url = "http://localhost:8000"
    
    def create_short_url(self, original_url: str, short_code: Optional[str] = None) -> dict:
        """
        원본 URL을 단축 URL로 변환합니다.
        fallback 전략에 위임하고 결과를 캐시에 저장합니다.
        """
        # fallback 전략에 URL 생성 위임
        result = self.fallback.create_short_url(original_url, short_code)
        
        # 캐시에 (short_code → original_url) 저장
        self.cache.set(result["short_code"], result["original_url"])
        
        print(f"[앱캐시] 생성 후 캐시 저장: {result['short_code']} (캐시 크기: {len(self.cache)})")
        
        return result
    
    def resolve(self, short_code: str) -> Optional[str]:
        """
        단축 코드를 원본 URL로 해석합니다.
        캐시를 먼저 확인하고, miss 시 fallback 전략에 위임합니다.
        """
        start_time = time.time()
        
        # 캐시 먼저 확인
        cached_url = self.cache.get(short_code)
        
        if cached_url is not None:
            # 캐시 hit
            elapsed_ms = (time.time() - start_time) * 1000
            print(f"[앱캐시] hit: {short_code} (elapsed_ms: {elapsed_ms:.2f}, 캐시 크기: {len(self.cache)})")
            return cached_url
        
        # 캐시 miss - fallback 전략에 위임
        print(f"[앱캐시] miss: {short_code} (캐시 크기: {len(self.cache)})")
        original_url = self.fallback.resolve(short_code)
        
        # fallback에서 결과가 있으면 캐시에 저장
        if original_url is not None:
            self.cache.set(short_code, original_url)
            print(f"[앱캐시] fallback 결과 캐시 저장: {short_code} (캐시 크기: {len(self.cache)})")
        
        return original_url
