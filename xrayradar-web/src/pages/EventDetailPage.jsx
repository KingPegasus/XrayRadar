import { useState, useEffect } from 'react'
import { fetchJson } from '../utils/api'
import { navigate } from '../utils/navigation'
import { EventDetailView } from '../components/EventDetailView'

export function EventDetailPage({ projectId, fingerprint, eventId }) {
  const [event, setEvent] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    setError('')
    fetchJson(`/api/user/projects/${projectId}/events/${eventId}`)
      .then((ev) => setEvent(ev))
      .catch((e) => setError(e.message || 'Failed to load event'))
      .finally(() => setLoading(false))
  }, [projectId, eventId])

  if (loading) {
    return (
      <div className="container" style={{ padding: '46px 0' }}>
        <div className="panel" style={{ padding: 18 }}>
          <div className="small" style={{ color: 'var(--muted)' }}>Loading event...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container" style={{ padding: '46px 0' }}>
        <div className="panel" style={{ padding: 18 }}>
          <div className="fieldError" role="alert">{error}</div>
          <button className="button" type="button" onClick={() => navigate(`/dashboard/projects/${projectId}/issues/${fingerprint}`)} style={{ marginTop: 10 }}>
            Back to Issue
          </button>
        </div>
      </div>
    )
  }

  if (!event) {
    return null
  }

  return (
    <div className="container" style={{ padding: '46px 0' }}>
      <div className="panel" style={{ padding: 18 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
          <div>
            <div style={{ fontWeight: 900, letterSpacing: '-0.02em', fontSize: 22 }}>Event Details</div>
            <div className="small" style={{ color: 'var(--muted)', marginTop: 8 }}>
              ID: <code>{event.id}</code> • {new Date(event.timestamp).toLocaleString()}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button className="button" type="button" onClick={() => navigate(`/dashboard/projects/${projectId}/issues/${fingerprint}`)}>
              Back to Issue
            </button>
          </div>
        </div>

        <EventDetailView event={event} />
      </div>
    </div>
  )
}
