import json
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import FileResponse  # 👈 이거 추가됨
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import database, models
from pydantic import BaseModel
from typing import Optional
import redis
import os

# 서비스 레이어 임포트
from app.services.lunar_service import get_lunar_date
from app.services.saju_engine import calculate_saju, get_fortune_by_period
from app.services.prompt_builder import build_saju_prompt, translate_pillar
from app.services.llm_service import get_ai_analysis

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Redis 설정
REDIS_URL = os.getenv("REDIS_URL")
r = redis.from_url(REDIS_URL) if REDIS_URL else None


# 요청 모델
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
        user = models.User(
            uid=payload.uid,
            email=payload.email,
            provider=payload.provider,
            is_premium=False
        )
        db.add(user)
        print(f"🆕 New User Registered: {payload.uid}")
    else:
        user.email = payload.email
        print(f"✅ Existing User Logged In: {payload.uid}")

    db.commit()
    db.refresh(user)
    return {"status": "ok", "uid": user.uid}


@app.post("/saju")
@limiter.limit("15/minute")
def saju_calculate(request: Request, payload: SajuRequest, db: Session = Depends(database.get_db)):
    cache_key = f"cache:{payload.birth_date}:{payload.birth_time}:{payload.theme}:{payload.include_analysis}:{payload.user_id}"
    if r:
        cached = r.get(cache_key)
        if cached:
            return json.loads(cached)

    try:
        y, m, d = map(int, payload.birth_date.split("-"))
        h, mn = map(int, payload.birth_time.split(":"))

        lunar = get_lunar_date(y, m, d, h, mn, payload.timezone, payload.longitude)
        saju_res = calculate_saju(
            lunar["lunar"]["year"],
            lunar["lunar"]["month"],
            lunar["lunar"]["day"],
            lunar["solar"]["hour"],
            lunar["solar"]["minute"]
        )

        analysis_result = None
        if payload.include_analysis:
            prompt = build_saju_prompt({"saju": saju_res}, theme=payload.theme)
            analysis_result = get_ai_analysis(prompt)

        res_data = {
            "input": payload.dict(),
            "lunar": lunar["lunar"],
            "saju": saju_res["pillars"],
            "elements": saju_res["elements"],
            "analysis": analysis_result
        }

        day_pillar_translated = translate_pillar(saju_res["pillars"]["day"])
        new_record = models.SajuRecord(
            user_id=payload.user_id,
            birth_date=payload.birth_date,
            birth_time=payload.birth_time,
            timezone=payload.timezone,
            longitude=payload.longitude,
            day_master=day_pillar_translated,
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
        print(f"❌ Saju Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{user_id}")
def get_history(user_id: str, db: Session = Depends(database.get_db)):
    # 히스토리 불러올 때 id랑 날짜 정보도 같이 보내주는 게 프론트에서 다루기 편함
    records = db.query(models.SajuRecord).filter(models.SajuRecord.user_id == user_id).order_by(
        models.SajuRecord.created_at.desc()).limit(10).all()

    output = []
    for rec in records:
        data = rec.result_json
        data["record_id"] = rec.id  # id 강제 주입
        data["created_at"] = rec.created_at.isoformat()
        output.append(data)
    return output


@app.get("/fortune/{period}/{record_id}")
def get_period_fortune(period: str, record_id: int, db: Session = Depends(database.get_db)):
    rec = db.query(models.SajuRecord).filter(models.SajuRecord.id == record_id).first()
    if not rec: raise HTTPException(status_code=404, detail="Not found")
    try:
        # result_json에서 일간(Day Master)의 천간 글자 따오기
        user_gan = rec.result_json["saju"]["day"][0]
        fortune = get_fortune_by_period(user_gan, period)
        return fortune
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/manifest.json")
def get_manifest():
    return FileResponse("manifest.json")