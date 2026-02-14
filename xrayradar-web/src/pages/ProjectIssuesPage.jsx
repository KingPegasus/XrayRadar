import { useState, useEffect, useMemo } from 'react'
import { fetchJson, bulkUpdateIssueStatus } from '../utils/api'
import { navigate } from '../utils/navigation'
import { EventFrequencyChart } from '../components/EventFrequencyChart'
import { ProjectSettingsModal } from '../components/ProjectSettingsModal'
import { IssueStatusBadge } from '../components/IssueStatusBadge'

export function ProjectIssuesPage({ projectId, me }) {
  const [projectName, setProjectName] = useState(null)
  const [isOwner, setIsOwner] = useState(false)
  const [issues, setIssues] = useState([])
  const [error, setError] = useState('')
  const [eventFrequencyData, setEventFrequencyData] = useState(null)
  const [statusFilter, setStatusFilter] = useState('all')
  const [environmentFilter, setEnvironmentFilter] = useState(null)
  const [environmentOptions, setEnvironmentOptions] = useState([])
  const [selectedFingerprints, setSelectedFingerprints] = useState(new Set())
  const [bulkActionLoading, setBulkActionLoading] = useState(false)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search || '')
    const envFromUrl = (params.get('environment') || '').trim()
    const storageKey = `project:${projectId}:environment`
    const envFromStorage = (localStorage.getItem(storageKey) || '').trim()
    const initial = envFromUrl || envFromStorage || ''
    setEnvironmentFilter(initial || null)
  }, [projectId])

  useEffect(() => {
    const storageKey = `project:${projectId}:environment`
    const params = new URLSearchParams(window.location.search || '')
    if (environmentFilter) {
      localStorage.setItem(storageKey, environmentFilter)
      params.set('environment', environmentFilter)
    } else {
      localStorage.removeItem(storageKey)
      params.delete('environment')
    }
    const query = params.toString()
    const next = `${window.location.pathname}${query ? `?${query}` : ''}`
    window.history.replaceState({}, '', next)
  }, [projectId, environmentFilter])

  const loadIssues = () => {
    setError('')
    const params = new URLSearchParams()
    if (statusFilter !== 'all') params.set('status', statusFilter)
    if (environmentFilter) params.set('environment', environmentFilter)
    const url = `/api/user/projects/${projectId}/issues${params.toString() ? `?${params.toString()}` : ''}`
    Promise.resolve(fetchJson(url))
      .then((rows) => setIssues(Array.isArray(rows) ? rows : []))
      .catch((e) => setError(e.message || 'Failed to load issues'))
  }

  useEffect(() => {
    Promise.resolve(fetchJson('/api/user/projects'))
      .then((projects) => {
        const p = Array.isArray(projects) ? projects.find((x) => x.id === projectId) : null
        setProjectName(p ? p.name : null)
        setIsOwner(p?.is_owner ?? false)
      })
      .catch(() => { setProjectName(null); setIsOwner(false) })
  }, [projectId])

  useEffect(() => {
    loadIssues()
    const params = new URLSearchParams()
    if (environmentFilter) params.set('environment', environmentFilter)
    Promise.resolve(fetchJson(`/api/user/projects/${projectId}/events/frequency${params.toString() ? `?${params.toString()}` : ''}`))
      .then((data) => setEventFrequencyData(data))
      .catch((e) => {
        console.warn('Failed to load event frequency:', e)
      })
  }, [projectId, statusFilter, environmentFilter])

  useEffect(() => {
    Promise.resolve(fetchJson(`/api/user/projects/${projectId}/environments`))
      .then((rows) => setEnvironmentOptions(Array.isArray(rows) ? rows : []))
      .catch(() => setEnvironmentOptions([]))
  }, [projectId])

  const eventFrequency = useMemo(() => {
    // Use UTC dates to match backend (which returns UTC dates)
    const now = new Date()
    const todayUTC = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()))
    const last30Days = []
    for (let i = 29; i >= 0; i--) {
      const date = new Date(todayUTC)
      date.setUTCDate(date.getUTCDate() - i)
      const dateKey = date.toISOString().split('T')[0]
      last30Days.push(dateKey)
    }
    const freq = {}
    last30Days.forEach(dateKey => {
      freq[dateKey] = eventFrequencyData?.frequency?.[dateKey] || 0
    })
    const sorted = last30Days.map(dateKey => [dateKey, freq[dateKey] || 0])
    const counts = Object.values(freq)
    const maxCount = counts.length > 0 ? Math.max(...counts) : 1
    return { data: sorted, maxCount, total: eventFrequencyData?.total || 0 }
  }, [eventFrequencyData])

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedFingerprints(new Set(issues.map(i => i.fingerprint)))
    } else {
      setSelectedFingerprints(new Set())
    }
  }

  const handleSelectIssue = (fingerprint, checked) => {
    const newSelected = new Set(selectedFingerprints)
    if (checked) {
      newSelected.add(fingerprint)
    } else {
      newSelected.delete(fingerprint)
    }
    setSelectedFingerprints(newSelected)
  }

  const handleBulkAction = async (status) => {
    if (selectedFingerprints.size === 0) return
    setBulkActionLoading(true)
    try {
      await bulkUpdateIssueStatus(projectId, Array.from(selectedFingerprints), { status })
      setSelectedFingerprints(new Set())
      loadIssues()
    } catch (e) {
      setError(e.message || 'Failed to update issues')
    } finally {
      setBulkActionLoading(false)
    }
  }

  return (
    <div className="container page">
      <header className="pageHeader" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <h1 className="pageTitle">{projectName ?? `Project ${projectId}`}</h1>
          <p className="pageSubtitle">
            Issues are grouped by fingerprint.
          </p>
        </div>
        <div className="pageActions" style={{ marginTop: 0 }}>
          {isOwner && (
            <ProjectSettingsModal
              projectId={projectId}
              me={me}
              projectName={projectName}
              isOwner={isOwner}
              onProjectNameUpdated={setProjectName}
            />
          )}
          <button className="button" type="button" onClick={() => navigate('/dashboard/projects')}>
            Back
          </button>
        </div>
      </header>

      {error ? (
        <div className="fieldError" role="alert">
          {error}
        </div>
      ) : null}

      <EventFrequencyChart eventFrequency={eventFrequency} />

      <section className="pageSection">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 className="pageSectionTitle" style={{ margin: 0 }}>Issues</h2>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <label htmlFor="environment-filter" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              Environment:
              <select
                className="fieldInput"
                id="environment-filter"
                value={environmentFilter || 'all'}
                onChange={(e) => setEnvironmentFilter(e.target.value === 'all' ? null : e.target.value)}
                style={{ width: 160 }}
              >
                <option value="all">All</option>
                {environmentOptions.map((opt) => (
                  <option key={opt.environment} value={opt.environment}>
                    {opt.environment}
                  </option>
                ))}
              </select>
            </label>
            <label htmlFor="status-filter" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              Filter:
              <select
                className="fieldInput"
                id="status-filter"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{ width: 160 }}
              >
                <option value="all">All</option>
                <option value="open">Open</option>
                <option value="in_progress">In Progress</option>
                <option value="resolved">Resolved</option>
                <option value="ignored">Ignored</option>
              </select>
            </label>
          </div>
        </div>

        {selectedFingerprints.size > 0 && (
          <div className="bulk-actions-bar" style={{ marginBottom: 16, padding: 8, background: '#1f2937', borderRadius: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 13 }}>{selectedFingerprints.size} selected</span>
            <div style={{ display: 'flex', gap: 6 }}>
              <button
                className="button"
                type="button"
                onClick={() => handleBulkAction('in_progress')}
                disabled={bulkActionLoading}
                style={{ padding: '4px 10px', fontSize: 12 }}
              >
                In Progress
              </button>
              <button
                className="button"
                type="button"
                onClick={() => handleBulkAction('resolved')}
                disabled={bulkActionLoading}
                style={{ padding: '4px 10px', fontSize: 12 }}
              >
                Resolve
              </button>
              <button
                className="button"
                type="button"
                onClick={() => handleBulkAction('ignored')}
                disabled={bulkActionLoading}
                style={{ padding: '4px 10px', fontSize: 12 }}
              >
                Ignore
              </button>
              <button
                className="button"
                type="button"
                onClick={() => setSelectedFingerprints(new Set())}
                disabled={bulkActionLoading}
                style={{ padding: '4px 10px', fontSize: 12 }}
              >
                Clear
              </button>
            </div>
          </div>
        )}

        <div className="pageCard" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="pageTable">
            <thead>
              <tr>
                <th style={{ width: 40 }}>
                  <input
                    type="checkbox"
                    checked={issues.length > 0 && selectedFingerprints.size === issues.length}
                    onChange={handleSelectAll}
                  />
                </th>
                <th>Status</th>
                <th>First seen</th>
                <th>Last seen</th>
                <th>Count</th>
                <th>Level</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              {(Array.isArray(issues) ? issues : []).map((it) => (
                <tr
                  key={it.fingerprint}
                  style={{ cursor: 'pointer' }}
                  onClick={(e) => {
                    // Don't navigate if clicking checkbox
                    if (e.target.type !== 'checkbox') {
                      const envQ = environmentFilter ? `?environment=${encodeURIComponent(environmentFilter)}` : ''
                      navigate(`/dashboard/projects/${projectId}/issues/${it.fingerprint}${envQ}`)
                    }
                  }}
                >
                  <td onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={selectedFingerprints.has(it.fingerprint)}
                      onChange={(e) => handleSelectIssue(it.fingerprint, e.target.checked)}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </td>
                  <td onClick={(e) => e.stopPropagation()}>
                    <IssueStatusBadge
                      status={it.status || 'open'}
                      resolvedRelease={it.resolved_release}
                      reopened={it.reopened}
                      onClick={(e) => {
                        e.stopPropagation()
                        const envQ = environmentFilter ? `?environment=${encodeURIComponent(environmentFilter)}` : ''
                        navigate(`/dashboard/projects/${projectId}/issues/${it.fingerprint}${envQ}`)
                      }}
                    />
                  </td>
                  <td>{new Date(it.first_seen).toLocaleString()}</td>
                  <td>{new Date(it.last_seen).toLocaleString()}</td>
                  <td>{it.count}</td>
                  <td>{it.level}</td>
                  <td>{it.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
