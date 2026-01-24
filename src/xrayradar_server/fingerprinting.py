from __future__ import annotations

import hashlib
from typing import Any


def compute_fingerprint(event: dict[str, Any]) -> str:
    """
    Compute a stable grouping key for an event.

    This is a simplified fingerprinting approach:
    - If the SDK provided a `fingerprint` list, use it.
    - Else use exception type + value/message + first frame (if available).

    Returns a 64-character hex string (full sha256) suitable for indexing.
    """
    fp = event.get("fingerprint")
    if isinstance(fp, list) and fp:
        parts = [str(x) for x in fp if x is not None]
        raw = "|".join(parts).strip()
        if raw:
            return _hash(raw)

    exc = event.get("exception")
    exc_type = ""
    exc_value = ""
    frame_sig = ""

    if isinstance(exc, dict):
        values = exc.get("values")
        if isinstance(values, list) and values:
            v0 = values[0] if isinstance(values[0], dict) else {}
            exc_type = str(v0.get("type") or "")
            exc_value = str(v0.get("value") or "")
            st = v0.get("stacktrace")
            if isinstance(st, dict):
                frames = st.get("frames")
                if isinstance(frames, list) and frames:
                    # Prefer first in-app-ish frame if present; else first frame.
                    chosen = None
                    for fr in frames:
                        if isinstance(fr, dict) and fr.get("in_app") is True:
                            chosen = fr
                            break
                    if chosen is None:
                        chosen = frames[0] if isinstance(frames[0], dict) else None
                    if isinstance(chosen, dict):
                        frame_sig = "|".join(
                            [
                                str(chosen.get("filename") or ""),
                                str(chosen.get("function") or ""),
                                str(chosen.get("lineno") or ""),
                            ]
                        )

    msg = str(event.get("message") or "")
    base = "|".join([exc_type, exc_value or msg, frame_sig]).strip("|").strip()
    if not base:
        base = msg or "unknown"
    return _hash(base)


def _hash(raw: str) -> str:
    """Hash a string for fingerprinting (non-cryptographic use)."""
    # Use SHA256 instead of SHA1 for better security posture
    # This is for error grouping, not security, but SHA1 is deprecated
    # Return full 64-character SHA256 hash for maximum collision resistance
    # Database column is VARCHAR(64), so this uses the full capacity
    return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()

