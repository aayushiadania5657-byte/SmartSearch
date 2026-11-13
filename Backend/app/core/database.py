
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import BACKEND_DIR, settings


# Preserve the existing database directory and default path.
BASE_DIR = BACKEND_DIR
DATABASE_PATH = BASE_DIR / "smartsearch.db"

# Read the database URL from application settings.
DATABASE_URL = settings.database_url

database_url = make_url(DATABASE_URL)

# Configure SQLite separately from other database engines.
engine_options = {}

if database_url.get_backend_name() == "sqlite":
    engine_options["connect_args"] = {
        "check_same_thread": False
    }

    # Create the parent directory for file-based SQLite databases.
    database_name = database_url.database

    if database_name and database_name not in (":memory:",):
        if not database_url.query.get("mode") == "memory":
            Path(database_name).parent.mkdir(
                parents=True,
                exist_ok=True,
            )


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    **engine_options,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
