from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional
from db import init_database, get_strategy_instance

# FastAPI 앱 생성
app = FastAPI(title="Bitly-Hana URL Shortener", version="1.0.0")

# 전략 인스턴스 생성 (db.py의 통합된 함수 사용)
url_strategy = get_strategy_instance()

# Pydantic 모델
class URLRequest(BaseModel):
    original_url: HttpUrl  # 자동으로 URL 검증
    short_code: Optional[str] = None

class URLResponse(BaseModel):
    short_code: str
    original_url: str
    short_url: str


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 데이터베이스 초기화"""
    init_database()


@app.post("/urls", response_model=URLResponse, status_code=201)
async def create_short_url(request: URLRequest):
    """단축 URL 생성 API"""
    try:
        # HttpUrl을 문자열로 변환
        original_url_str = str(request.original_url)
        
        result = url_strategy.create_short_url(
            original_url=original_url_str,
            short_code=request.short_code
        )
        return URLResponse(**result)
    except Exception as e:
        error_msg = str(e)
        if error_msg.startswith("409:"):
            raise HTTPException(status_code=409, detail=error_msg[4:])  # "409: " 제거
        else:
            raise HTTPException(status_code=500, detail=error_msg)


@app.get("/{short_code}")
async def redirect_url(short_code: str):
    """단축 URL 리디렉션 API (풀스캔 조회)"""
    original_url = url_strategy.resolve(short_code)
    
    if original_url is None:
        raise HTTPException(status_code=404, detail="Not found")
    
    # 307 Temporary Redirect로 리디렉션
    return RedirectResponse(url=original_url, status_code=307)


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "Bitly-Hana URL Shortener API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
