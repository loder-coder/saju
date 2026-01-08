from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from database import Base


class SajuRecord(Base):
    __tablename__ = "saju_records"

    id = Column(Integer, primary_key=True, index=True)
    birth_date = Column(String, index=True)
    birth_time = Column(String)
    timezone = Column(String)
    longitude = Column(Float)
    day_master = Column(String)
    result_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# [NEW] 소셜 로그인 유저 관리용
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)  # 구글 이메일
    provider = Column(String)  # google, apple
    is_premium = Column(Boolean, default=False)  # 결제 여부
    created_at = Column(DateTime(timezone=True), server_default=func.now())