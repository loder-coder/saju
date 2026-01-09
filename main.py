import json
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# 파일 구조에 따라 임포트 경로 자동 조절
try:
    from app import database, models
except ImportError:
    import database, models

from pydantic import BaseModel
from typing import Optional
import redis
import os

# 서비스 레이어 임포트
try:
    from app.services.lunar_service import get_lunar_date
    from app.services.saju_engine import calculate_saju, get_fortune_by_period
    from app.services.prompt_builder import build_saju_prompt, translate_pillar
    from app.services.llm_service import get_ai_analysis
except ImportError:
    from services.lunar_service import get_lunar_date
    from services.saju_engine import calculate_saju, get_fortune_by_period
    from services.prompt_builder import build_saju_prompt, translate_pillar
    from services.llm_service import get_ai_analysis

app = FastAPI()


# [중요] 서버 시작 시 실행될 로직
@app.on_event("startup")
def startup_event():
    print("🚀 [STARTUP] Checking Database Connection...")
    # 현재 연결된 DB 주소 출력 (비밀번호 제외)
    db_url = str(database.engine.url).split('@')[-1]
    print(f"📡 [DB-INFO] Connecting to: {db_url}")

    try:
        # 테이블 생성 강제 실행
        models.Base.metadata.create_all(bind=database.engine)
        print("✅ [DB-INFO] Database tables checked/created successfully.")
    except Exception as e:
        print(f"❌ [DB-ERROR] Failed to create tables: {e}")


limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Redis 설정
REDIS_URL = os.getenv("REDIS_URL")
r = redis.from_url(REDIS_URL) if REDIS_URL else None


# --- 아래는 기존 API 로직과 동일 (생략 금지, 전체 복사해서 사용하셈) ---

class SajuRequest(BaseModel):
    birth_date: str
    birth_time: str
    timezone: str = "Asia/Seoul"
    longitude: float = 127.0
    latitude: float = 37.5
    include_analysis: bool = False
    theme: str = "general"
    user_id: Optional[str] = None


class UserLogin(BaseModel):
    uid: str
    email: str
    provider: str = "google"


@app.post("/login")
def login_user(payload: UserLogin, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.uid == payload.uid).first()
    if not user:
        user = models.User(uid=payload.uid, email=payload.email, provider=payload.provider)
        db.add(user)
    else:
        user.email = payload.email
    db.commit()
    db.refresh(user)
    return {"status": "ok", "uid": user.uid}


@app.post("/saju")
@limiter.limit("15/minute")
def saju_calculate(request: Request, payload: SajuRequest, db: Session = Depends(database.get_db)):
    cache_key = f"cache:{payload.birth_date}:{payload.birth_time}:{payload.theme}:{payload.user_id}"
    if r:
        cached = r.get(cache_key)
        if cached: return json.loads(cached)

    try:
        y, m, d = map(int, payload.birth_date.split("-"))
        h, mn = map(int, payload.birth_time.split(":"))
        lunar = get_lunar_date(y, m, d, h, mn, payload.timezone, payload.longitude)
        saju_res = calculate_saju(lunar["lunar"]["year"], lunar["lunar"]["month"], lunar["lunar"]["day"],
                                  lunar["solar"]["hour"], lunar["solar"]["minute"])

        analysis_result = None
        if payload.include_analysis:
            prompt = build_saju_prompt({"saju": saju_res}, theme=payload.theme)
            analysis_result = get_ai_analysis(prompt)

        res_data = {"input": payload.dict(), "lunar": lunar["lunar"], "saju": saju_res["pillars"],
                    "elements": saju_res["elements"], "analysis": analysis_result}

        new_record = models.SajuRecord(
            user_id=payload.user_id, birth_date=payload.birth_date, birth_time=payload.birth_time,
            timezone=payload.timezone, longitude=payload.longitude,
            day_master=translate_pillar(saju_res["pillars"]["day"]), result_json=res_data
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        res_data["record_id"] = new_record.id

        if r: r.setex(cache_key, 3600, json.dumps(res_data))
        return res_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{user_id}")
def get_history(user_id: str, db: Session = Depends(database.get_db)):
    records = db.query(models.SajuRecord).filter(models.SajuRecord.user_id == user_id).order_by(
        models.SajuRecord.created_at.desc()).limit(10).all()
    return [{"record_id": rec.id, "created_at": rec.created_at.isoformat(), **rec.result_json} for rec in records]


@app.get("/fortune/{period}/{record_id}")
def get_period_fortune(period: str, record_id: int, db: Session = Depends(database.get_db)):
    rec = db.query(models.SajuRecord).filter(models.SajuRecord.id == record_id).first()
    if not rec: raise HTTPException(status_code=404, detail="Not found")
    user_gan = rec.result_json["saju"]["day"][0]
    return get_fortune_by_period(user_gan, period)


@app.get("/manifest.json")
def get_manifest(): return FileResponse("manifest.json")