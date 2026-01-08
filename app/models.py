from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class SajuRecord(Base):
    __tablename__ = "saju_records"

    id = Column(Integer, primary_key=True, index=True)

    # [수정] 소셜 로그인 유저와 연결 (어떤 유저의 기록인지 저장)
    user_id = Column(String, index=True, nullable=True)

    # 입력 정보
    birth_date = Column(String, index=True)  # YYYY-MM-DD
    birth_time = Column(String)  # HH:MM
    timezone = Column(String)
    longitude = Column(Float)

    # 핵심 결과
    day_master = Column(String)

    # 결과 JSON (Pillars, Elements, Analysis 등)
    result_json = Column(JSON)

    # 생성 시간
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # [수정] Firebase나 Google에서 주는 고유 UID 저장용
    uid = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    provider = Column(String)  # google, apple 등
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())