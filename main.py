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

# 같은 위치에 있는 모듈들
import models
import database
import os
from dotenv import load_dotenv
from datetime import date

load_dotenv()

# DB 생성
models.Base.metadata.create_all(bind=database.engine)

# [보안] Rate Limiter 설정 (IP당 분당 5회 제한)
limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


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
        print(f"Error processing saju: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/saju/{record_id}")
def get_saju_record(record_id: int, db: Session = Depends(database.get_db)):
    record = db.query(models.SajuRecord).filter(models.SajuRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record.result_json


# 오늘의 운세 API
@app.get("/fortune/daily/{record_id}")
def get_daily_fortune_api(record_id: int, db: Session = Depends(database.get_db)):
    record = db.query(models.SajuRecord).filter(models.SajuRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    try:
        # result_json -> saju -> day -> 첫 글자 (예: "甲")
        user_day_gan = record.result_json["saju"]["day"][0]
        fortune = get_today_fortune(user_day_gan)
        return fortune
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fortune calculation failed: {str(e)}")


# [PWA] manifest.json 서빙
@app.get("/manifest.json")
def get_manifest():
    return FileResponse("manifest.json")