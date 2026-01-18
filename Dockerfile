FROM node:20-slim AS web-build

WORKDIR /web

COPY xrayradar-web/package.json xrayradar-web/package-lock.json /web/
RUN npm ci

COPY xrayradar-web /web
RUN npm run build


FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md alembic.ini /app/
COPY alembic /app/alembic
COPY src /app/src
COPY --from=web-build /web/dist /app/xrayradar-web/dist

ENV XRAYRADAR_WEB_DIST=/app/xrayradar-web/dist

RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir .

RUN useradd -m -u 10001 app \
    && chown -R app:app /app

EXPOSE 8000

USER app

CMD ["sh","-c","alembic -c alembic.ini upgrade head && uvicorn --proxy-headers --forwarded-allow-ips='*' --app-dir src xrayradar_server.main:app --host 0.0.0.0 --port ${PORT:-8000}"]