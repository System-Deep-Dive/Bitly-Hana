import sqlite3
import random
import string
import time
from typing import Optional
from .base import URLStrategy
from db import get_db_connection


class IndexedStrategy(URLStrategy):
    """인덱스를 활용하는 URL 단축 전략 (효율적인 조회)"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        # Base62 문자셋 (대소문자 + 숫자)
        self.base62_chars = string.ascii_letters + string.digits
    
    def _generate_short_code(self, length: int = 6) -> str:
        """Base62 랜덤 단축 코드를 생성합니다."""
        return ''.join(random.choice(self.base62_chars) for _ in range(length))
    
    def create_short_url(self, original_url: str, short_code: Optional[str] = None) -> dict:
        """원본 URL을 단축 URL로 변환합니다 (DB UNIQUE 제약 기반 중복 처리)."""
        if short_code is None:
            # 최대 5회 시도
            for attempt in range(5):
                short_code = self._generate_short_code()
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO url_mapping (short_code, original_url) VALUES (?, ?)",
                        (short_code, original_url)
                    )
                    conn.commit()
                    conn.close()
                    
                    print(f"[인덱스] 생성 성공: {short_code} (시도 {attempt + 1}회)")
                    break
                except sqlite3.IntegrityError:
                    conn.close()
                    print(f"[인덱스] 충돌 재시도: {short_code} (시도 {attempt + 1}회)")
                    if attempt == 4:  # 마지막 시도
                        raise Exception("409: Unable to generate unique short code after 5 attempts")
        else:
            # 사용자가 지정한 코드도 DB UNIQUE 제약으로 중복 체크
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO url_mapping (short_code, original_url) VALUES (?, ?)",
                    (short_code, original_url)
                )
                conn.commit()
                conn.close()
            except sqlite3.IntegrityError:
                conn.close()
                raise Exception("409: Short code already exists")
        
        return {
            "short_code": short_code,
            "original_url": original_url,
            "short_url": f"{self.base_url}/{short_code}"
        }
    
    def resolve(self, short_code: str) -> Optional[str]:
        """단축 코드를 원본 URL로 해석합니다 (인덱스 활용)."""
        start_time = time.time()
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            # 인덱스를 활용한 효율적인 조회
            cursor.execute(
                "SELECT original_url FROM url_mapping WHERE short_code = ? LIMIT 1",
                (short_code,)
            )
            result = cursor.fetchone()
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            if result:
                print(f"[인덱스] hit: {short_code} (elapsed_ms: {elapsed_ms:.2f})")
                return result[0]
            else:
                print(f"[인덱스] miss: {short_code} (elapsed_ms: {elapsed_ms:.2f})")
                return None
        finally:
            conn.close()
