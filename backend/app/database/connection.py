import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Supabase PostgreSQL database URL with URL-encoded password (Mokshitha@007 -> Mokshitha%40007)
DEFAULT_DB_URL = "postgresql://postgres:Mokshitha%40007@db.cqvgsibjkkgympkchtko.supabase.co:5432/postgres"

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)