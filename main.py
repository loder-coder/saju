from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from app.services.lunar_service import get_lunar_date
from app.services.saju_engine import calculate_saju
from app.services.prompt_builder import build_saju_prompt
from app.services.llm_service import get_ai_analysis
import os
from dotenv import load_dotenv

# .env 로드 (로컬 개발용)
load_dotenv()

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
def saju_calculate(payload: SajuRequest):
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
            # 프롬프트 생성
            full_saju_context = {"saju": saju_data}
            prompt = build_saju_prompt(full_saju_context)

            # LLM 호출
            analysis_result = get_ai_analysis(prompt)
            response_data["analysis"] = analysis_result

        return response_data

    except Exception as e:
        print(f"Error processing saju: {e}")
        raise HTTPException(status_code=500, detail=str(e))