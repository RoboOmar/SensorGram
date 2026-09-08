from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.config import settings

connect_args = {"check_same_thread": False, "timeout": 15} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_size=50,
    max_overflow=50,
    pool_pre_ping=True
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables on startup and apply missing schema migrations."""
    from backend.models import robot, post, like, comment, comment_like  # noqa: F401
    Base.metadata.create_all(bind=engine)

    from sqlalchemy import text
    try:
        with engine.begin() as conn:
            # Safely attempt to add the parent_comment_id column if it doesn't exist
            conn.execute(text("ALTER TABLE comments ADD COLUMN IF NOT EXISTS parent_comment_id INTEGER REFERENCES comments(id)"))
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Could not apply column migration (it may already exist): {e}")
