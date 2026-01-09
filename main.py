import json
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# 파일 구조에 따라 임포트 경로 자동 조절
try:
    from app import database, models
except ImportError:
    import database, models

from pydantic import BaseModel
from typing import Optional
import redis
import os

# 서비스 레이어 임포트
try:
    from app.services.lunar_service import get_lunar_date
    from app.services.saju_engine import calculate_saju, get_fortune_by_period
    from app.services.prompt_builder import build_saju_prompt, translate_pillar
    from app.services.llm_service import get_ai_analysis
    from app.services.geo_service import geo_service  # [NEW] GeoService 추가
except ImportError:
    from services.lunar_service import get_lunar_date
    from services.saju_engine import calculate_saju, get_fortune_by_period
    from services.prompt_builder import build_saju_prompt, translate_pillar
    from services.llm_service import get_ai_analysis
    from services.geo_service import geo_service  # [NEW] GeoService 추가

app = FastAPI()


# [중요] 서버 시작 시 실행될 로직
@app.on_event("startup")
def startup_event():
    print("🚀 [STARTUP] Checking Database Connection...")
    # 현재 연결된 DB 주소 출력 (비밀번호 제외)
    db_url = str(database.engine.url).split('@')[-1]
    print(f"📡 [DB-INFO] Connecting to: {db_url}")

    try:
        # 테이블 생성 강제 실행
        models.Base.metadata.create_all(bind=database.engine)
        print("✅ [DB-INFO] Database tables checked/created successfully.")
    except Exception as e:
        print(f"❌ [DB-ERROR] Failed to create tables: {e}")


limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Redis 설정
REDIS_URL = os.getenv("REDIS_URL")
r = redis.from_url(REDIS_URL) if REDIS_URL else None


# --- API 로직 ---

class SajuRequest(BaseModel):
    birth_date: str
    birth_time: str
    timezone: str = "Asia/Seoul"
    longitude: float = 127.0
    latitude: float = 37.5
    include_analysis: bool = False
    theme: str = "general"
    user_id: Optional[str] = None
    birth_place: Optional[str] = None  # [NEW] 도시 이름 입력 필드 추가


class UserLogin(BaseModel):
    uid: str
    email: str
    provider: str = "google"


@app.post("/login")
def login_user(payload: UserLogin, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.uid == payload.uid).first()
    if not user:
        user = models.User(uid=payload.uid, email=payload.email, provider=payload.provider)
        db.add(user)
    else:
        user.email = payload.email
    db.commit()
    db.refresh(user)
    return {"status": "ok", "uid": user.uid}


@app.post("/saju")
@limiter.limit("15/minute")
def saju_calculate(request: Request, payload: SajuRequest, db: Session = Depends(database.get_db)):
    # [NEW] 1. 지리 정보 보정 로직
    # birth_place(예: "Nanterre")가 들어오면 좌표/타임존을 조회해서 payload를 갱신함
    if payload.birth_place:
        geo_info = geo_service.get_location_info(payload.birth_place)
        if geo_info:
            print(f"📍 [Geo] Fixed: {payload.birth_place} -> {geo_info['address']} ({geo_info['timezone']})")
            payload.latitude = geo_info['latitude']
            payload.longitude = geo_info['longitude']
            payload.timezone = geo_info['timezone']
        else:
            print(f"⚠️ [Geo] Failed to find '{payload.birth_place}'. Using provided defaults.")

    # [NEW] 캐시 키에 위도/경도 포함 (위치가 다르면 결과도 달라져야 함)
    # 소수점 약간의 차이는 무시하기 위해 round 처리할 수도 있지만, 여기선 그대로 사용
    cache_key = f"cache:{payload.birth_date}:{payload.birth_time}:{payload.latitude}:{payload.longitude}:{payload.theme}:{payload.user_id}"

    if r:
        cached = r.get(cache_key)
        if cached: return json.loads(cached)

    try:
        y, m, d = map(int, payload.birth_date.split("-"))
        h, mn = map(int, payload.birth_time.split(":"))

        # 2. 갱신된 좌표/타임존으로 만세력 계산
        lunar = get_lunar_date(y, m, d, h, mn, payload.timezone, payload.longitude)

        saju_res = calculate_saju(
            lunar["solar"]["year"],
            lunar["solar"]["month"],
            lunar["solar"]["day"],
            lunar["solar"]["hour"],
            lunar["solar"]["minute"]
        )

        analysis_result = None
        if payload.include_analysis:
            # 프롬프트 빌더에 지리 정보 컨텍스트를 넘겨줄 수 있다면 여기서 추가 가능
            # 현재는 사주 결과 기반 해석
            prompt = build_saju_prompt({"saju": saju_res}, theme=payload.theme)

            # [Tip] 만약 LLM에게 "여기는 프랑스다"라고 알려주고 싶다면 prompt에 문자열을 추가하면 됨
            if payload.birth_place:
                prompt += f"\n(참고: 사용자의 출생지는 {payload.birth_place}, 시간대는 {payload.timezone}입니다.)"

            analysis_result = get_ai_analysis(prompt)

        res_data = {"input": payload.dict(), "lunar": lunar["lunar"], "saju": saju_res["pillars"],
                    "elements": saju_res["elements"], "analysis": analysis_result}

        # DB 저장
        new_record = models.SajuRecord(
            user_id=payload.user_id,
            birth_date=payload.birth_date,
            birth_time=payload.birth_time,
            timezone=payload.timezone,
            longitude=payload.longitude,
            day_master=translate_pillar(saju_res["pillars"]["day"]),
            result_json=res_data
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        res_data["record_id"] = new_record.id

        if r: r.setex(cache_key, 3600, json.dumps(res_data))
        return res_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{user_id}")
def get_history(user_id: str, db: Session = Depends(database.get_db)):
    records = db.query(models.SajuRecord).filter(models.SajuRecord.user_id == user_id).order_by(
        models.SajuRecord.created_at.desc()).limit(10).all()
    return [{"record_id": rec.id, "created_at": rec.created_at.isoformat(), **rec.result_json} for rec in records]


@app.get("/fortune/{period}/{record_id}")
def get_period_fortune(period: str, record_id: int, db: Session = Depends(database.get_db)):
    rec = db.query(models.SajuRecord).filter(models.SajuRecord.id == record_id).first()
    if not rec: raise HTTPException(status_code=404, detail="Not found")
    user_gan = rec.result_json["saju"]["day"][0]
    return get_fortune_by_period(user_gan, period)


@app.get("/manifest.json")
def get_manifest(): return FileResponse("manifest.json")