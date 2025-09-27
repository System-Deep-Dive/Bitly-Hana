import sqlite3
import random
import string
from typing import Optional
from .base import URLStrategy
from db import get_db_connection


class FullScanStrategy(URLStrategy):
    """풀스캔을 사용하는 URL 단축 전략 (의도적으로 비효율적)"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        # Base62 문자셋 (대소문자 + 숫자)
        self.base62_chars = string.ascii_letters + string.digits
    
    def _generate_short_code(self, length: int = 6) -> str:
        """Base62 랜덤 단축 코드를 생성합니다."""
        return ''.join(random.choice(self.base62_chars) for _ in range(length))
    
    def _check_short_code_exists(self, short_code: str) -> bool:
        """풀스캔으로 short_code 중복을 체크합니다."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            # 의도적으로 비효율적인 풀스캔: 전체 테이블을 가져와서 Python에서 비교
            cursor.execute("SELECT short_code, original_url FROM url_mapping")
            all_rows = cursor.fetchall()
            
            print(f"[풀스캔] rows_scanned: {len(all_rows)}")
            
            for row in all_rows:
                if row[0] == short_code:
                    print(f"[풀스캔] hit: {short_code}")
                    return True
            
            print(f"[풀스캔] miss: {short_code}")
            return False
        finally:
            conn.close()
    
    def create_short_url(self, original_url: str, short_code: Optional[str] = None) -> dict:
        """원본 URL을 단축 URL로 변환합니다 (풀스캔 중복 체크)."""
        if short_code is None:
            # 최대 5회 시도
            for attempt in range(5):
                short_code = self._generate_short_code()
                if not self._check_short_code_exists(short_code):
                    break
            else:
                # 5회 시도 후에도 중복이면 409 에러
                raise Exception("409: Unable to generate unique short code after 5 attempts")
        else:
            # 사용자가 지정한 코드도 풀스캔으로 중복 체크
            if self._check_short_code_exists(short_code):
                raise Exception("409: Short code already exists")
        
        # 중복이 없으면 삽입
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO url_mapping (short_code, original_url) VALUES (?, ?)",
                (short_code, original_url)
            )
            conn.commit()
            
            return {
                "short_code": short_code,
                "original_url": original_url,
                "short_url": f"{self.base_url}/{short_code}"
            }
        finally:
            conn.close()
    
    def resolve(self, short_code: str) -> Optional[str]:
        """단축 코드를 원본 URL로 해석합니다 (의도적으로 비효율적인 풀스캔)."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            # 의도적으로 비효율적인 풀스캔: 전체 테이블을 가져와서 Python 루프로 비교
            cursor.execute("SELECT short_code, original_url FROM url_mapping")
            all_rows = cursor.fetchall()
            
            print(f"[풀스캔] rows_scanned: {len(all_rows)}")
            
            for row in all_rows:
                if row[0] == short_code:
                    print(f"[풀스캔] hit: {short_code}")
                    return row[1]
            
            print(f"[풀스캔] miss: {short_code}")
            return None
        finally:
            conn.close()
