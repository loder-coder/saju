from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from app.database import Base


class SajuRecord(Base):
    __tablename__ = "saju_records"

    id = Column(Integer, primary_key=True, index=True)
    # Firebase UID 저장 (유저와 기록 연결)
    user_id = Column(String, index=True, nullable=True)

    birth_date = Column(String, index=True)
    birth_time = Column(String)
    timezone = Column(String)
    longitude = Column(Float)
    day_master = Column(String)
    result_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # 구글 로그인 시 넘어오는 고유 UID (이게 식별자임)
    uid = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    provider = Column(String)  # google
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())