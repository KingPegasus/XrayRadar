import pytest

from xrayradar.config import Config, load_config


def test_config_from_env_defaults(monkeypatch):
    monkeypatch.delenv("XRAYRADAR_DSN", raising=False)
    monkeypatch.delenv("XRAYRADAR_DEBUG", raising=False)
    monkeypatch.delenv("XRAYRADAR_ENVIRONMENT", raising=False)
    monkeypatch.delenv("XRAYRADAR_RELEASE", raising=False)
    monkeypatch.delenv("XRAYRADAR_SERVER_NAME", raising=False)
    monkeypatch.delenv("XRAYRADAR_SAMPLE_RATE", raising=False)
    monkeypatch.delenv("XRAYRADAR_MAX_BREADCRUMBS", raising=False)
    monkeypatch.delenv("XRAYRADAR_TIMEOUT", raising=False)
    monkeypatch.delenv("XRAYRADAR_VERIFY_SSL", raising=False)
    monkeypatch.delenv("XRAYRADAR_MAX_PAYLOAD_SIZE", raising=False)

    cfg = Config.from_env()

    assert cfg.dsn is None
    assert cfg.debug is False
    assert cfg.environment == "development"
    assert cfg.release is None
    assert isinstance(cfg.server_name, str) and cfg.server_name
    assert cfg.sample_rate == 1.0
    assert cfg.max_breadcrumbs == 100
    assert cfg.timeout == 10.0
    assert cfg.verify_ssl is True
    assert cfg.max_payload_size == 100 * 1024


def test_config_parses_env_values(monkeypatch):
    monkeypatch.setenv("XRAYRADAR_DSN", "http://localhost:8001/1")
    monkeypatch.setenv("XRAYRADAR_DEBUG", "1")
    monkeypatch.setenv("XRAYRADAR_ENVIRONMENT", "prod")
    monkeypatch.setenv("XRAYRADAR_RELEASE", "v1")
    monkeypatch.setenv("XRAYRADAR_SERVER_NAME", "srv")
    monkeypatch.setenv("XRAYRADAR_SAMPLE_RATE", "0.25")
    monkeypatch.setenv("XRAYRADAR_MAX_BREADCRUMBS", "5")
    monkeypatch.setenv("XRAYRADAR_TIMEOUT", "2.5")
    monkeypatch.setenv("XRAYRADAR_VERIFY_SSL", "false")
    monkeypatch.setenv("XRAYRADAR_MAX_PAYLOAD_SIZE", "123")

    cfg = Config.from_env()

    assert cfg.dsn == "http://localhost:8001/1"
    assert cfg.debug is True
    assert cfg.environment == "prod"
    assert cfg.release == "v1"
    assert cfg.server_name == "srv"
    assert cfg.sample_rate == 0.25
    assert cfg.max_breadcrumbs == 5
    assert cfg.timeout == 2.5
    assert cfg.verify_ssl is False
    assert cfg.max_payload_size == 123


def test_config_validation_sample_rate(monkeypatch):
    monkeypatch.setenv("XRAYRADAR_SAMPLE_RATE", "2.0")
    with pytest.raises(ValueError):
        Config.from_env()


def test_load_config_variants(monkeypatch, tmp_path):
    monkeypatch.delenv("XRAYRADAR_ENVIRONMENT", raising=False)

    cfg = load_config({"environment": "staging"})
    assert cfg.environment == "staging"

    cfg2 = load_config(cfg)
    assert cfg2 is cfg

    p = tmp_path / "cfg.json"
    p.write_text('{"environment": "qa", "timeout": 1.0}')
    cfg3 = load_config(str(p))
    assert cfg3.environment == "qa"
    assert cfg3.timeout == 1.0

    with pytest.raises(TypeError):
        load_config(123)
