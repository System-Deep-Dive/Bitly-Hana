from collections import OrderedDict
from typing import Any, Optional


class LRUCache:
    """LRU(Least Recently Used) 캐시 구현"""
    
    def __init__(self, capacity: int = 1000):
        """
        LRU 캐시를 초기화합니다.
        
        Args:
            capacity: 최대 캐시 크기
        """
        self.capacity = capacity
        self.cache = OrderedDict()
    
    def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 값을 조회합니다.
        
        Args:
            key: 조회할 키
            
        Returns:
            캐시된 값 (없으면 None)
        """
        if key in self.cache:
            # 최근 사용된 항목을 맨 뒤로 이동 (LRU 업데이트)
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        캐시에 값을 저장합니다.
        
        Args:
            key: 저장할 키
            value: 저장할 값
        """
        if key in self.cache:
            # 기존 항목이 있으면 제거 후 다시 추가 (LRU 업데이트)
            self.cache.pop(key)
        elif len(self.cache) >= self.capacity:
            # 용량 초과 시 가장 오래된 항목 제거 (FIFO)
            self.cache.popitem(last=False)
        
        self.cache[key] = value
    
    def __len__(self) -> int:
        """현재 캐시 크기를 반환합니다."""
        return len(self.cache)
    
    def __contains__(self, key: str) -> bool:
        """키가 캐시에 있는지 확인합니다."""
        return key in self.cache
