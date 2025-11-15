from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.config import get_settings
from app.models import Base
from typing import Generator
from contextlib import contextmanager

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Создаём таблицы и pgvector extension"""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Контекстный менеджер для использования в коде (with get_db() as db)
    И dependency для FastAPI (db: Session = Depends(get_db))
    
    FastAPI автоматически понимает контекстные менеджеры!
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()