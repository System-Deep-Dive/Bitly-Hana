#!/bin/bash

# URL 단축기 성능 벤치마크 스크립트 (FULLSCAN vs INDEXED vs APP_CACHE 비교)
# 전제: 서버가 :8000에서 실행 중

set -e

BASE_URL="http://localhost:8000"
BENCHMARK_DURATION="30s"
CONCURRENCY=50
SETTINGS_FILE="settings.py"

echo "=== URL 단축기 성능 벤치마크 (FULLSCAN vs INDEXED vs APP_CACHE) ==="
echo "서버: $BASE_URL"
echo "지속시간: $BENCHMARK_DURATION"
echo "동시성: $CONCURRENCY"
echo

# 원본 전략 값 저장
ORIGINAL_STRATEGY=$(grep 'DEFAULT_STRATEGY = ' $SETTINGS_FILE | sed 's/.*DEFAULT_STRATEGY = "\(.*\)".*/\1/')
echo "원본 전략 저장: $ORIGINAL_STRATEGY"

# 1. 히트/미스 코드를 메모리에서 생성하고 합치기
echo "1. 테스트 데이터 준비 중..."
HIT_CODES=$(python3 -c "
import sqlite3
import random
conn = sqlite3.connect('url_shortener.db')
cursor = conn.cursor()
cursor.execute('SELECT short_code FROM url_mapping')
all_codes = [row[0] for row in cursor.fetchall()]
conn.close()

# 100개 랜덤 선택 (데이터가 100개 미만이면 전체 사용)
hit_codes = random.sample(all_codes, min(100, len(all_codes)))
print(' '.join(hit_codes))
")

MISS_CODES=$(python3 -c "
import random
import string

def generate_random_code():
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(6))

miss_codes = [generate_random_code() for _ in range(100)]
print(' '.join(miss_codes))
")

# 히트/미스 코드를 합쳐서 섞기
COMBINED_CODES=$(echo "$HIT_CODES $MISS_CODES" | tr ' ' '\n' | shuf)
echo "테스트 데이터 준비 완료 (히트: 100개, 미스: 100개, 총 200개)"

# 2. hey 경로 설정
HEY_CMD="hey"
if ! command -v hey &> /dev/null; then
    if [ -f "$HOME/go/bin/hey" ]; then
        HEY_CMD="$HOME/go/bin/hey"
        echo "hey를 $HEY_CMD에서 찾았습니다."
    else
        echo "오류: hey가 설치되지 않았습니다."
        echo "설치 방법: go install github.com/rakyll/hey@latest"
        exit 1
    fi
fi

# 벤치마크 실행 함수
run_benchmark() {
    local strategy=$1
    
    echo
    echo "=== $strategy 전략 벤치마크 실행 ==="
    echo "히트/미스 비율: 50:50"
    echo "----------------------------------------"
    
    # 합쳐진 코드를 단일 입력 스트림으로 사용
    $HEY_CMD -z $BENCHMARK_DURATION -c $CONCURRENCY \
        -m GET \
        -H "Accept: application/json" \
        -D <(echo "$COMBINED_CODES") \
        $BASE_URL/{}
    
    echo "----------------------------------------"
    echo "$strategy 벤치마크 완료"
}

# 전략 설정 함수
set_strategy() {
    local strategy=$1
    echo
    echo "=== $strategy 전략 설정 ==="
    sed -i.bak "s/DEFAULT_STRATEGY = \".*\"/DEFAULT_STRATEGY = \"$strategy\"/" $SETTINGS_FILE
    echo "DEFAULT_STRATEGY를 $strategy로 변경했습니다."
    echo "⚠️  서버를 재시작하세요! (Ctrl+C로 중단 후 python3 app.py 실행)"
    echo "서버 재시작 후 Enter를 눌러 계속하세요..."
    read -r
}

# 3. FULLSCAN 전략 벤치마크
set_strategy "FULLSCAN"
run_benchmark "FULLSCAN"

# 4. INDEXED 전략 벤치마크
set_strategy "INDEXED"
run_benchmark "INDEXED"

# 5. APP_CACHE 전략 벤치마크
set_strategy "APP_CACHE"
run_benchmark "APP_CACHE"

# 6. 원본 전략 복구
echo
echo "=== 원본 전략 복구 ==="
sed -i.bak "s/DEFAULT_STRATEGY = \".*\"/DEFAULT_STRATEGY = \"$ORIGINAL_STRATEGY\"/" $SETTINGS_FILE
echo "DEFAULT_STRATEGY를 원본 값($ORIGINAL_STRATEGY)으로 복구했습니다."

# 7. 정리
echo
echo "=== 정리 ==="
echo "임시 파일 정리 중..."
rm -f $SETTINGS_FILE.bak

echo
echo "벤치마크 완료!"
echo "원본 전략 복구 완료"
echo "모든 전략의 성능 비교가 완료되었습니다."