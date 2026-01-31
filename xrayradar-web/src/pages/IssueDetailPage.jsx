import { useState, useCallback, useEffect, useMemo } from 'react'
import { fetchJson } from '../utils/api'
import { navigate } from '../utils/navigation'
import { EventFrequencyChart } from '../components/EventFrequencyChart'

export function IssueDetailPage({ projectId, fingerprint }) {
  const [events, setEvents] = useState([])
  const [eventFrequencyData, setEventFrequencyData] = useState(null)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    setError('')
    // Fetch events list for display
    fetchJson(`/api/user/projects/${projectId}/issues/${fingerprint}/events`)
      .then((rows) => setEvents(rows || []))
      .catch((e) => setError(e.message || 'Failed to load events'))
    
    // Fetch aggregated frequency data (handles unlimited events efficiently)
    fetchJson(`/api/user/projects/${projectId}/issues/${fingerprint}/events/frequency`)
      .then((data) => setEventFrequencyData(data))
      .catch((e) => {
        // Silently fail for frequency chart - it's optional
        console.warn('Failed to load event frequency:', e)
      })
  }, [projectId, fingerprint])

  useEffect(() => load(), [load])

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
            <div style={{ fontWeight: 900, letterSpacing: '-0.02em', fontSize: 22 }}>Issue</div>
            <div className="small" style={{ color: 'var(--muted)', marginTop: 8 }}>
              Fingerprint: <code>{fingerprint}</code>
              {events.length > 0 && (
                <>
                  {' • '}
                  First seen: {new Date(events[events.length - 1]?.timestamp || Date.now()).toLocaleString()}
                  {' • '}
                  Last seen: {new Date(events[0]?.timestamp || Date.now()).toLocaleString()}
                  {' • '}
                  Total: {events.length} event{events.length !== 1 ? 's' : ''}
                </>
              )}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button className="button" type="button" onClick={() => navigate(`/dashboard/projects/${projectId}`)}>
              Back
            </button>
            <button className="button" type="button" onClick={load}>
              Refresh
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
                <th style={{ textAlign: 'left', padding: '8px 6px' }}>Time</th>
                <th style={{ textAlign: 'left', padding: '8px 6px' }}>Level</th>
                <th style={{ textAlign: 'left', padding: '8px 6px' }}>Message</th>
              </tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr
                  key={e.id}
                  style={{ cursor: 'pointer', borderTop: '1px solid rgba(255,255,255,0.08)' }}
                  onClick={() => navigate(`/dashboard/projects/${projectId}/issues/${fingerprint}/events/${e.id}`)}
                >
                  <td style={{ padding: '10px 6px', fontSize: 13 }}>{new Date(e.timestamp).toLocaleString()}</td>
                  <td style={{ padding: '10px 6px', fontSize: 13 }}>{e.level}</td>
                  <td style={{ padding: '10px 6px', fontSize: 13, color: 'var(--text)' }}>{e.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
