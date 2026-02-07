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
  const text = await resp.text()
  if (!text || text.trim() === '') return null
  try {
    return JSON.parse(text)
  } catch {
    throw new Error('Invalid JSON in response')
  }
}

export async function updateIssueStatus(projectId, fingerprint, statusData) {
  return await fetchJson(`/api/user/projects/${projectId}/issues/${fingerprint}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(statusData),
  })
}

export async function bulkUpdateIssueStatus(projectId, fingerprints, statusData) {
  return await fetchJson(`/api/user/projects/${projectId}/issues/bulk-status`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fingerprints, ...statusData }),
  })
}
