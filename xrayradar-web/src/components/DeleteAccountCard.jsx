import { useState, useEffect } from 'react'
import { fetchJson } from '../utils/api'

export function DeleteAccountCard({ me }) {
  const [deletionRequest, setDeletionRequest] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showConfirm, setShowConfirm] = useState(false)
  const [reason, setReason] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchJson('/api/user/deletion-request')
      .then((data) => {
        setDeletionRequest(data)
        setLoading(false)
      })
      .catch(() => {
        setLoading(false)
      })
  }, [])

  const handleRequestDeletion = async () => {
    setSubmitting(true)
    setError('')
    try {
      const data = await fetchJson('/api/user/deletion-request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: reason.trim() || null }),
      })
      setDeletionRequest(data)
      setShowConfirm(false)
      setReason('')
    } catch (e) {
      setError(e.message || 'Failed to request deletion')
    } finally {
      setSubmitting(false)
    }
  }

  const handleCancelRequest = async () => {
    setSubmitting(true)
    setError('')
    try {
      await fetchJson('/api/user/deletion-request', { method: 'DELETE' })
      setDeletionRequest(null)
    } catch (e) {
      setError(e.message || 'Failed to cancel request')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return null

  const verified = me?.email_verified

  return (
    <div style={{ marginTop: 20 }}>
      <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 10, color: '#fca5a5' }}>Danger Zone</div>
      <div style={{ background: 'rgba(239, 68, 68, 0.1)', padding: 16, borderRadius: 8, border: '1px solid rgba(239, 68, 68, 0.3)' }}>
        {deletionRequest ? (
          <div>
            <div style={{ fontWeight: 600, marginBottom: 8, color: '#fca5a5' }}>
              Account Deletion Requested
            </div>
            <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12 }}>
              Your account deletion request is pending review. An admin will process it and permanently delete your account and all data.
            </p>
            <p style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 12 }}>
              Requested on: {new Date(deletionRequest.created_at).toLocaleDateString()}
              {deletionRequest.reason && (
                <><br />Reason: {deletionRequest.reason}</>
              )}
            </p>
            {error && <div className="fieldError" style={{ marginBottom: 10 }}>{error}</div>}
            <button
              type="button"
              className="button"
              onClick={handleCancelRequest}
              disabled={submitting}
            >
              {submitting ? 'Cancelling...' : 'Cancel Request'}
            </button>
          </div>
        ) : !verified ? (
          <div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>Delete Account</div>
            <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12 }}>
              Verify your email to request account deletion.
            </p>
          </div>
        ) : showConfirm ? (
          <div>
            <div style={{ fontWeight: 600, marginBottom: 8, color: '#fca5a5' }}>
              Confirm Account Deletion
            </div>
            <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12 }}>
              This will request permanent deletion of your account and all associated data including:
            </p>
            <ul style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12, paddingLeft: 20 }}>
              <li>All your projects</li>
              <li>All events stored in your projects</li>
              <li>All your tokens</li>
              <li>Your account and settings</li>
            </ul>
            <p style={{ fontSize: 13, color: '#fca5a5', marginBottom: 12 }}>
              This action cannot be undone.
            </p>
            <div style={{ marginBottom: 12 }}>
              <label style={{ fontSize: 12, color: 'var(--muted)', display: 'block', marginBottom: 6 }}>
                Reason for leaving (optional)
              </label>
              <textarea
                className="fieldInput"
                style={{ width: '100%', minHeight: 60, resize: 'vertical' }}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Help us improve..."
              />
            </div>
            {error && <div className="fieldError" style={{ marginBottom: 10 }}>{error}</div>}
            <div style={{ display: 'flex', gap: 10 }}>
              <button
                type="button"
                className="button"
                onClick={() => setShowConfirm(false)}
                disabled={submitting}
              >
                Cancel
              </button>
              <button
                type="button"
                className="button"
                style={{ background: '#b91c1c', borderColor: '#b91c1c' }}
                onClick={handleRequestDeletion}
                disabled={submitting}
              >
                {submitting ? 'Submitting...' : 'Request Account Deletion'}
              </button>
            </div>
          </div>
        ) : (
          <div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>Delete Account</div>
            <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12 }}>
              Permanently delete your account and all associated data. This action cannot be undone.
            </p>
            <button
              type="button"
              className="button"
              style={{ background: '#b91c1c', borderColor: '#b91c1c' }}
              onClick={() => setShowConfirm(true)}
              disabled={!verified}
            >
              Delete My Account
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
