"""
Database configuration and session management
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models.research import Base

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DATABASE_PATH = os.path.join(DATA_DIR, "research.db")
DEFAULT_SQLITE_URL = f"sqlite:///{DATABASE_PATH}"

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)

db_password = os.getenv("DB_PASSWORD")
if db_password and "PLACEHOLDER" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("PLACEHOLDER", db_password)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}  # Needed for SQLite

engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database (create all tables)"""
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at: {DATABASE_PATH}")


def get_db() -> Session:
    """
    Get a database session
    
    Usage:
        with get_db() as db:
            pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Get a database session (for non-FastAPI usage)
    
    Usage:
        db = get_db_session()
        db.close()
    """
    return SessionLocal()


if DATABASE_URL.startswith("sqlite"):
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATABASE_PATH):
        print(f"Creating new database at: {DATABASE_PATH}")
        init_db()
    else:
        print(f"Database exists at: {DATABASE_PATH}")
