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


_db_url = get_database_url()
_connect_args = {}
if _db_url.startswith("sqlite:"):
    _connect_args["check_same_thread"] = False

engine = create_engine(_db_url, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
