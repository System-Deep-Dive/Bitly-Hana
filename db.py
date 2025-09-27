import sqlite3
from pathlib import Path
import importlib
import settings

DB_PATH = "url_shortener.db"


def get_db_connection():
    """SQLite 데이터베이스 연결을 반환합니다."""
    return sqlite3.connect(DB_PATH)


def _load_sql_for_strategy(strategy_name: str) -> str:
    """전략 이름에 맞는 SQL 초기화 파일을 로드"""
    sql_dir = Path(__file__).parent / "sql"
    if strategy_name == "FULLSCAN":
        return (sql_dir / "v1_init.sql").read_text(encoding="utf-8")
    elif strategy_name == "INDEXED":
        # V1 스키마 + V2 인덱스 적용
        v1 = (sql_dir / "v1_init.sql").read_text(encoding="utf-8")
        v2 = (sql_dir / "v2_add_index.sql").read_text(encoding="utf-8")
        return v1 + "\n" + v2
    # 필요 시 다른 전략도 확장
    else:
        raise ValueError(f"알 수 없는 전략: {strategy_name}")


def init_database():
    """선택된 전략에 맞는 스키마 초기화"""
    sql_script = _load_sql_for_strategy(settings.DEFAULT_STRATEGY)
    conn = get_db_connection()
    try:
        conn.executescript(sql_script)
        conn.commit()
        print(f"데이터베이스 스키마가 초기화되었습니다 (strategy={settings.DEFAULT_STRATEGY})")
    except Exception as e:
        print(f"데이터베이스 초기화 중 오류 발생: {e}")
        raise
    finally:
        conn.close()


def get_strategy_instance():
    """settings.AVAILABLE_STRATEGIES에 정의된 전략 클래스 인스턴스 반환"""
    class_path = settings.AVAILABLE_STRATEGIES[settings.DEFAULT_STRATEGY]
    module_name, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    strategy_class = getattr(module, class_name)
    return strategy_class()


if __name__ == "__main__":
    init_database()
