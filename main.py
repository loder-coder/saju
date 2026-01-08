from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse  # 추가됨
from pydantic import BaseModel, Field
from app.services.lunar_service import get_lunar_date
from app.services.saju_engine import calculate_saju

app = FastAPI()


class SajuRequest(BaseModel):
    birth_date: str = Field(..., description="YYYY-MM-DD format")
    birth_time: str = Field(..., description="HH:MM format")
    timezone: str = Field("Asia/Seoul", description="Timezone string e.g. 'America/New_York'")
    longitude: float = Field(127.0, description="Longitude for solar time correction")
    latitude: float = Field(37.5, description="Latitude (for future use)")


@app.get("/")
def health():
    # 원래 헬스체크만 하던 곳을 HTML 서빙으로 변경
    # 같은 경로에 있는 index.html 파일을 읽어서 리턴함
    return FileResponse("index.html")


@app.post("/saju")
def saju_calculate(payload: SajuRequest):
    try:
        year, month, day = map(int, payload.birth_date.split("-"))
        hour, minute = map(int, payload.birth_time.split(":"))

        # 1. Lunar Service 호출 (여기서 진태양시 보정 수행됨)
        lunar_data = get_lunar_date(
            year, month, day, hour, minute,
            timezone_str=payload.timezone,
            longitude=payload.longitude
        )

        # 2. 보정된 Solar 시간 기준의 Lunar 데이터를 사용하여 사주 계산
        # (주의: 시간 보정으로 인해 날짜가 바뀌었을 수도 있으므로 lunar_data의 solar 값을 참조할 수도 있으나,
        #  saju_engine은 음력 데이터를 기반으로 동작하므로 lunar 값을 넘김)

        # 보정된 시간(시/분)은 lunar_data['solar']에 들어있는 보정된 시간을 사용해야 시주(Time Pillar)가 정확함
        adjusted_hour = lunar_data["solar"]["hour"]
        adjusted_minute = lunar_data["solar"]["minute"]

        saju = calculate_saju(
            lunar_data["lunar"]["year"],
            lunar_data["lunar"]["month"],
            lunar_data["lunar"]["day"],
            adjusted_hour,
            adjusted_minute
        )

        return {
            "input": payload.dict(),
            "adjusted_time": {
                "year": lunar_data["solar"]["year"],
                "month": lunar_data["solar"]["month"],
                "day": lunar_data["solar"]["day"],
                "hour": adjusted_hour,
                "minute": adjusted_minute
            },
            "lunar": lunar_data["lunar"],
            "saju": saju
        }

    except Exception as e:
        # 로그 좀 찍어주면 디버깅 편함
        print(f"Error processing saju: {e}")
        raise HTTPException(status_code=500, detail=str(e))