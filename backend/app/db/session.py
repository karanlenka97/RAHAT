"""Database session management, connection pooling, and PostGIS verification."""
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.models.base import Base


def get_database_url() -> str:
    """Build or retrieve database URL."""
    if settings.DATABASE_URL:
        return settings.DATABASE_URL
    return (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
        f"{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )


# Engine configuration
database_url = get_database_url()
connect_args = {}
if database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding transactional database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_postgis_available(db: Session) -> bool:
    """Verify if PostGIS extension is installed and available in the active database."""
    try:
        result = db.execute(text("SELECT PostGIS_Version();")).scalar()
        return bool(result)
    except Exception:
        return False
