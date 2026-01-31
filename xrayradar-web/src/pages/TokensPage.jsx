import { useState, useCallback, useEffect } from 'react'
import { fetchJson } from '../utils/api'

export function TokensPage({ me }) {
  const [tokens, setTokens] = useState([])
  const [projects, setProjects] = useState([])
  const [tokenProjects, setTokenProjects] = useState({}) // token_id -> [project_ids]
  const [requests, setRequests] = useState([])
  const [name, setName] = useState('')
  const [note, setNote] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [expandedToken, setExpandedToken] = useState(null)

  const loadProjects = useCallback(async () => {
    try {
      setProjects(await fetchJson('/api/user/projects'))
    } catch (e) {
      setError(e.message || 'Failed to load projects')
    }
  }, [])

  const loadTokens = useCallback(async () => {
    try {
      const ts = await fetchJson('/api/user/tokens')
      const tokenList = Array.isArray(ts) ? ts : []
      setTokens(tokenList)
      // Load project access for each token
      const tp = {}
      for (const t of tokenList) {
        if (!t.revoked_at) {
          try {
            const access = await fetchJson(`/api/user/tokens/${t.id}/projects`)
            tp[t.id] = access.map((a) => a.project_id)
          } catch (e) {
            tp[t.id] = []
          }
        }
      }
      setTokenProjects(tp)
    } catch (e) {
      setError(e.message || 'Failed to load tokens')
    }
  }, [])

  const loadRequests = useCallback(async () => {
    try {
      setRequests(await fetchJson('/api/user/token-requests'))
    } catch (e) {
      setError(e.message || 'Failed to load token requests')
    }
  }, [])

  useEffect(() => {
    loadProjects()
    loadTokens()
    loadRequests()
  }, [loadProjects, loadTokens, loadRequests])

  const grantAccess = async (tokenId, projectId) => {
    try {
      await fetchJson(`/api/user/tokens/${tokenId}/projects/${projectId}/grant`, { method: 'POST' })
      await loadTokens() // Reload to refresh project access
    } catch (e) {
      setError(e.message || 'Failed to grant project access')
    }
  }

  const createRequest = async (e) => {
    e.preventDefault()
    if (busy) return
    const trimmedName = name.trim()
    if (!trimmedName) {
      setError('Token name is required.')
      return
    }
    setBusy(true)
    setError('')
    try {
      await fetchJson('/api/user/token-requests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: trimmedName, note: note.trim() || null }),
      })
      setName('')
      setNote('')
      await loadRequests()
    } catch (e2) {
      setError(e2.message || 'Failed to create token request')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="container" style={{ padding: '46px 0' }}>
      <div className="panel" style={{ padding: 18 }}>
        <div style={{ fontWeight: 900, letterSpacing: '-0.02em', fontSize: 22 }}>Tokens</div>
        <div className="small" style={{ color: 'var(--muted)', marginTop: 8 }}>
          Manage your API tokens and request new ones from an admin.
        </div>

        {error ? (
          <div className="fieldError" role="alert" style={{ marginTop: 14 }}>
            {error}
          </div>
        ) : null}

        {!me?.email_verified && (
          <div className="small" style={{ marginTop: 14, color: '#fbbf24' }}>
            Verify your email to request tokens or grant project access.
          </div>
        )}
        <div style={{ marginTop: 20 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 10 }}>Request a new token</h3>
          <form onSubmit={createRequest} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div>
              <label className="fieldLabel">Token name</label>
              <input
                className="fieldInput"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Production API"
                disabled={busy || !me?.email_verified}
              />
            </div>
            <div>
              <label className="fieldLabel">Note (optional)</label>
              <textarea
                className="fieldInput"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Additional context for the admin..."
                rows={3}
                disabled={busy || !me?.email_verified}
                style={{ resize: 'vertical', fontFamily: 'inherit' }}
              />
            </div>
            <button className="button buttonPrimary" type="submit" disabled={busy || !me?.email_verified} style={{ alignSelf: 'flex-start' }}>
              {busy ? 'Requesting...' : 'Request token'}
            </button>
          </form>
        </div>

        <div style={{ marginTop: 32 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 10 }}>My tokens</h3>
          <div className="small" style={{ color: 'var(--muted)', marginBottom: 14 }}>
            Tokens are not automatically linked to projects. Grant access to your projects below to use the token with them.
          </div>
          {(!Array.isArray(tokens) || tokens.length === 0) ? (
            <div className="small" style={{ color: 'var(--muted)' }}>No tokens yet.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {tokens.map((t) => {
                const hasAccess = tokenProjects[t.id] || []
                const isExpanded = expandedToken === t.id
                return (
                  <div key={t.id} className="card" style={{ padding: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10, flexWrap: 'wrap' }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div className="cardTitle" style={{ fontSize: 15 }}>{t.name}</div>
                        <div className="small" style={{ color: 'var(--muted)', marginTop: 4 }}>
                          Created: {new Date(t.created_at).toLocaleString()}
                          {t.revoked_at ? ` • Revoked: ${new Date(t.revoked_at).toLocaleString()}` : ''}
                        </div>
                        {t.token && !t.revoked_at ? (
                          <div style={{ marginTop: 8 }}>
                            <code style={{ fontSize: 12, background: 'rgba(255,255,255,0.1)', padding: '4px 8px', borderRadius: 4, wordBreak: 'break-all' }}>
                              {t.token}
                            </code>
                          </div>
                        ) : null}
                        {!t.revoked_at && (
                          <div style={{ marginTop: 10 }}>
                            <div className="small" style={{ color: 'var(--muted)', marginBottom: 6 }}>
                              Project access: {hasAccess.length > 0 ? `${hasAccess.length} project(s)` : 'None'}
                            </div>
                            {hasAccess.length > 0 && (
                              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 6 }}>
                                {hasAccess.map((pid) => {
                                  const proj = projects.find((p) => p.id === pid)
                                  return proj ? (
                                    <span key={pid} className="badge" style={{ background: 'rgba(37, 99, 235, 0.2)', color: '#93c5fd' }}>
                                      {proj.name}
                                    </span>
                                  ) : null
                                })}
                              </div>
                            )}
                            {projects.length > 0 && (
                              <div style={{ marginTop: 10 }}>
                                <button
                                  className="button"
                                  type="button"
                                  onClick={() => setExpandedToken(isExpanded ? null : t.id)}
                                  disabled={!me?.email_verified}
                                  style={{ fontSize: 13, padding: '6px 12px' }}
                                >
                                  {isExpanded ? 'Hide' : 'Manage'} project access
                                </button>
                                {isExpanded && (
                                  <div style={{ marginTop: 10, padding: 10, background: 'rgba(255,255,255,0.03)', borderRadius: 6 }}>
                                    <div className="small" style={{ color: 'var(--muted)', marginBottom: 8 }}>
                                      Grant access to projects:
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                      {projects.map((p) => {
                                        const hasAccessToProject = hasAccess.includes(p.id)
                                        return (
                                          <div key={p.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10 }}>
                                            <span className="small">{p.name} (ID: {p.id})</span>
                                            {hasAccessToProject ? (
                                              <span className="badge" style={{ background: 'rgba(34, 197, 94, 0.2)', color: '#86efac', fontSize: 11 }}>
                                                Has access
                                              </span>
                                            ) : (
                                              <button
                                                className="button"
                                                type="button"
                                                onClick={() => grantAccess(t.id, p.id)}
                                                disabled={!me?.email_verified}
                                                style={{ fontSize: 12, padding: '4px 10px' }}
                                              >
                                                Grant access
                                              </button>
                                            )}
                                          </div>
                                        )
                                      })}
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                      {t.revoked_at ? (
                        <span className="badge" style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5' }}>
                          Revoked
                        </span>
                      ) : (
                        <span className="badge" style={{ background: 'rgba(34, 197, 94, 0.2)', color: '#86efac' }}>
                          Active
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        <div style={{ marginTop: 32 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 10 }}>Token requests</h3>
          {requests.length === 0 ? (
            <div className="small" style={{ color: 'var(--muted)' }}>No requests yet.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {requests.map((r) => (
                <div key={r.id} className="card" style={{ padding: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10, flexWrap: 'wrap' }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div className="cardTitle" style={{ fontSize: 15 }}>{r.name}</div>
                      {r.note ? (
                        <div className="small" style={{ color: 'var(--muted)', marginTop: 4 }}>
                          {r.note}
                        </div>
                      ) : null}
                      <div className="small" style={{ color: 'var(--muted)', marginTop: 4 }}>
                        Requested: {new Date(r.created_at).toLocaleString()}
                        {r.fulfilled_at ? ` • Fulfilled: ${new Date(r.fulfilled_at).toLocaleString()}` : ''}
                      </div>
                    </div>
                    {r.fulfilled_at ? (
                      <span className="badge" style={{ background: 'rgba(34, 197, 94, 0.2)', color: '#86efac' }}>
                        Fulfilled
                      </span>
                    ) : (
                      <span className="badge" style={{ background: 'rgba(251, 191, 36, 0.2)', color: '#fde047' }}>
                        Pending
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
