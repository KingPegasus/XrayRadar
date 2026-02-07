"""API utilities for admin UI."""

API_JS = """async function api(path, opts={}) {
  const r = await fetch(path, Object.assign({ credentials: 'same-origin' }, opts));
  const text = await r.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch (e) { data = text; }
  if (!r.ok) {
    const detail = (data && data.detail) ? data.detail : (typeof data === 'string' ? data : r.statusText);
    throw new Error(`HTTP ${r.status}: ${detail}`);
  }
  return data;
}"""
