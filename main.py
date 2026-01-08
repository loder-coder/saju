import os
import json
import redis
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
from typing import Optional
from sqlalchemy import text

# 내부 모듈
from app import models, database
from app.services.lunar_service import get_lunar_date
from app.services.saju_engine import calculate_saju, get_fortune_by_period
from app.services.prompt_builder import build_saju_prompt, translate_pillar
from app.services.llm_service import get_ai_analysis

load_dotenv()
models.Base.metadata.create_all(bind=database.engine)

@app.on_event("startup")
def add_column_if_not_exists():
    with database.engine.connect() as conn:
        try:
            # saju_records 테이블에 user_id 컬럼이 있는지 확인하고 없으면 추가
            conn.execute(text("ALTER TABLE saju_records ADD COLUMN IF NOT EXISTS user_id VARCHAR;"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_saju_records_user_id ON saju_records (user_id);"))
            conn.commit()
            print("✅ Database schema updated: user_id column added.")
        except Exception as e:
            print(f"⚠️ Column might already exist or error: {e}")

# Redis 설정 (Railway 환경변수 REDIS_URL 사용)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
r = redis.from_url(REDIS_URL, decode_responses=True)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if not os.path.exists("static"): os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class SajuRequest(BaseModel):
    birth_date: str
    birth_time: str
    timezone: str
    longitude: float
    latitude: float
    include_analysis: bool
    theme: str
    user_id: Optional[str] = None  # 소셜 로그인 UID (Firebase/Google 등)


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/saju")
@limiter.limit("10/minute")
def saju_calculate(request: Request, payload: SajuRequest, db: Session = Depends(database.get_db)):
    # 1. Redis 캐시 키 생성 (생년월일+시간+테마 조합)
    cache_key = f"saju_cache:{payload.birth_date}:{payload.birth_time}:{payload.theme}:{payload.include_analysis}"

    # 2. 캐시 확인
    cached_data = r.get(cache_key)
    if cached_data:
        print("🚀 Redis Cache Hit!")
        return json.loads(cached_data)

    try:
        y, m, d = map(int, payload.birth_date.split("-"))
        h, mn = map(int, payload.birth_time.split(":"))

        lunar = get_lunar_date(y, m, d, h, mn, payload.timezone, payload.longitude)
        adj_h = lunar["solar"]["hour"]
        adj_m = lunar["solar"]["minute"]

        saju = calculate_saju(lunar["lunar"]["year"], lunar["lunar"]["month"], lunar["lunar"]["day"], adj_h, adj_m)

        res_data = {
            "input": payload.dict(),
            "lunar": lunar["lunar"],
            "saju": saju["pillars"],
            "elements": saju["elements"],
            "analysis": None
        }

        # AI 분석 포함 시
        if payload.include_analysis:
            full_context = {"saju": saju}
            prompt = build_saju_prompt(full_context, theme=payload.theme)
            res_data["analysis"] = get_ai_analysis(prompt)

        # 3. DB 저장 및 유저 ID 연동
        day_pillar = translate_pillar(saju["pillars"]["day"])
        new_record = models.SajuRecord(
            birth_date=payload.birth_date,
            birth_time=payload.birth_time,
            timezone=payload.timezone,
            longitude=payload.longitude,
            day_master=day_pillar,
            result_json=res_data,
            # 만약 models.SajuRecord에 user_id 컬럼이 없다면 추가해야 함
            # user_id=payload.user_id
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        res_data["record_id"] = new_record.id

        # 4. Redis 캐싱 (유효기간 1시간 = 3600초)
        r.setex(cache_key, 3600, json.dumps(res_data))

        return res_data
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/saju/{record_id}")
def get_record(record_id: int, db: Session = Depends(database.get_db)):
    rec = db.query(models.SajuRecord).filter(models.SajuRecord.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Not found")
    return rec.result_json


# [NEW] 개인 사주 히스토리 조회 API
@app.get("/history/{user_id}")
def get_user_history(user_id: str, db: Session = Depends(database.get_db)):
    # 최신순으로 해당 유저의 기록 20개 조회
    # (SajuRecord 모델에 user_id 컬럼이 있다고 가정)
    # records = db.query(models.SajuRecord).filter(models.SajuRecord.user_id == user_id).order_by(desc(models.SajuRecord.created_at)).limit(20).all()

    # 현재는 모델 연동 전이라 가이드 메시지 리턴
    return {"message": f"History for user {user_id} - Feature ready in logic, update models.py to enable mapping."}


@app.get("/fortune/{period}/{record_id}")
def get_period_fortune(period: str, record_id: int, db: Session = Depends(database.get_db)):
    rec = db.query(models.SajuRecord).filter(models.SajuRecord.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Not found")

    try:
        user_gan = rec.result_json["saju"]["day"][0]
        fortune = get_fortune_by_period(user_gan, period)
        return fortune
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/manifest.json")
def get_manifest():
    return FileResponse("manifest.json")