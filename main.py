from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.services.lunar_service import get_lunar_date
from app.services.saju_engine import calculate_saju

app = FastAPI()


class SajuRequest(BaseModel):
    birth_date: str
    birth_time: str


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/saju")
def saju_calculate(payload: SajuRequest):
    try:
        year, month, day = map(int, payload.birth_date.split("-"))
        hour, minute = map(int, payload.birth_time.split(":"))

        lunar = get_lunar_date(year, month, day)

        saju = calculate_saju(
            lunar["lunar"]["year"],
            lunar["lunar"]["month"],
            lunar["lunar"]["day"],
            hour,
            minute
        )

        return {
            "input": payload.dict(),
            "lunar": lunar,
            "saju": saju
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
