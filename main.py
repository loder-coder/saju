import json
from fastapi import FastAPI, Request, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app import database, models
from app.services.lunar_service import get_lunar_date
from app.services.saju_engine import calculate_saju, get_fortune_by_period, get_dominant_element, ARCHETYPES, RHYTHM_KEYWORDS, RELATIONS, get_element
from app.services.prompt_builder import build_saju_prompt, translate_pillar
from app.services.llm_service import get_ai_analysis
from app.services.geo_service import geo_service
from pydantic import BaseModel
from typing import Optional
import redis
import os

app = FastAPI()


@app.on_event("startup")
def startup_event():
    db_url = str(database.engine.url).split('@')[-1]
    print(f"[DB] Connecting to: {db_url}")
    try:
        models.Base.metadata.create_all(bind=database.engine)
        inspector = inspect(database.engine)
        user_columns = {col["name"] for col in inspector.get_columns("users")} if inspector.has_table("users") else set()
        if "nickname" not in user_columns:
            with database.engine.begin() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN nickname VARCHAR"))
        print("[DB] Tables ready.")
    except Exception as e:
        print(f"[DB] Table creation failed: {e}")


limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

REDIS_URL = os.getenv("REDIS_URL")
r = redis.from_url(REDIS_URL) if REDIS_URL else None


class SajuRequest(BaseModel):
    birth_date: str
    birth_time: str
    timezone: str = "Asia/Seoul"
    longitude: float = 127.0
    latitude: float = 37.5
    include_analysis: bool = False
    theme: str = "general"
    user_id: Optional[str] = None
    birth_place: Optional[str] = None


class UserLogin(BaseModel):
    uid: str
    email: str
    provider: str = "google"
    nickname: Optional[str] = None


class FeedPostRequest(BaseModel):
    record_id: int
    caption: Optional[str] = None


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@app.post("/login")
def login_user(payload: UserLogin, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.uid == payload.uid).first()
    if not user:
        user = models.User(
            uid=payload.uid,
            email=payload.email,
            provider=payload.provider,
            nickname=payload.nickname,
        )
        db.add(user)
    else:
        user.email = payload.email
        user.provider = payload.provider
        if payload.nickname is not None:
            user.nickname = payload.nickname
    db.commit()
    db.refresh(user)
    return {"status": "ok", "uid": user.uid}


# ---------------------------------------------------------------------------
# Core: Saju calculate
# ---------------------------------------------------------------------------

@app.post("/saju")
@limiter.limit("60/minute")
def saju_calculate(request: Request, payload: SajuRequest, db: Session = Depends(database.get_db)):
    if payload.birth_place:
        geo_info = geo_service.get_location_info(payload.birth_place)
        if geo_info:
            payload.latitude = geo_info['latitude']
            payload.longitude = geo_info['longitude']
            payload.timezone = geo_info['timezone']

    lat_r = round(payload.latitude, 2)
    lon_r = round(payload.longitude, 2)
    cache_key = f"saju:{payload.birth_date}:{payload.birth_time}:{payload.timezone}:{lat_r}:{lon_r}:{payload.theme}"

    cached_payload = None
    if r:
        cached = r.get(cache_key)
        if cached:
            cached_payload = json.loads(cached)

    try:
        if cached_payload:
            res_data = cached_payload
        else:
            y, m, d = map(int, payload.birth_date.split("-"))
            h, mn = map(int, payload.birth_time.split(":"))

            lunar = get_lunar_date(y, m, d, h, mn, payload.timezone, payload.longitude)

            saju_res = calculate_saju(
                lunar["solar"]["year"],
                lunar["solar"]["month"],
                lunar["solar"]["day"],
                lunar["solar"]["hour"],
                lunar["solar"]["minute"]
            )

            dominant = get_dominant_element(saju_res["elements"])
            archetype = ARCHETYPES.get(dominant, "The Explorer")

            res_data = {
                "lunar": lunar["lunar"],
                "saju": saju_res["pillars"],
                "elements": saju_res["elements"],
                "dominant": dominant,
                "archetype": archetype,
            }

            if r:
                r.setex(cache_key, 3600, json.dumps(res_data))

        analysis_result = None
        if payload.include_analysis:
            prompt = build_saju_prompt(
                {"saju": {"pillars": res_data["saju"], "elements": res_data["elements"]}},
                theme=payload.theme,
            )
            if payload.birth_place:
                prompt += f"\n(Location context: {payload.birth_place}, {payload.timezone})"
            analysis_result = get_ai_analysis(prompt)

        response_data = dict(res_data)
        response_data["analysis"] = analysis_result

        new_record = models.SajuRecord(
            user_id=payload.user_id,
            birth_date=payload.birth_date,
            birth_time=payload.birth_time,
            timezone=payload.timezone,
            longitude=payload.longitude,
            day_master=translate_pillar(res_data["saju"]["day"]),
            result_json=response_data,
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        response_data["record_id"] = new_record.id

        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

@app.get("/history/{user_id}")
def get_history(user_id: str, db: Session = Depends(database.get_db)):
    records = (
        db.query(models.SajuRecord)
        .filter(models.SajuRecord.user_id == user_id)
        .order_by(models.SajuRecord.created_at.desc())
        .limit(10)
        .all()
    )
    return [{"record_id": rec.id, "created_at": rec.created_at.isoformat(), **rec.result_json} for rec in records]


# ---------------------------------------------------------------------------
# Fortune (period-based)
# ---------------------------------------------------------------------------

@app.get("/fortune/{period}/{record_id}")
def get_period_fortune(period: str, record_id: int, db: Session = Depends(database.get_db)):
    if period not in ("daily", "weekly", "monthly", "yearly", "life"):
        raise HTTPException(status_code=400, detail="period must be: daily, weekly, monthly, yearly, life")
    rec = db.query(models.SajuRecord).filter(models.SajuRecord.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Record not found")
    user_gan = rec.result_json["saju"]["day"][0]
    return get_fortune_by_period(user_gan, period)


# ---------------------------------------------------------------------------
# Feed
# ---------------------------------------------------------------------------

def _build_feed_item(post: models.FeedPost, rec: models.SajuRecord, db: Session) -> dict:
    rj = rec.result_json
    elements = rj.get("elements", {})
    dominant = rj.get("dominant") or get_dominant_element(elements)
    archetype = rj.get("archetype") or ARCHETYPES.get(dominant, "The Explorer")

    user_gan = rj["saju"]["day"][0]
    user_elm = get_element(user_gan)
    from datetime import datetime
    now = datetime.now()
    yearly_solar = __import__("lunar_python").Solar.fromYmd(now.year, 2, 4)
    yearly_eight = yearly_solar.getLunar().getEightChar()
    yearly_elm = get_element(yearly_eight.getYearGan())
    year_relation = RELATIONS.get((user_elm, yearly_elm), "Friend")
    rhythm = RHYTHM_KEYWORDS.get(year_relation, "Steady")

    display_name = archetype
    if rec.user_id:
        user = db.query(models.User).filter(models.User.uid == rec.user_id).first()
        if user and user.nickname:
            display_name = user.nickname

    return {
        "post_id": post.id,
        "record_id": post.record_id,
        "display_name": display_name,
        "archetype": archetype,
        "dominant": dominant,
        "rhythm": rhythm,
        "year_theme": f"{now.year} Pattern",
        "elements": elements,
        "caption": post.caption,
        "created_at": post.created_at.isoformat(),
    }


@app.get("/feed")
def list_feed(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(database.get_db),
):
    posts = (
        db.query(models.FeedPost)
        .order_by(models.FeedPost.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    result = []
    for post in posts:
        rec = db.query(models.SajuRecord).filter(models.SajuRecord.id == post.record_id).first()
        if rec:
            result.append(_build_feed_item(post, rec, db))
    return result


@app.post("/feed")
def create_feed_post(payload: FeedPostRequest, db: Session = Depends(database.get_db)):
    rec = db.query(models.SajuRecord).filter(models.SajuRecord.id == payload.record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Record not found")

    existing = db.query(models.FeedPost).filter(models.FeedPost.record_id == payload.record_id).first()
    if existing:
        existing.caption = payload.caption
        db.commit()
        db.refresh(existing)
        return {"status": "ok", "post_id": existing.id}

    post = models.FeedPost(record_id=payload.record_id, caption=payload.caption)
    db.add(post)
    db.commit()
    db.refresh(post)
    return {"status": "ok", "post_id": post.id}


@app.get("/feed/{post_id}")
def get_feed_post(post_id: int, db: Session = Depends(database.get_db)):
    post = db.query(models.FeedPost).filter(models.FeedPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    rec = db.query(models.SajuRecord).filter(models.SajuRecord.id == post.record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Record not found")
    return _build_feed_item(post, rec, db)


# ---------------------------------------------------------------------------
# PWA
# ---------------------------------------------------------------------------

@app.get("/manifest.json")
def get_manifest():
    return FileResponse("manifest.json")
