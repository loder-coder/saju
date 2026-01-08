from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from database import Base  # 여기 수정됨 (app. 제거)


class SajuRecord(Base):
    __tablename__ = "saju_records"

    id = Column(Integer, primary_key=True, index=True)

    # 입력 정보
    birth_date = Column(String, index=True)
    birth_time = Column(String)
    timezone = Column(String)
    longitude = Column(Float)

    # 핵심 결과
    day_master = Column(String)

    # 전체 결과
    result_json = Column(JSON)

    # 생성 시간
    created_at = Column(DateTime(timezone=True), server_default=func.now())