import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    url = os.getenv("XRAYRADAR_DATABASE_URL")
    if not url:
        raise RuntimeError("XRAYRADAR_DATABASE_URL is not set")
    return url


_engine = None
_SessionLocal = None
_engine_url = None


def _ensure_engine():
    """Ensure database engine is initialized (lazy initialization)"""
    global _engine, _SessionLocal, _engine_url
    _db_url = get_database_url()
    # Recreate engine if URL changed (for tests that change the env var)
    if _engine is None or _engine_url != _db_url:
        if _engine is not None:
            _engine.dispose()
        _engine_url = _db_url
        _connect_args = {}
        if _db_url.startswith("sqlite:"):
            _connect_args["check_same_thread"] = False
        _engine = create_engine(_db_url, pool_pre_ping=True, connect_args=_connect_args)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def _ensure_session_local():
    """Ensure session maker is initialized"""
    if _SessionLocal is None:
        _ensure_engine()
    return _SessionLocal


# Use __getattr__ for lazy initialization of module-level attributes
# This allows imports to succeed even if XRAYRADAR_DATABASE_URL is not set
# The engine will be created on first access
def __getattr__(name: str):
    if name == "engine":
        return _ensure_engine()
    if name == "SessionLocal":
        return _ensure_session_local()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=_ensure_engine())


def get_db():
    db = _ensure_session_local()()
    try:
        yield db
    finally:
        db.close()
