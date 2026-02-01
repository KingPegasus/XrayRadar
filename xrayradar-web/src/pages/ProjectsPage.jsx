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
    <div className="container page">
      <header className="pageHeader">
        <h1 className="pageTitle">Projects</h1>
        <p className="pageSubtitle">
          Signed in as <code>{me?.email}</code>
        </p>
      </header>

      <UsageWidget usage={usage} />

      {!me?.email_verified && (
        <div className="pageAlert">
          Verify your email to create projects.
        </div>
      )}
      <form onSubmit={create} className="pageForm">
        <div className="pageFormRow">
          <div style={{ flex: 1, minWidth: 240 }}>
            <label className="fieldLabel">New project name</label>
            <input
              className="fieldInput"
              style={{ marginTop: 6 }}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="New project name"
              disabled={!me?.email_verified}
            />
          </div>
          <button className="button buttonPrimary" type="submit" disabled={busy || !me?.email_verified} style={{ alignSelf: 'flex-end' }}>
            Create project
          </button>
        </div>
        {error ? (
          <div className="fieldError" role="alert">
            {error}
          </div>
        ) : null}
      </form>

      <section className="pageSection">
        <h2 className="pageSectionTitle">Your projects</h2>
        <div className="grid3">
          {(projects || []).map((p) => (
            <div
              key={p.id}
              className="pageCard pageCardInteractive"
              onClick={() => navigate(`/dashboard/projects/${p.id}`)}
            >
              <div className="pageCardTitle">{p.name}</div>
              <div className="pageCardText">
                Project ID: <code>{p.id}</code>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
