import json

import pytest

from xrayradar.config import Config, load_config


def test_load_config_accepts_config_instance():
    cfg = Config(dsn="http://x/1")
    assert load_config(cfg) is cfg


def test_load_config_accepts_dict():
    cfg = load_config({"dsn": "http://x/1", "timeout": 2.0})
    assert isinstance(cfg, Config)
    assert cfg.dsn == "http://x/1"
    assert cfg.timeout == 2.0


def test_load_config_rejects_unsupported_type():
    with pytest.raises(TypeError):
        load_config(123)  # type: ignore[arg-type]


def test_load_config_from_file_json(tmp_path):
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps({"dsn": "http://x/1", "timeout": 3.5}))
    cfg = load_config(str(p))
    assert cfg.dsn == "http://x/1"
    assert cfg.timeout == 3.5


def test_load_config_from_file_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(str(tmp_path / "missing.json"))


def test_load_config_from_file_unsupported_ext_raises(tmp_path):
    p = tmp_path / "cfg.txt"
    p.write_text("dsn: http://x/1")
    with pytest.raises(ValueError):
        load_config(str(p))


def test_config_default_server_name_fallback(monkeypatch):
    # Force socket.gethostname() to raise so we hit the fallback.
    import socket

    monkeypatch.setattr(socket, "gethostname", lambda: (
        _ for _ in ()).throw(RuntimeError("x")))
    cfg = Config(dsn="http://x/1")
    assert cfg.server_name in ("unknown", cfg.server_name)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"sample_rate": -0.1},
        {"sample_rate": 1.1},
        {"max_breadcrumbs": -1},
        {"timeout": 0},
        {"max_payload_size": 0},
    ],
)
def test_config_validation_errors(kwargs):
    base = {"dsn": "http://x/1"}
    base.update(kwargs)
    with pytest.raises(ValueError):
        Config(**base)
