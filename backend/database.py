"""Database setup and session. Supports SQLite (dev) and Postgres (prod via DATABASE_URL)."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ops_monitor.db")

# Vercel/Prisma gir ofte URLer på formen postgres://... – SQLAlchemy 2.x
# forventer postgresql+psycopg:// når vi bruker psycopg (v3-driver).
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from backend import models_db  # noqa: F401
    Base.metadata.create_all(bind=engine)
