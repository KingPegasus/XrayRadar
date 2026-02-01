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
      <div className="container page">
        <div className="pageCard">
          <p className="pageEmpty" style={{ margin: 0 }}>Loading event…</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container page">
        <div className="pageCard">
          <div className="fieldError" role="alert">{error}</div>
          <div className="pageActions">
            <button className="button" type="button" onClick={() => navigate(`/dashboard/projects/${projectId}/issues/${fingerprint}`)}>
              Back to Issue
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!event) {
    return null
  }

  return (
    <div className="container page">
      <header className="pageHeader" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <h1 className="pageTitle">Event Details</h1>
          <p className="pageSubtitle">
            ID: <code>{event.id}</code> • {new Date(event.timestamp).toLocaleString()}
          </p>
        </div>
        <div className="pageActions" style={{ marginTop: 0 }}>
          <button className="button" type="button" onClick={() => navigate(`/dashboard/projects/${projectId}/issues/${fingerprint}`)}>
            Back to Issue
          </button>
        </div>
      </header>

      <EventDetailView event={event} />
    </div>
  )
}
