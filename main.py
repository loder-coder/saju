import os
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

# 내부 모듈
from app import models, database
from app.services.lunar_service import get_lunar_date
from app.services.saju_engine import calculate_saju, get_fortune_by_period
from app.services.prompt_builder import build_saju_prompt, translate_pillar
from app.services.llm_service import get_ai_analysis

load_dotenv()
models.Base.metadata.create_all(bind=database.engine)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if not os.path.exists("static"): os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class SajuRequest(BaseModel):
    birth_date: str
    birth_time: str
    timezone: str
    longitude: float
    latitude: float
    include_analysis: bool
    theme: str


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/saju")
@limiter.limit("10/minute")
def saju_calculate(request: Request, payload: SajuRequest, db: Session = Depends(database.get_db)):
    try:
        y, m, d = map(int, payload.birth_date.split("-"))
        h, mn = map(int, payload.birth_time.split(":"))

        lunar = get_lunar_date(y, m, d, h, mn, payload.timezone, payload.longitude)
        # lunar_data 구조에 맞춰 시간 보정값 사용
        adj_h = lunar["solar"]["hour"]
        adj_m = lunar["solar"]["minute"]

        saju = calculate_saju(lunar["lunar"]["year"], lunar["lunar"]["month"], lunar["lunar"]["day"], adj_h, adj_m)

        res_data = {
            "input": payload.dict(),
            "lunar": lunar["lunar"],
            "saju": saju["pillars"],
            "elements": saju["elements"],
            "analysis": None
        }

        if payload.include_analysis:
            full_context = {"saju": saju}
            prompt = build_saju_prompt(full_context, theme=payload.theme)
            res_data["analysis"] = get_ai_analysis(prompt)

        day_pillar = translate_pillar(saju["pillars"]["day"])
        new_record = models.SajuRecord(
            birth_date=payload.birth_date, birth_time=payload.birth_time, timezone=payload.timezone,
            longitude=payload.longitude, day_master=day_pillar, result_json=res_data
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        res_data["record_id"] = new_record.id
        return res_data
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/saju/{record_id}")
def get_record(record_id: int, db: Session = Depends(database.get_db)):
    rec = db.query(models.SajuRecord).filter(models.SajuRecord.id == record_id).first()
    if not rec: raise HTTPException(status_code=404, detail="Not found")
    return rec.result_json


# [NEW] 기간별 운세 통합 API
@app.get("/fortune/{period}/{record_id}")
def get_period_fortune(period: str, record_id: int, db: Session = Depends(database.get_db)):
    rec = db.query(models.SajuRecord).filter(models.SajuRecord.id == record_id).first()
    if not rec: raise HTTPException(status_code=404, detail="Not found")

    try:
        user_gan = rec.result_json["saju"]["day"][0]
        # saju_engine의 함수 호출
        fortune = get_fortune_by_period(user_gan, period)
        return fortune
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/manifest.json")
def get_manifest():
    return FileResponse("manifest.json")