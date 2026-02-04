import { useState, useEffect, useMemo } from 'react'
import { fetchJson, bulkUpdateIssueStatus } from '../utils/api'
import { navigate } from '../utils/navigation'
import { EventFrequencyChart } from '../components/EventFrequencyChart'
import { ProjectSettingsModal } from '../components/ProjectSettingsModal'
import { IssueStatusBadge } from '../components/IssueStatusBadge'

export function ProjectIssuesPage({ projectId, me }) {
  const [issues, setIssues] = useState([])
  const [error, setError] = useState('')
  const [eventFrequencyData, setEventFrequencyData] = useState(null)
  const [statusFilter, setStatusFilter] = useState('all')
  const [selectedFingerprints, setSelectedFingerprints] = useState(new Set())
  const [bulkActionLoading, setBulkActionLoading] = useState(false)

  const loadIssues = () => {
    setError('')
    const url = statusFilter === 'all'
      ? `/api/user/projects/${projectId}/issues`
      : `/api/user/projects/${projectId}/issues?status=${statusFilter}`
    fetchJson(url)
      .then((rows) => setIssues(rows || []))
      .catch((e) => setError(e.message || 'Failed to load issues'))
  }

  useEffect(() => {
    loadIssues()

    fetchJson(`/api/user/projects/${projectId}/events/frequency`)
      .then((data) => setEventFrequencyData(data))
      .catch((e) => {
        console.warn('Failed to load event frequency:', e)
      })
  }, [projectId, statusFilter])

  const eventFrequency = useMemo(() => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const last30Days = []
    for (let i = 29; i >= 0; i--) {
      const date = new Date(today)
      date.setDate(date.getDate() - i)
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
          <h1 className="pageTitle">Project {projectId}</h1>
          <p className="pageSubtitle">
            Issues are grouped by fingerprint.
          </p>
        </div>
        <div className="pageActions" style={{ marginTop: 0 }}>
          <ProjectSettingsModal projectId={projectId} me={me} />
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
            <label htmlFor="status-filter" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              Filter:
              <select
                id="status-filter"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{ padding: '4px 8px' }}
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
              {issues.map((it) => (
                <tr
                  key={it.fingerprint}
                  style={{ cursor: 'pointer' }}
                  onClick={(e) => {
                    // Don't navigate if clicking checkbox
                    if (e.target.type !== 'checkbox') {
                      navigate(`/dashboard/projects/${projectId}/issues/${it.fingerprint}`)
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
                        navigate(`/dashboard/projects/${projectId}/issues/${it.fingerprint}`)
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
