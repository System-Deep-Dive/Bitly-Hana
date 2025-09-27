from abc import ABC, abstractmethod
from typing import Optional


class URLStrategy(ABC):
    """URL 단축/확장을 위한 전략 인터페이스"""
    
    @abstractmethod
    def create_short_url(self, original_url: str, short_code: Optional[str] = None) -> dict:
        """
        원본 URL을 단축 URL로 변환합니다.
        
        Args:
            original_url: 원본 URL
            short_code: 사용자가 지정한 단축 코드 (None이면 자동 생성)
            
        Returns:
            dict: 단축 URL 정보 (short_code, original_url, short_url 등)
        """
        pass
    
    @abstractmethod
    def resolve(self, short_code: str) -> Optional[str]:
        """
        단축 코드를 원본 URL로 해석합니다.
        
        Args:
            short_code: 단축 코드
            
        Returns:
            Optional[str]: 원본 URL (없으면 None)
        """
        pass
