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
    _run_migrations()


def _run_migrations():
    """Idempotent ALTER TABLE migrations for columns added after initial deploy."""
    is_sqlite = DATABASE_URL.startswith("sqlite")
    migrations = []

    if is_sqlite:
        # SQLite does not support IF NOT EXISTS for columns; check pragma instead.
        with engine.connect() as conn:
            from sqlalchemy import text
            cols = {row[1] for row in conn.execute(text("PRAGMA table_info(users)"))}
            if "failed_login_attempts" not in cols:
                migrations.append(
                    "ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0"
                )
            if "locked_until" not in cols:
                migrations.append(
                    "ALTER TABLE users ADD COLUMN locked_until TIMESTAMP"
                )
    else:
        # PostgreSQL supports DO $$ … END $$ for conditional DDL
        migrations = [
            """
            DO $$ BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='users' AND column_name='failed_login_attempts'
              ) THEN
                ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0;
              END IF;
            END $$;
            """,
            """
            DO $$ BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='users' AND column_name='locked_until'
              ) THEN
                ALTER TABLE users ADD COLUMN locked_until TIMESTAMP;
              END IF;
            END $$;
            """,
            """
            DO $$ BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name='api_keys'
              ) THEN
                CREATE TABLE api_keys (
                  id SERIAL PRIMARY KEY,
                  organization_id INTEGER NOT NULL REFERENCES organizations(id),
                  name VARCHAR(255) NOT NULL,
                  key_hash VARCHAR(64) NOT NULL UNIQUE,
                  key_prefix VARCHAR(16) NOT NULL,
                  revoked BOOLEAN NOT NULL DEFAULT FALSE,
                  created_at TIMESTAMP DEFAULT NOW(),
                  last_used_at TIMESTAMP
                );
                CREATE INDEX ix_api_keys_organization_id ON api_keys(organization_id);
                CREATE INDEX ix_api_keys_key_hash ON api_keys(key_hash);
                CREATE INDEX ix_api_keys_revoked ON api_keys(revoked);
              END IF;
            END $$;
            """,
        ]

    if migrations:
        from sqlalchemy import text
        with engine.begin() as conn:
            for stmt in migrations:
                try:
                    conn.execute(text(stmt))
                except Exception:
                    pass  # already applied or harmless
