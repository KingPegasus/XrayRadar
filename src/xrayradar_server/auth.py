from datetime import datetime
import hashlib
import hmac
import os
import secrets

from fastapi import HTTPException, Request
from itsdangerous import BadSignature, URLSafeSerializer


def _is_production() -> bool:
    return (os.getenv("XRAYRADAR_ENV") or "").strip().lower() == "production"


def _cookie_secure() -> bool:
    raw = (os.getenv("XRAYRADAR_COOKIE_SECURE") or "").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    return _is_production()


def _get_session_serializer() -> URLSafeSerializer:
    secret = (os.getenv("XRAYRADAR_SESSION_SECRET") or "").strip()
    if not secret:
        raise RuntimeError("XRAYRADAR_SESSION_SECRET is not set")
    return URLSafeSerializer(secret_key=secret, salt="xrayradar-session")


def _parse_admin_allowlist() -> set[str]:
    raw = (os.getenv("XRAYRADAR_ADMIN_EMAILS") or "").strip()
    if not raw:
        return set()
    return {x.strip().lower() for x in raw.split(",") if x.strip()}


def _get_session_email(request: Request) -> str | None:
    cookie = (request.cookies.get("xrayradar_session") or "").strip()
    if not cookie:
        return None
    s = _get_session_serializer()
    try:
        payload = s.loads(cookie)
    except BadSignature:
        return None
    email = (payload.get("email") if isinstance(payload, dict) else None) or ""
    email = email.strip().lower()
    return email or None


def _get_user_session_email(request: Request) -> str | None:
    cookie = (request.cookies.get("xrayradar_user_session") or "").strip()
    if not cookie:
        return None
    s = _get_session_serializer()
    try:
        payload = s.loads(cookie)
    except BadSignature:
        return None
    email = (payload.get("email") if isinstance(payload, dict) else None) or ""
    email = email.strip().lower()
    return email or None


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    rounds = 210_000
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        rounds,
    )
    return f"pbkdf2_sha256${rounds}${salt}${dk.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds_raw, salt, digest_hex = stored.split("$", 3)
    except ValueError:
        return False
    if algo != "pbkdf2_sha256":
        return False
    try:
        rounds = int(rounds_raw)
    except ValueError:
        return False
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        rounds,
    )
    return hmac.compare_digest(dk.hex(), digest_hex)


def _unauthorized(detail: str = "Unauthorized") -> HTTPException:
    return HTTPException(status_code=401, detail=detail)


def _forbidden(detail: str = "Forbidden") -> HTTPException:
    return HTTPException(status_code=403, detail=detail)


def _session_payload_for_email(email: str) -> dict:
    return {"email": email, "ts": int(datetime.now().timestamp())}
