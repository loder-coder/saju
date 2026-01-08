from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# 서비스 모듈
from app.services.lunar_service import get_lunar_date
from app.services.saju_engine import calculate_saju, get_today_fortune
from app.services.prompt_builder import build_saju_prompt, translate_pillar
from app.services.llm_service import get_ai_analysis

import models
import database
import os
from dotenv import load_dotenv
from datetime import date

load_dotenv()

# DB 생성
models.Base.metadata.create_all(bind=database.engine)

# [보안] Rate Limiter 설정 (IP당 하루 50회 제한)
limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ... (SajuRequest 클래스는 동일) ...
class SajuRequest(BaseModel):
    birth_date: str = Field(..., description="YYYY-MM-DD format")
    birth_time: str = Field(..., description="HH:MM format")
    timezone: str = Field("Asia/Seoul", description="Timezone string e.g. 'America/New_York'")
    longitude: float = Field(127.0, description="Longitude for solar time correction")
    latitude: float = Field(37.5, description="Latitude (for future use)")
    include_analysis: bool = Field(False, description="Whether to include LLM analysis")


@app.get("/")
def health():
    return FileResponse("index.html")


# [보안] 1분에 5번만 요청 가능
@app.post("/saju")
@limiter.limit("5/minute")
def saju_calculate(request: Request, payload: SajuRequest, db: Session = Depends(database.get_db)):
    # ... (기존 사주 로직 동일) ...
    # ... (중략: lunar_data, saju_data 계산) ...
    try:
        year, month, day = map(int, payload.birth_date.split("-"))
        hour, minute = map(int, payload.birth_time.split(":"))

        lunar_data = get_lunar_date(year, month, day, hour, minute, payload.timezone, payload.longitude)
        adjusted_hour = lunar_data["solar"]["hour"]
        adjusted_minute = lunar_data["solar"]["minute"]
        saju_data = calculate_saju(lunar_data["lunar"]["year"], lunar_data["lunar"]["month"],
                                   lunar_data["lunar"]["day"], adjusted_hour, adjusted_minute)

        response_data = {
            "input": payload.dict(),
            "adjusted_time": lunar_data["solar"],
            "lunar": lunar_data["lunar"],
            "saju": saju_data["pillars"],
            "elements": saju_data["elements"],
            "analysis": None
        }

        if payload.include_analysis:
            full_saju_context = {"saju": saju_data}
            prompt = build_saju_prompt(full_saju_context)
            analysis_result = get_ai_analysis(prompt)
            response_data["analysis"] = analysis_result

        day_pillar_en = translate_pillar(saju_data["pillars"]["day"])
        new_record = models.SajuRecord(
            birth_date=payload.birth_date, birth_time=payload.birth_time, timezone=payload.timezone,
            longitude=payload.longitude, day_master=day_pillar_en, result_json=response_data
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        response_data["record_id"] = new_record.id
        return response_data
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/saju/{record_id}")
def get_saju_record(record_id: int, db: Session = Depends(database.get_db)):
    record = db.query(models.SajuRecord).filter(models.SajuRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record.result_json


# [NEW] 오늘의 운세 API
@app.get("/fortune/daily/{record_id}")
def get_daily_fortune_api(record_id: int, db: Session = Depends(database.get_db)):
    record = db.query(models.SajuRecord).filter(models.SajuRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="User record not found")

    # DB에 저장된 사주 데이터에서 '일간(Day Gan)' 추출
    # 저장된 JSON 구조: record.result_json['saju']['day'] -> "戊寅"
    try:
        day_pillar = record.result_json['saju']['day']  # "戊寅"
        day_gan = day_pillar[0]  # "戊"

        today_str = str(date.today())
        fortune = get_today_fortune(day_gan, today_str)

        return fortune
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fortune Error: {str(e)}")


# [PWA] manifest.json 서빙
@app.get("/manifest.json")
def get_manifest():
    return FileResponse("manifest.json")


# [PWA] Service Worker 서빙
@app.get("/sw.js")
def get_sw():
    return FileResponse("sw.js")