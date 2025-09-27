#!/usr/bin/env python3
"""
URL 단축기 시드 데이터 생성 스크립트
사용법: python scripts/seed.py --count 100000 --domain https://example.com
"""

import argparse
import sys
import time
import uuid
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from db import get_db_connection
from strategy.fullscan import FullScanStrategy


def generate_urls(domain: str, count: int):
    """지정된 개수만큼 URL을 생성합니다."""
    urls = []
    for _ in range(count):
        url = f"{domain.rstrip('/')}/{uuid.uuid4()}"
        urls.append(url)
    return urls


def seed_database(urls: list):
    """데이터베이스에 URL들을 시드합니다."""
    strategy = FullScanStrategy()
    total = len(urls)
    start_time = time.time()
    
    print(f"시드 시작: {total:,}개 URL 생성 중...")
    
    for i, url in enumerate(urls, 1):
        try:
            # 풀스캔 전략으로 URL 생성 (중복 체크 포함)
            strategy.create_short_url(url)
            
            # 진행률 로그 (10k 단위)
            if i % 10000 == 0 or i == total:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                print(f"진행률: {i:,}/{total:,} ({i/total*100:.1f}%) - "
                      f"속도: {rate:.0f} URLs/sec - "
                      f"경과시간: {elapsed:.1f}초")
                
        except Exception as e:
            print(f"오류 발생 (URL {i}): {e}")
            continue
    
    total_time = time.time() - start_time
    print(f"\n시드 완료!")
    print(f"총 소요시간: {total_time:.2f}초")
    print(f"평균 속도: {total/total_time:.0f} URLs/sec")


def main():
    parser = argparse.ArgumentParser(description="URL 단축기 시드 데이터 생성")
    parser.add_argument("--count", type=int, required=True, 
                       help="생성할 URL 개수")
    parser.add_argument("--domain", type=str, required=True,
                       help="기본 도메인 (예: https://example.com)")
    
    args = parser.parse_args()
    
    if args.count <= 0:
        print("오류: count는 양수여야 합니다.")
        sys.exit(1)
    
    if not args.domain.startswith(('http://', 'https://')):
        print("오류: domain은 http:// 또는 https://로 시작해야 합니다.")
        sys.exit(1)
    
    print(f"시드 설정:")
    print(f"  - 개수: {args.count:,}")
    print(f"  - 도메인: {args.domain}")
    print()
    
    # URL 생성
    urls = generate_urls(args.domain, args.count)
    
    # 데이터베이스 시드
    seed_database(urls)


if __name__ == "__main__":
    main()
