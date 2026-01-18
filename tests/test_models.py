import uuid

from sqlalchemy.dialects import postgresql, sqlite


def test_guid_load_dialect_impl_postgres_branch(database_url):
    from xrayradar_server.models import GUID

    guid = GUID()
    dialect = postgresql.dialect()
    impl = guid.load_dialect_impl(dialect)
    assert impl.as_uuid is True


def test_guid_process_bind_param_branches(database_url):
    from xrayradar_server.models import GUID

    guid = GUID()

    # None branch
    assert guid.process_bind_param(None, sqlite.dialect()) is None

    # postgres branch
    u = uuid.uuid4()
    assert guid.process_bind_param(u, postgresql.dialect()) == u

    # sqlite: non-uuid value coerces via uuid.UUID(str(value))
    u_str = str(uuid.uuid4())
    assert guid.process_bind_param(u_str, sqlite.dialect()) == u_str


def test_guid_process_result_value_branches(database_url):
    from xrayradar_server.models import GUID

    guid = GUID()

    # None branch
    assert guid.process_result_value(None, sqlite.dialect()) is None

    # already uuid.UUID branch
    u = uuid.uuid4()
    assert guid.process_result_value(u, sqlite.dialect()) == u

    # string -> uuid.UUID branch
    u_str = str(uuid.uuid4())
    assert guid.process_result_value(
        u_str, sqlite.dialect()) == uuid.UUID(u_str)
