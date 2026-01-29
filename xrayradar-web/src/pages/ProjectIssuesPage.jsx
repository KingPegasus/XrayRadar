import { useState, useEffect, useMemo } from 'react'
import { fetchJson } from '../utils/api'
import { navigate } from '../utils/navigation'
import { EventFrequencyChart } from '../components/EventFrequencyChart'
import { ProjectSettingsModal } from '../components/ProjectSettingsModal'

export function ProjectIssuesPage({ projectId }) {
  const [issues, setIssues] = useState([])
  const [error, setError] = useState('')

  const [eventFrequencyData, setEventFrequencyData] = useState(null)

  useEffect(() => {
    setError('')
    fetchJson(`/api/user/projects/${projectId}/issues`)
      .then((rows) => setIssues(rows || []))
      .catch((e) => setError(e.message || 'Failed to load issues'))
    
    // Fetch aggregated frequency data (handles unlimited events efficiently)
    fetchJson(`/api/user/projects/${projectId}/events/frequency`)
      .then((data) => setEventFrequencyData(data))
      .catch((e) => {
        // Silently fail for frequency chart - it's optional
        console.warn('Failed to load event frequency:', e)
      })
  }, [projectId])

  // Calculate event frequency by day for chart (last 30 days)
  const eventFrequency = useMemo(() => {
    // Generate array of last 30 days
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const last30Days = []
    for (let i = 29; i >= 0; i--) {
      const date = new Date(today)
      date.setDate(date.getDate() - i)
      const dateKey = date.toISOString().split('T')[0]
      last30Days.push(dateKey)
    }
    
    // Use aggregated frequency data from backend, or initialize to 0
    const freq = {}
    last30Days.forEach(dateKey => {
      freq[dateKey] = eventFrequencyData?.frequency?.[dateKey] || 0
    })
    
    // Convert to sorted array (already sorted by date)
    const sorted = last30Days.map(dateKey => [dateKey, freq[dateKey] || 0])
    const counts = Object.values(freq)
    const maxCount = counts.length > 0 ? Math.max(...counts) : 1
    
    return { data: sorted, maxCount, total: eventFrequencyData?.total || 0 }
  }, [eventFrequencyData])

  return (
    <div className="container" style={{ padding: '46px 0' }}>
      <div className="panel" style={{ padding: 18 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontWeight: 900, letterSpacing: '-0.02em', fontSize: 22 }}>Project {projectId}</div>
            <div className="small" style={{ color: 'var(--muted)', marginTop: 8 }}>
              Issues are grouped by fingerprint.
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <ProjectSettingsModal projectId={projectId} />
            <button className="button" type="button" onClick={() => navigate('/dashboard')}>
              Back
            </button>
          </div>
        </div>

        {error ? (
          <div className="fieldError" role="alert" style={{ marginTop: 10 }}>
            {error}
          </div>
        ) : null}

        <EventFrequencyChart eventFrequency={eventFrequency} />

        <div style={{ marginTop: 14 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ color: 'var(--muted)', fontSize: 13 }}>
                <th style={{ textAlign: 'left', padding: '8px 6px' }}>First seen</th>
                <th style={{ textAlign: 'left', padding: '8px 6px' }}>Last seen</th>
                <th style={{ textAlign: 'left', padding: '8px 6px' }}>Count</th>
                <th style={{ textAlign: 'left', padding: '8px 6px' }}>Level</th>
                <th style={{ textAlign: 'left', padding: '8px 6px' }}>Message</th>
              </tr>
            </thead>
            <tbody>
              {issues.map((it) => (
                <tr
                  key={it.fingerprint}
                  style={{ cursor: 'pointer', borderTop: '1px solid rgba(255,255,255,0.08)' }}
                  onClick={() => navigate(`/dashboard/projects/${projectId}/issues/${it.fingerprint}`)}
                >
                  <td style={{ padding: '10px 6px', fontSize: 13 }}>{new Date(it.first_seen).toLocaleString()}</td>
                  <td style={{ padding: '10px 6px', fontSize: 13 }}>{new Date(it.last_seen).toLocaleString()}</td>
                  <td style={{ padding: '10px 6px', fontSize: 13 }}>{it.count}</td>
                  <td style={{ padding: '10px 6px', fontSize: 13 }}>{it.level}</td>
                  <td style={{ padding: '10px 6px', fontSize: 13, color: 'var(--text)' }}>{it.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
