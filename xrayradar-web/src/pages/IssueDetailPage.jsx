import { useState, useCallback, useEffect, useMemo } from 'react'
import { fetchJson } from '../utils/api'
import { navigate } from '../utils/navigation'
import { EventFrequencyChart } from '../components/EventFrequencyChart'
import { IssueBreakdown } from '../components/IssueBreakdown'
import { IssueStatusBadge } from '../components/IssueStatusBadge'
import { IssueStatusModal } from '../components/IssueStatusModal'

export function IssueDetailPage({ projectId, fingerprint }) {
  const [events, setEvents] = useState([])
  const [eventFrequencyData, setEventFrequencyData] = useState(null)
  const [breakdown, setBreakdown] = useState(null)
  const [issueStatus, setIssueStatus] = useState(null)
  const [error, setError] = useState('')
  const [statusModalOpen, setStatusModalOpen] = useState(false)

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

    // Load issue status - try to get from issues list first
    fetchJson(`/api/user/projects/${projectId}/issues`)
      .then((issues) => {
        const issue = issues.find(i => i.fingerprint === fingerprint)
        if (issue) {
          setIssueStatus({
            status: issue.status || 'open',
            resolved_release: issue.resolved_release,
            resolved_at: issue.resolved_at,
            reopened: issue.reopened || false,
          })
        }
      })
      .catch((e) => {
        console.warn('Failed to load issue status:', e)
      })
  }, [projectId, fingerprint])

  useEffect(() => load(), [load])

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

  const shouldShowAutoReopenNotification = useMemo(() => {
    if (!issueStatus || issueStatus.status !== 'resolved' || events.length === 0 || statusModalOpen) {
      return false
    }
    // Only show if there are events that occurred after the resolution time
    if (issueStatus.resolved_at) {
      const resolvedTime = new Date(issueStatus.resolved_at).getTime()
      return events.some(e => new Date(e.timestamp).getTime() > resolvedTime)
    }
    // If no resolved_at, show notification if there are any events (conservative)
    return true
  }, [issueStatus, events, statusModalOpen])

  return (
    <div className="container page">
      <header className="pageHeader" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
            <h1 className="pageTitle" style={{ margin: 0 }}>Issue</h1>
            {issueStatus && (
              <IssueStatusBadge
                status={issueStatus.status || 'open'}
                resolvedRelease={issueStatus.resolved_release}
                reopened={issueStatus.reopened}
                onClick={() => setStatusModalOpen(true)}
              />
            )}
          </div>
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

      {shouldShowAutoReopenNotification && (
        <div className="auto-reopen-notification" style={{ marginBottom: 16, padding: 12, background: '#fef3c7', border: '1px solid #f59e0b', borderRadius: 8, color: '#92400e' }}>
          <strong>Note:</strong> This issue is marked as resolved, but new events have been recorded. 
          {issueStatus.resolved_release && ` It was resolved for release "${issueStatus.resolved_release}".`}
          {!issueStatus.resolved_release && ' It may have been auto-reopened due to new occurrences.'}
        </div>
      )}

      {issueStatus && issueStatus.reopened && issueStatus.status === 'open' && (
        <div className="reopened-notification" style={{ marginBottom: 16, padding: 12, background: 'rgba(251, 191, 36, 0.1)', border: '1px solid rgba(251, 191, 36, 0.3)', borderRadius: 8, color: '#fbbf24', fontSize: 13 }}>
          <strong>Reopened:</strong> This issue was previously resolved and has been automatically reopened due to new events.
        </div>
      )}

      {statusModalOpen && issueStatus && (
        <IssueStatusModal
          projectId={projectId}
          fingerprint={fingerprint}
          currentStatus={issueStatus.status || 'open'}
          resolvedRelease={issueStatus.resolved_release}
          resolvedAt={issueStatus.resolved_at}
          onStatusChange={(newStatus) => {
            setIssueStatus(newStatus)
            load()
          }}
          onClose={() => setStatusModalOpen(false)}
        />
      )}

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
