import { useState, useCallback, useEffect, useMemo } from 'react'
import { fetchJson } from '../utils/api'
import { navigate } from '../utils/navigation'
import { EventFrequencyChart } from '../components/EventFrequencyChart'
import { IssueBreakdown } from '../components/IssueBreakdown'

export function IssueDetailPage({ projectId, fingerprint }) {
  const [events, setEvents] = useState([])
  const [eventFrequencyData, setEventFrequencyData] = useState(null)
  const [breakdown, setBreakdown] = useState(null)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    setError('')
    fetchJson(`/api/user/projects/${projectId}/issues/${fingerprint}/events`)
      .then((rows) => setEvents(rows || []))
      .catch((e) => setError(e.message || 'Failed to load events'))

    fetchJson(`/api/user/projects/${projectId}/issues/${fingerprint}/events/frequency`)
      .then((data) => setEventFrequencyData(data))
      .catch((e) => {
        console.warn('Failed to load event frequency:', e)
      })

    fetchJson(`/api/user/projects/${projectId}/issues/${fingerprint}/breakdown`)
      .then((data) => setBreakdown(data))
      .catch((e) => {
        console.warn('Failed to load breakdown:', e)
      })
  }, [projectId, fingerprint])

  useEffect(() => load(), [load])

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
          <h1 className="pageTitle">Issue</h1>
          <p className="pageSubtitle">
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
          </p>
        </div>
        <div className="pageActions" style={{ marginTop: 0, marginLeft: 'auto' }}>
          <button className="button" type="button" onClick={() => navigate(`/dashboard/projects/${projectId}`)}>
            Back
          </button>
          <button className="button" type="button" onClick={load}>
            Refresh
          </button>
        </div>
      </header>

      {error ? (
        <div className="fieldError" role="alert">
          {error}
        </div>
      ) : null}

      <EventFrequencyChart eventFrequency={eventFrequency} />

      {breakdown && (
        <IssueBreakdown
          byRelease={breakdown.by_release}
          byEnvironment={breakdown.by_environment}
        />
      )}

      <section className="pageSection">
        <h2 className="pageSectionTitle">Events</h2>
        <div className="pageCard" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="pageTable">
            <thead>
              <tr>
                <th>Time</th>
                <th>Level</th>
                <th>Release</th>
                <th>Environment</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr
                  key={e.id}
                  style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/dashboard/projects/${projectId}/issues/${fingerprint}/events/${e.id}`)}
                >
                  <td>{new Date(e.timestamp).toLocaleString()}</td>
                  <td>{e.level}</td>
                  <td>{e.release ?? '—'}</td>
                  <td>{e.environment ?? '—'}</td>
                  <td>{e.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
