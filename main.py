from fastapi import FastAPI, HTTPException, Query
from app.services.lunar_service import get_lunar_date
from app.services.saju_engine import calculate_saju

app = FastAPI()


@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/saju")
def saju_calculate(
    birth_date: str = Query(..., example="1993-07-21"),
    birth_time: str = Query(..., example="14:30")
):
    try:
        year, month, day = map(int, birth_date.split("-"))
        hour, minute = map(int, birth_time.split(":"))

        # 1. 양력 → 음력
        lunar = get_lunar_date(year, month, day)

        lunar_year = lunar["lunar"]["year"]
        lunar_month = lunar["lunar"]["month"]
        lunar_day = lunar["lunar"]["day"]

        # 2. 사주 계산
        saju = calculate_saju(
            lunar_year,
            lunar_month,
            lunar_day,
            hour,
            minute
        )

        return {
            "input": {
                "birth_date": birth_date,
                "birth_time": birth_time
            },
            "lunar": lunar,
            "saju": saju
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
