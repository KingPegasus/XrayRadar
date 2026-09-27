import importlib.util
from datetime import datetime, timezone
from pathlib import Path
import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from xrayradar_server import models
from xrayradar_server.db import Base


def _load_migration_module():
    path = Path(__file__).parent.parent / "scripts" / "migrate_postgres_to_sqlite.py"
    spec = importlib.util.spec_from_file_location("migrate_postgres_to_sqlite", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migrate_copies_rows_between_sqlite_databases(tmp_path):
    source_path = tmp_path / "source.sqlite3"
    target_path = tmp_path / "target.sqlite3"
    source_engine = create_engine(f"sqlite:///{source_path}")
    target_engine = create_engine(f"sqlite:///{target_path}")

    Base.metadata.create_all(source_engine)
    event_id = uuid.uuid4()
    with Session(source_engine) as db:
        user = models.User(id=1, email="a@example.com", password_hash="x", plan="Free")
        db.add(user)
        db.flush()
        db.add(models.Project(id=1, name="P", owner_user_id=user.id))
        db.flush()
        db.add(models.Token(id=1, name="t", token="tok", user_id=user.id, is_admin=False))
        db.flush()
        db.add(models.TokenProjectAccess(id=1, token_id=1, project_id=1))
        db.add(
            models.Event(
                id=event_id,
                project_id=1,
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                level="error",
                message="boom",
                payload={"a": 1, "b": [1, 2, 3]},
            )
        )
        db.commit()

    migrate = _load_migration_module().migrate
    counts = migrate(f"sqlite:///{source_path}", f"sqlite:///{target_path}")

    assert counts["users"] == 1
    assert counts["projects"] == 1
    assert counts["tokens"] == 1
    assert counts["token_project_access"] == 1
    assert counts["events"] == 1

    with Session(target_engine) as db:
        assert db.scalar(select(models.User).where(models.User.id == 1)).email == "a@example.com"
        assert db.scalar(select(models.Project).where(models.Project.id == 1)).owner_user_id == 1
        event = db.scalar(select(models.Event).where(models.Event.id == event_id))
        assert event is not None
        assert event.payload == {"a": 1, "b": [1, 2, 3]}
        assert event.project_id == 1

    source_engine.dispose()
    target_engine.dispose()
