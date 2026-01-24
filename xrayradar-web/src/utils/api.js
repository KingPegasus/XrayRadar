export async function readErrorMessage(resp) {
  try {
    const data = await resp.json()
    if (data && typeof data.detail === 'string' && data.detail.trim()) return data.detail
  } catch {
    // ignore
  }
  return `Request failed (${resp.status})`
}

export async function fetchMe() {
  try {
    const resp = await fetch('/api/me', { credentials: 'include' })
    if (!resp.ok) return null
    return await resp.json()
  } catch {
    return null
  }
}

export async function fetchJson(url, opts) {
  const resp = await fetch(url, { credentials: 'include', ...(opts || {}) })
  if (!resp.ok) throw new Error(await readErrorMessage(resp))
  return await resp.json()
}
