"""애플리케이션 설정"""

# URL 단축 전략 설정
DEFAULT_STRATEGY = "INDEXED"  # FULLSCAN, INDEXED, APP_CACHE, REDIS 중 선택

# 지원되는 전략들
AVAILABLE_STRATEGIES = {
    "FULLSCAN": "strategy.fullscan.FullScanStrategy",
    "INDEXED": "strategy.indexed.IndexedStrategy",
    # 향후 추가될 전략들 (3, 4단계에서 구현)
    # "APP_CACHE": "strategy.app_cache.AppCacheStrategy", 
    # "REDIS": "strategy.redis_strategy.RedisStrategy",
}

# 기본 호스트 설정
BASE_URL = "http://localhost:8000"

# Redis 설정 (향후 사용)
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
