import { useState, useEffect, useMemo } from 'react'
import { fetchJson } from '../utils/api'
import { navigate } from '../utils/navigation'
import { EventFrequencyChart } from '../components/EventFrequencyChart'
import { ProjectSettingsModal } from '../components/ProjectSettingsModal'

export function ProjectIssuesPage({ projectId, me }) {
  const [issues, setIssues] = useState([])
  const [error, setError] = useState('')
  const [eventFrequencyData, setEventFrequencyData] = useState(null)

  useEffect(() => {
    setError('')
    fetchJson(`/api/user/projects/${projectId}/issues`)
      .then((rows) => setIssues(rows || []))
      .catch((e) => setError(e.message || 'Failed to load issues'))

    fetchJson(`/api/user/projects/${projectId}/events/frequency`)
      .then((data) => setEventFrequencyData(data))
      .catch((e) => {
        console.warn('Failed to load event frequency:', e)
      })
  }, [projectId])

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
        <h2 className="pageSectionTitle">Issues</h2>
        <div className="pageCard" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="pageTable">
            <thead>
              <tr>
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
                  onClick={() => navigate(`/dashboard/projects/${projectId}/issues/${it.fingerprint}`)}
                >
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
