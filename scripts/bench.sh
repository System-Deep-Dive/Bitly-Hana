#!/bin/bash

# URL 단축기 성능 벤치마크 스크립트 (FULLSCAN vs INDEXED 비교)
# 전제: 서버가 :8000에서 실행 중

set -e

BASE_URL="http://localhost:8000"
HIT_CODES_FILE="hit_codes.txt"
MISS_CODES_FILE="miss_codes.txt"
BENCHMARK_DURATION="30s"
CONCURRENCY=50
SETTINGS_FILE="settings.py"
BACKUP_SETTINGS="settings.py.backup"

echo "=== URL 단축기 성능 벤치마크 (FULLSCAN vs INDEXED) ==="
echo "서버: $BASE_URL"
echo "지속시간: $BENCHMARK_DURATION"
echo "동시성: $CONCURRENCY"
echo

# settings.py 백업
cp $SETTINGS_FILE $BACKUP_SETTINGS
echo "settings.py 백업 완료: $BACKUP_SETTINGS"

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

# 3. hey 경로 설정
HEY_CMD="hey"
if ! command -v hey &> /dev/null; then
    if [ -f "$HOME/go/bin/hey" ]; then
        HEY_CMD="$HOME/go/bin/hey"
        echo "hey를 $HEY_CMD에서 찾았습니다."
    else
        echo "오류: hey가 설치되지 않았습니다."
        echo "설치 방법: go install github.com/rakyll/hey@latest"
        # 백업 복원
        mv $BACKUP_SETTINGS $SETTINGS_FILE
        exit 1
    fi
fi

# 벤치마크 실행 함수
run_benchmark() {
    local strategy=$1
    local output_file=$2
    
    echo
    echo "=== $strategy 전략 벤치마크 실행 ==="
    echo "히트/미스 비율: 50:50"
    
    # 히트 요청과 미스 요청을 섞어서 실행
    $HEY_CMD -z $BENCHMARK_DURATION -c $CONCURRENCY \
        -m GET \
        -H "Accept: application/json" \
        -D $HIT_CODES_FILE \
        -D $MISS_CODES_FILE \
        $BASE_URL/{} \
        > $output_file 2>&1
    
    echo "$strategy 벤치마크 완료: $output_file"
}

# 결과 파싱 함수
parse_benchmark_results() {
    local result_file=$1
    local strategy=$2
    
    if [ ! -f "$result_file" ]; then
        echo "결과 파일을 찾을 수 없습니다: $result_file"
        return 1
    fi
    
    # RPS 추출
    local rps=$(grep "Requests/sec:" "$result_file" | awk '{print $2}' || echo "N/A")
    
    # 응답시간 지표 추출 (p50, p95, p99)
    local p50=$(grep -A 20 "Latency distribution:" "$result_file" | grep "50%" | awk '{print $3}' | sed 's/secs//' || echo "N/A")
    local p95=$(grep -A 20 "Latency distribution:" "$result_file" | grep "95%" | awk '{print $3}' | sed 's/secs//' || echo "N/A")
    local p99=$(grep -A 20 "Latency distribution:" "$result_file" | grep "99%" | awk '{print $3}' | sed 's/secs//' || echo "N/A")
    
    # 총 요청 수
    local total_requests=$(grep "Total:" "$result_file" | awk '{print $2}' || echo "N/A")
    
    # 에러 수
    local errors=$(grep "Errors:" "$result_file" | awk '{print $2}' || echo "N/A")
    
    # 결과를 전역 변수에 저장
    if [ "$strategy" = "FULLSCAN" ]; then
        FULLSCAN_RPS="$rps"
        FULLSCAN_P50="$p50"
        FULLSCAN_P95="$p95"
        FULLSCAN_P99="$p99"
        FULLSCAN_TOTAL="$total_requests"
        FULLSCAN_ERRORS="$errors"
    else
        INDEXED_RPS="$rps"
        INDEXED_P50="$p50"
        INDEXED_P95="$p95"
        INDEXED_P99="$p99"
        INDEXED_TOTAL="$total_requests"
        INDEXED_ERRORS="$errors"
    fi
}

# 4. FULLSCAN 전략 벤치마크
echo
echo "=== FULLSCAN 전략 설정 ==="
sed -i.bak 's/DEFAULT_STRATEGY = ".*"/DEFAULT_STRATEGY = "FULLSCAN"/' $SETTINGS_FILE
echo "DEFAULT_STRATEGY를 FULLSCAN으로 변경했습니다."
echo "⚠️  서버를 재시작하세요! (Ctrl+C로 중단 후 python3 app.py 실행)"
echo "서버 재시작 후 Enter를 눌러 계속하세요..."
read -r

run_benchmark "FULLSCAN" "benchmark_fullscan.txt"
parse_benchmark_results "benchmark_fullscan.txt" "FULLSCAN"

# 5. INDEXED 전략 벤치마크
echo
echo "=== INDEXED 전략 설정 ==="
sed -i.bak 's/DEFAULT_STRATEGY = ".*"/DEFAULT_STRATEGY = "INDEXED"/' $SETTINGS_FILE
echo "DEFAULT_STRATEGY를 INDEXED로 변경했습니다."
echo "⚠️  서버를 재시작하세요! (Ctrl+C로 중단 후 python3 app.py 실행)"
echo "서버 재시작 후 Enter를 눌러 계속하세요..."
read -r

run_benchmark "INDEXED" "benchmark_indexed.txt"
parse_benchmark_results "benchmark_indexed.txt" "INDEXED"

# 6. settings.py 원복
echo
echo "=== 설정 원복 ==="
mv $BACKUP_SETTINGS $SETTINGS_FILE
echo "settings.py를 원래 상태로 복원했습니다."

# 7. 결과 비교 요약
echo
echo "=== 벤치마크 결과 비교 요약 ==="
echo
printf "%-15s %-15s %-15s %-15s\n" "지표" "FULLSCAN" "INDEXED" "개선도"
echo "----------------------------------------------------------------"
printf "%-15s %-15s %-15s %-15s\n" "RPS" "$FULLSCAN_RPS" "$INDEXED_RPS" "N/A"
printf "%-15s %-15s %-15s %-15s\n" "P50 (ms)" "$FULLSCAN_P50" "$INDEXED_P50" "N/A"
printf "%-15s %-15s %-15s %-15s\n" "P95 (ms)" "$FULLSCAN_P95" "$INDEXED_P95" "N/A"
printf "%-15s %-15s %-15s %-15s\n" "P99 (ms)" "$FULLSCAN_P99" "$INDEXED_P99" "N/A"
printf "%-15s %-15s %-15s %-15s\n" "Total Requests" "$FULLSCAN_TOTAL" "$INDEXED_TOTAL" "N/A"
printf "%-15s %-15s %-15s %-15s\n" "Errors" "$FULLSCAN_ERRORS" "$INDEXED_ERRORS" "N/A"
echo

# 8. 상세 결과 출력
echo "=== FULLSCAN 상세 결과 ==="
if [ -f "benchmark_fullscan.txt" ]; then
    cat benchmark_fullscan.txt
else
    echo "FULLSCAN 결과 파일을 찾을 수 없습니다."
fi

echo
echo "=== INDEXED 상세 결과 ==="
if [ -f "benchmark_indexed.txt" ]; then
    cat benchmark_indexed.txt
else
    echo "INDEXED 결과 파일을 찾을 수 없습니다."
fi

# 9. 정리
echo
echo "=== 정리 ==="
echo "임시 파일 정리 중..."
rm -f $HIT_CODES_FILE $MISS_CODES_FILE
rm -f $SETTINGS_FILE.bak
rm -f settings.py.bak

echo
echo "벤치마크 완료!"
echo "결과 파일:"
echo "  - benchmark_fullscan.txt"
echo "  - benchmark_indexed.txt"