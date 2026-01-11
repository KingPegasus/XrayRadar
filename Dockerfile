FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY src /app/src

RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir .

EXPOSE 8000

CMD ["sh", "-c", "python -m uvicorn xrayradar_server.main:app --host 0.0.0.0 --port ${PORT:-8000} --app-dir src"]
