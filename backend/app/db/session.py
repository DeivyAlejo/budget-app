from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def normalize_database_url(raw_url: str) -> str:
    url = raw_url.strip()

    # Render and other platforms sometimes provide postgres:// URLs.
    if url.startswith('postgres://'):
        return url.replace('postgres://', 'postgresql+psycopg://', 1)

    # Prefer psycopg (v3) explicitly for PostgreSQL connections.
    if url.startswith('postgresql://'):
        return url.replace('postgresql://', 'postgresql+psycopg://', 1)

    return url


database_url = normalize_database_url(settings.database_url)
is_sqlite = database_url.startswith('sqlite')

engine = create_engine(
    database_url,
    connect_args={'check_same_thread': False} if is_sqlite else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
