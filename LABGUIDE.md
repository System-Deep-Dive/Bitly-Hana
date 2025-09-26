# Bitly-Hana: URL 단축기 성능 실습 가이드

이 프로젝트는 URL 단축기를 직접 구현하면서, 아래 단계별로 성능을 비교하고 학습하는 실습을 목표로 함.

**풀스캔 → 인덱스 → 애플리케이션 캐시 → Redis 캐시**

## 실습 순서

### 0. 환경 준비

-   Python 3.10+
-   FastAPI, SQLite, Redis (docker-compose)
-   의존성 설치

```bash
    pip install -r requirements.txt
```

### 1. 풀스캔 베이스라인

-   url_mapping 테이블 생성 (인덱스 없음)
-   단축 생성 API: POST /urls
-   리디렉션 API: GET /{short_code} → 풀스캔 조회
-   성능 측정: wrk/hey로 p95 지연시간 기록

### 2. 데이터베이스 인덱스 추가

-   short_code 컬럼에 UNIQUE 인덱스 추가
-   조회 속도 개선 확인
-   성능 측정: 풀스캔 대비 개선폭 기록

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
