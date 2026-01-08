from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.services.lunar_service import get_lunar_date
from app.services.saju_engine import calculate_saju
from app.services.prompt_builder import build_saju_prompt, translate_pillar
from app.services.llm_service import get_ai_analysis
from app import models, database

import os
from dotenv import load_dotenv

# .env 로드
load_dotenv()

# DB 테이블 생성 (앱 시작 시 자동 실행)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()


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


@app.post("/saju")
def saju_calculate(payload: SajuRequest, db: Session = Depends(database.get_db)):
    try:
        year, month, day = map(int, payload.birth_date.split("-"))
        hour, minute = map(int, payload.birth_time.split(":"))

        # 1. Lunar Service 호출
        lunar_data = get_lunar_date(
            year, month, day, hour, minute,
            timezone_str=payload.timezone,
            longitude=payload.longitude
        )

        adjusted_hour = lunar_data["solar"]["hour"]
        adjusted_minute = lunar_data["solar"]["minute"]

        # 2. 사주 계산
        saju_data = calculate_saju(
            lunar_data["lunar"]["year"],
            lunar_data["lunar"]["month"],
            lunar_data["lunar"]["day"],
            adjusted_hour,
            adjusted_minute
        )

        response_data = {
            "input": payload.dict(),
            "adjusted_time": {
                "year": lunar_data["solar"]["year"],
                "month": lunar_data["solar"]["month"],
                "day": lunar_data["solar"]["day"],
                "hour": adjusted_hour,
                "minute": adjusted_minute
            },
            "lunar": lunar_data["lunar"],
            "saju": saju_data["pillars"],
            "elements": saju_data["elements"],
            "analysis": None
        }

        # 3. LLM 분석 (옵션)
        if payload.include_analysis:
            full_saju_context = {"saju": saju_data}
            prompt = build_saju_prompt(full_saju_context)
            analysis_result = get_ai_analysis(prompt)
            response_data["analysis"] = analysis_result

        # 4. DB 저장 (NEW!)
        # 일주(Day Pillar) 영어 번역
        day_pillar_en = translate_pillar(saju_data["pillars"]["day"])

        new_record = models.SajuRecord(
            birth_date=payload.birth_date,
            birth_time=payload.birth_time,
            timezone=payload.timezone,
            longitude=payload.longitude,
            day_master=day_pillar_en,
            result_json=response_data  # 전체 결과를 JSON으로 저장
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)

        # 저장된 ID를 응답에 포함시켜주면 나중에 조회할 때 씀
        response_data["record_id"] = new_record.id

        return response_data

    except Exception as e:
        print(f"Error processing saju: {e}")
        raise HTTPException(status_code=500, detail=str(e))