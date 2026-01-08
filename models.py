from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class SajuRecord(Base):
    __tablename__ = "saju_records"

    id = Column(Integer, primary_key=True, index=True)

    # 입력 정보
    birth_date = Column(String, index=True)  # YYYY-MM-DD
    birth_time = Column(String)  # HH:MM
    timezone = Column(String)
    longitude = Column(Float)

    # 핵심 결과 (검색용)
    day_master = Column(String)  # 일주 (예: Yang Earth Tiger)

    # 전체 결과 (JSON으로 통째로 저장)
    # Pillars, Elements, Analysis 등 다 때려박음
    result_json = Column(JSON)

    # 생성 시간
    created_at = Column(DateTime(timezone=True), server_default=func.now())