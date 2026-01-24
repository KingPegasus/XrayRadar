import { useState, useCallback, useEffect, useMemo } from 'react'
import { fetchJson } from '../utils/api'
import { navigate } from '../utils/navigation'

export function IssueDetailPage({ projectId, fingerprint }) {
  const [events, setEvents] = useState([])
  const [error, setError] = useState('')

  const load = useCallback(() => {
    setError('')
    fetchJson(`/api/user/projects/${projectId}/issues/${fingerprint}/events`)
      .then((rows) => setEvents(rows || []))
      .catch((e) => setError(e.message || 'Failed to load events'))
  }, [projectId, fingerprint])

  useEffect(() => load(), [load])

  // Calculate event frequency by day for chart
  const eventFrequency = useMemo(() => {
    const freq = {}
    events.forEach((e) => {
      const date = new Date(e.timestamp).toLocaleDateString()
      freq[date] = (freq[date] || 0) + 1
    })
    const sorted = Object.entries(freq).sort((a, b) => new Date(a[0]) - new Date(b[0]))
    const maxCount = Math.max(...Object.values(freq), 1)
    return { data: sorted, maxCount }
  }, [events])

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

        {/* Event Frequency Chart */}
        {eventFrequency.data.length > 0 && (
          <div style={{ marginTop: 20, marginBottom: 20 }}>
            <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 10, color: '#cbd5e1' }}>Event Frequency</div>
            <div style={{ background: 'rgba(0, 0, 0, 0.2)', padding: 16, borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)' }}>
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height: 120 }}>
                {eventFrequency.data.map(([date, count], idx) => {
                  const height = (count / eventFrequency.maxCount) * 100
                  return (
                    <div key={idx} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                      <div
                        style={{
                          width: '100%',
                          background: 'linear-gradient(to top, #2563eb, #3b82f6)',
                          height: `${height}%`,
                          minHeight: count > 0 ? '4px' : '0',
                          borderRadius: '4px 4px 0 0',
                          transition: 'all 0.2s',
                        }}
                        title={`${date}: ${count} event${count !== 1 ? 's' : ''}`}
                      />
                      <div style={{ fontSize: 10, color: '#94a3b8', writingMode: 'vertical-rl', textOrientation: 'mixed', transform: 'rotate(180deg)' }}>
                        {new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      </div>
                    </div>
                  )
                })}
              </div>
              <div style={{ marginTop: 8, fontSize: 11, color: '#94a3b8', textAlign: 'center' }}>
                Total: {events.length} event{events.length !== 1 ? 's' : ''} across {eventFrequency.data.length} day{eventFrequency.data.length !== 1 ? 's' : ''}
              </div>
            </div>
          </div>
        )}

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
