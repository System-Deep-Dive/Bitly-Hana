#!/bin/bash

# URL 단축기 성능 벤치마크 스크립트
# 전제: 서버가 :8000에서 실행 중

set -e

BASE_URL="http://localhost:8000"
HIT_CODES_FILE="hit_codes.txt"
MISS_CODES_FILE="miss_codes.txt"
BENCHMARK_DURATION="30s"
CONCURRENCY=50

echo "=== URL 단축기 성능 벤치마크 ==="
echo "서버: $BASE_URL"
echo "지속시간: $BENCHMARK_DURATION"
echo "동시성: $CONCURRENCY"
echo

# 1. 시드된 코드 중 임의 100개를 hit_codes.txt로 추출
echo "1. 히트 대상 코드 추출 중..."
python3 -c "
import sqlite3
import random
conn = sqlite3.connect('url_shortener.db')
cursor = conn.cursor()
cursor.execute('SELECT short_code FROM url_mapping')
all_codes = [row[0] for row in cursor.fetchall()]
conn.close()

# 100개 랜덤 선택 (데이터가 100개 미만이면 전체 사용)
hit_codes = random.sample(all_codes, min(100, len(all_codes)))
with open('hit_codes.txt', 'w') as f:
    for code in hit_codes:
        f.write(code + '\n')
print(f'히트 코드 {len(hit_codes)}개 추출 완료')
"

# 2. 존재하지 않는 코드 100개 생성
echo "2. 미스 대상 코드 생성 중..."
python3 -c "
import random
import string

def generate_random_code():
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(6))

miss_codes = [generate_random_code() for _ in range(100)]
with open('miss_codes.txt', 'w') as f:
    for code in miss_codes:
        f.write(code + '\n')
print(f'미스 코드 100개 생성 완료')
"

# 3. hey가 설치되어 있는지 확인
if ! command -v hey &> /dev/null; then
    echo "오류: hey가 설치되지 않았습니다."
    echo "설치 방법: go install github.com/rakyll/hey@latest"
    exit 1
fi

# 4. 벤치마크 실행
echo "3. 벤치마크 실행 중..."
echo "히트/미스 비율: 50:50"

# 히트 요청과 미스 요청을 섞어서 실행
hey -z $BENCHMARK_DURATION -c $CONCURRENCY \
    -m GET \
    -H "Accept: application/json" \
    -D hit_codes.txt \
    -D miss_codes.txt \
    $BASE_URL/{} \
    > benchmark_results.txt 2>&1

# 5. 결과 파싱 및 요약
echo
echo "=== 벤치마크 결과 요약 ==="

# hey 결과에서 주요 지표 추출
if [ -f benchmark_results.txt ]; then
    echo "상세 결과:"
    cat benchmark_results.txt
    echo
    
    # p50/p95/p99/RPS 파싱
    echo "주요 지표 요약:"
    
    # RPS 추출
    RPS=$(grep "Requests/sec:" benchmark_results.txt | awk '{print $2}' || echo "N/A")
    echo "RPS: $RPS"
    
    # 응답시간 지표 추출 (p50, p95, p99)
    if grep -q "Response time histogram:" benchmark_results.txt; then
        # hey의 응답시간 히스토그램에서 지표 추출
        echo "응답시간 지표:"
        grep -A 20 "Response time histogram:" benchmark_results.txt | grep -E "(50%|95%|99%)" || echo "응답시간 지표 파싱 실패"
    else
        # 대체 방법: Summary 섹션에서 추출
        echo "응답시간 지표 (Summary):"
        grep -A 10 "Summary:" benchmark_results.txt | grep -E "(Average|Slowest|Fastest)" || echo "응답시간 지표 없음"
    fi
    
    # 총 요청 수
    TOTAL_REQUESTS=$(grep "Total:" benchmark_results.txt | awk '{print $2}' || echo "N/A")
    echo "총 요청 수: $TOTAL_REQUESTS"
    
    # 에러 수
    ERRORS=$(grep "Errors:" benchmark_results.txt | awk '{print $2}' || echo "N/A")
    echo "에러 수: $ERRORS"
    
else
    echo "벤치마크 결과 파일을 찾을 수 없습니다."
fi

# 정리
echo
echo "정리 중..."
rm -f $HIT_CODES_FILE $MISS_CODES_FILE benchmark_results.txt

echo "벤치마크 완료!"
