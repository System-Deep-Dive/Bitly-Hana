-- V2: short_code 컬럼에 UNIQUE 인덱스 추가
-- 이미 인덱스가 존재하면 중복 생성되지 않도록 IF NOT EXISTS 사용

CREATE UNIQUE INDEX IF NOT EXISTS idx_url_mapping_short_code
ON url_mapping(short_code);
