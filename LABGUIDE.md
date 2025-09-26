# Bitly-Hana: URL 단축기 성능 실습 가이드

이 프로젝트는 URL 단축기를 직접 구현하면서, 아래 단계별로 성능을 비교하고 학습하는 실습을 목표로 함.

**풀스캔 → 인덱스 → 애플리케이션 캐시 → Redis 캐시**

## 프로젝트 구조

(문서화를 위한 .gitignore, md 확장자 파일은 생략됨.)

```
bitly-hana/
├─ app.py                 # FastAPI 엔트리
├─ db.py                  # SQLite 연결/DDL 실행
├─ settings.py            # 설정(전략, Redis, 기본 호스트 등)
├─ cache/
│  ├─ __init__.py
│  ├─ lru_cache.py        # 애플리케이션 LRU 캐시
│  └─ redis_cache.py      # Redis 캐시(키, TTL, 네거티브 캐시)
├─ strategy/
│  ├─ __init__.py
│  ├─ base.py             # 조회 전략 인터페이스
│  ├─ fullscan.py         # 풀스캔 전략
│  ├─ indexed.py          # 인덱스 전략
│  ├─ app_cache.py        # 앱 LRU 캐시 전략
│  └─ redis_strategy.py   # Redis 캐시 전략
├─ sql/
│  ├─ v1_init.sql         # V1 스키마(인덱스 없음)
│  └─ v2_add_index.sql    # V2 인덱스 추가
├─ scripts/               # 실험/벤치마크 유틸 모음
│  ├─ seed.py
│  └─ bench.sh
├─ requirements.txt
└─ docker-compose.yml    # Redis
```

## 엔티티 설계

### URL 매핑 (핵심 엔티티)

-   **short_code** (TEXT): 단축 URL 코드 (예: aB12xY)
-   **original_url** (TEXT): 원본 긴 URL
-   **created_at** (TIMESTAMP): 생성 시각 (옵션)

## 단계별 스키마

### V1: 인덱스 없이 풀스캔 실험

**sql/v1_init.sql**

```sql
CREATE TABLE IF NOT EXISTS url_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    short_code   TEXT NOT NULL,
    original_url TEXT NOT NULL,
    created_at   TEXT DEFAULT (datetime('now'))
);
```

### V2: short_code에 UNIQUE 인덱스 추가

**sql/v2_add_index.sql**

```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_url_mapping_short_code
ON url_mapping(short_code);
```

## 실습 순서

### 0. 환경 준비

-   Python 3.10+
-   가상환경(venv 또는 conda) 생성 권장
    ```bash
    python -m venv .venv
    source .venv/bin/activate   # macOS/Linux
    .venv\\Scripts\\activate    # Windows
    ```
-   FastAPI, SQLite, Redis (docker-compose)
-   의존성 설치
    ```bash
    pip install -r requirements.txt
    ```

### 1. 풀스캔 베이스라인

-   url_mapping 테이블 생성 (인덱스 없음)
-   더미 데이터 스크립트 실행
-   단축 생성 API: POST /urls
-   리디렉션 API: GET /{short_code} (풀스캔 조회)
-   wrk/hey로 p95 지연시간 기록

### 2. 데이터베이스 인덱스 추가

-   short_code 컬럼에 UNIQUE 인덱스 추가
-   조회 속도 개선 확인
-   풀스캔 대비 개선폭 기록

### 3. 애플리케이션 캐시 (LRU)

-   Python OrderedDict 기반 LRU 캐시 구현
-   조회 시 캐시 우선 조회 → 미스 시 DB 접근
-   캐시 적중률, 메모리 크기, 성능 비교

### 4. Redis 분산 캐시

-   Redis를 도입해 캐시를 외부화
-   TTL + LRU 정책 적용
-   네거티브 캐시 및 스탬피드 방지 기법 실습
-   장애 발생 시 DB 폴백 확인

### 5. 관측 및 비교

-   단계별 성능 결과(p50, p95, p99, RPS) 기록
-   캐시 적중률과 DB 부하 변화 비교

## 학습 포인트

-   읽기 트래픽이 압도적인 시스템에서의 성능 병목
-   데이터베이스 인덱스의 효과
-   애플리케이션 캐시의 한계와 Redis 도입 필요성
-   캐시 전략(LRU, TTL, 네거티브 캐시)의 실제 효과
