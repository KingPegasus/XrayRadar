import os

import pytest


def _load_env_file(path: str) -> None:
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        return


@pytest.fixture(scope="session")
def database_url() -> str:
    if not os.getenv("XRAYRADAR_DATABASE_URL"):
        _load_env_file(os.path.join(os.getcwd(), ".env"))
    url = os.getenv("XRAYRADAR_DATABASE_URL")
    if not url:
        pytest.skip("XRAYRADAR_DATABASE_URL is not set")
    return url
