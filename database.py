import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Railway에서 자동으로 넣어주는 환경변수 가져오기
DATABASE_URL = os.getenv("DATABASE_URL")

# 로컬 테스트용 (DB 없을 때 에러 방지용 SQLite)
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./test.db"
    print("WARNING: No DATABASE_URL found. Using SQLite for testing.")
else:
    # SQLAlchemy는 'postgres://' 대신 'postgresql://'을 원함 (Railway 호환성 수정)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency Injection (API 요청마다 DB 세션 열고 닫기)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()