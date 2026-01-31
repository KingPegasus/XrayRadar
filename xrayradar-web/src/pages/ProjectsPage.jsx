import { useState, useCallback, useEffect } from 'react'
import { fetchJson } from '../utils/api'
import { navigate } from '../utils/navigation'
import { UsageWidget } from '../components/UsageWidget'

export function ProjectsPage({ me }) {
  const [projects, setProjects] = useState([])
  const [usage, setUsage] = useState(null)
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setError('')
    try {
      const [projectsData, usageData] = await Promise.all([
        fetchJson('/api/user/projects'),
        fetchJson('/api/user/usage'),
      ])
      setProjects(Array.isArray(projectsData) ? projectsData : [])
      setUsage(usageData)
    } catch (e) {
      setError(e.message || 'Failed to load projects')
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const create = async (e) => {
    e.preventDefault()
    if (busy) return
    const trimmed = name.trim()
    if (!trimmed) {
      setError('Project name is required.')
      return
    }
    setBusy(true)
    setError('')
    try {
      await fetchJson('/api/user/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: trimmed }),
      })
      setName('')
      await load()
    } catch (e2) {
      setError(e2.message || 'Failed to create project')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="container" style={{ padding: '46px 0' }}>
      <div className="panel" style={{ padding: 18 }}>
        <div style={{ fontWeight: 900, letterSpacing: '-0.02em', fontSize: 22 }}>Projects</div>
        <div className="small" style={{ color: 'var(--muted)', marginTop: 8 }}>
          Signed in as <code>{me?.email}</code>
        </div>

        <UsageWidget usage={usage} />

        {!me?.email_verified && (
          <div className="small" style={{ marginTop: 14, color: '#fbbf24' }}>
            Verify your email to create projects.
          </div>
        )}
        <form onSubmit={create} style={{ marginTop: 14, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <input
            className="fieldInput"
            style={{ flex: 1, minWidth: 240 }}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="New project name"
            disabled={!me?.email_verified}
          />
          <button className="button buttonPrimary" type="submit" disabled={busy || !me?.email_verified}>
            Create project
          </button>
        </form>

        {error ? (
          <div className="fieldError" role="alert" style={{ marginTop: 10 }}>
            {error}
          </div>
        ) : null}

        <div style={{ marginTop: 14 }} className="grid3">
          {(projects || []).map((p) => (
            <div key={p.id} className="card" style={{ cursor: 'pointer' }} onClick={() => navigate(`/dashboard/projects/${p.id}`)}>
              <div className="cardTitle">{p.name}</div>
              <div className="cardText" style={{ marginTop: 6 }}>
                Project ID: <code>{p.id}</code>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
