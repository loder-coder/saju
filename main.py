import os
import json
import redis
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
from typing import Optional

# 내부 모듈
from app import models, database
from app.services.lunar_service import get_lunar_date
from app.services.saju_engine import calculate_saju, get_fortune_by_period
from app.services.prompt_builder import build_saju_prompt, translate_pillar
from app.services.llm_service import get_ai_analysis

load_dotenv()
models.Base.metadata.create_all(bind=database.engine)

# 1. Limiter 정의
limiter = Limiter(key_func=get_remote_address)

# 2. FastAPI 'app' 객체 생성 (이게 데코레이터들보다 무조건 위에 있어야 함!)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Redis 설정
REDIS_URL = os.getenv("REDIS_URL")
r = None
if REDIS_URL:
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        print("✅ Redis Connected")
    except Exception as e:
        print(f"❌ Redis Connection Failed: {e}")

# 정적 파일 및 템플릿 설정
if not os.path.exists("static"): os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# 3. 데이터베이스 컬럼 수동 추가 로직 (Startup Event)
@app.on_event("startup")
def add_column_if_not_exists():
    with database.engine.connect() as conn:
        try:
            # saju_records 테이블에 user_id 컬럼이 없으면 추가
            conn.execute(text("ALTER TABLE saju_records ADD COLUMN IF NOT EXISTS user_id VARCHAR;"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_saju_records_user_id ON saju_records (user_id);"))
            conn.commit()
            print("✅ Database schema updated: user_id column added.")
        except Exception as e:
            print(f"⚠️ DB Update Note: {e}")


class SajuRequest(BaseModel):
    birth_date: str
    birth_time: str
    timezone: str
    longitude: float
    latitude: float
    include_analysis: bool
    theme: str
    user_id: Optional[str] = None


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/saju")
@limiter.limit("15/minute")
def saju_calculate(request: Request, payload: SajuRequest, db: Session = Depends(database.get_db)):
    cache_key = f"cache:{payload.birth_date}:{payload.birth_time}:{payload.theme}:{payload.include_analysis}"
    if r:
        cached = r.get(cache_key)
        if cached:
            return json.loads(cached)

    try:
        y, m, d = map(int, payload.birth_date.split("-"))
        h, mn = map(int, payload.birth_time.split(":"))

        lunar = get_lunar_date(y, m, d, h, mn, payload.timezone, payload.longitude)
        saju = calculate_saju(lunar["lunar"]["year"], lunar["lunar"]["month"], lunar["lunar"]["day"],
                              lunar["solar"]["hour"], lunar["solar"]["minute"])

        res_data = {
            "input": payload.dict(),
            "lunar": lunar["lunar"],
            "saju": saju["pillars"],
            "elements": saju["elements"],
            "analysis": None
        }

        if payload.include_analysis:
            prompt = build_saju_prompt({"saju": saju}, theme=payload.theme)
            res_data["analysis"] = get_ai_analysis(prompt)

        day_pillar = translate_pillar(saju["pillars"]["day"])
        new_record = models.SajuRecord(
            user_id=payload.user_id,
            birth_date=payload.birth_date,
            birth_time=payload.birth_time,
            timezone=payload.timezone,
            longitude=payload.longitude,
            day_master=day_pillar,
            result_json=res_data
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        res_data["record_id"] = new_record.id

        if r:
            r.setex(cache_key, 3600, json.dumps(res_data))

        return res_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{user_id}")
def get_history(user_id: str, db: Session = Depends(database.get_db)):
    records = db.query(models.SajuRecord).filter(models.SajuRecord.user_id == user_id).order_by(
        models.SajuRecord.created_at.desc()).limit(10).all()
    return [rec.result_json for rec in records]


@app.get("/fortune/{period}/{record_id}")
def get_period_fortune(period: str, record_id: int, db: Session = Depends(database.get_db)):
    rec = db.query(models.SajuRecord).filter(models.SajuRecord.id == record_id).first()
    if not rec: raise HTTPException(status_code=404, detail="Not found")
    try:
        user_gan = rec.result_json["saju"]["day"][0]
        fortune = get_fortune_by_period(user_gan, period)
        return fortune
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/manifest.json")
def get_manifest():
    return FileResponse("manifest.json")