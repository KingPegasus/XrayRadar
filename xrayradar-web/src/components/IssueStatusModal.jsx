import { useState } from 'react'
import { updateIssueStatus } from '../utils/api'
import { IssueStatusBadge } from './IssueStatusBadge'

export function IssueStatusModal({ projectId, fingerprint, currentStatus, resolvedRelease, resolvedAt, onStatusChange, onClose }) {
  const [status, setStatus] = useState(currentStatus || 'open')
  const [resolvedReleaseInput, setResolvedReleaseInput] = useState(resolvedRelease || '')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showNotes, setShowNotes] = useState(false)

  const handleSave = async () => {
    setError('')
    setLoading(true)
    try {
      const statusData = {
        status,
        resolved_release: status === 'resolved' ? resolvedReleaseInput || null : null,
        notes: notes || null,
      }
      const result = await updateIssueStatus(projectId, fingerprint, statusData)
      if (onStatusChange) {
        onStatusChange(result)
      }
      onClose()
    } catch (e) {
      setError(e.message || 'Failed to update status')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="status-modal-title"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(0,0,0,0.6)',
        padding: 24,
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div
        style={{
          background: 'var(--panel-bg, #1e293b)',
          borderRadius: 12,
          border: '1px solid rgba(255,255,255,0.1)',
          maxWidth: 400,
          width: '100%',
          padding: 20,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 id="status-modal-title" style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>Update Issue Status</h3>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--muted)',
              cursor: 'pointer',
              padding: 4,
              fontSize: 24,
              lineHeight: 1,
            }}
          >
            ×
          </button>
        </div>

        <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 13, color: 'var(--muted)' }}>Current:</span>
          <IssueStatusBadge status={currentStatus || 'open'} resolvedRelease={resolvedRelease} />
        </div>

        {currentStatus === 'resolved' && resolvedAt && (
          <div style={{ marginBottom: 16, padding: 8, background: 'rgba(255,255,255,0.05)', borderRadius: 6, fontSize: 12, color: 'var(--muted)' }}>
            {resolvedRelease && <div>Resolved in release: <strong>{resolvedRelease}</strong></div>}
            <div>Resolved on: {new Date(resolvedAt).toLocaleString()}</div>
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--muted)', marginBottom: 6 }}>
              Status
            </label>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {['open', 'in_progress', 'resolved', 'ignored'].map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setStatus(s)}
                  disabled={loading}
                  style={{
                    padding: '6px 12px',
                    fontSize: 12,
                    fontWeight: status === s ? 600 : 400,
                    border: `1px solid ${status === s ? 'rgba(79, 124, 255, 0.5)' : 'rgba(255,255,255,0.1)'}`,
                    borderRadius: 6,
                    background: status === s ? 'rgba(79, 124, 255, 0.15)' : 'rgba(255,255,255,0.05)',
                    color: 'var(--text)',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    opacity: loading ? 0.5 : 1,
                  }}
                >
                  {s === 'in_progress' ? 'In Progress' : s.charAt(0).toUpperCase() + s.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {status === 'resolved' && (
            <div>
              <label htmlFor="resolved-release" style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--muted)', marginBottom: 6 }}>
                Resolve until release (optional)
              </label>
              <input
                id="resolved-release"
                type="text"
                value={resolvedReleaseInput}
                onChange={(e) => setResolvedReleaseInput(e.target.value)}
                placeholder="e.g., v1.2.3"
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '8px 10px',
                  fontSize: 13,
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: 6,
                  background: 'rgba(255,255,255,0.05)',
                  color: 'var(--text)',
                }}
              />
              <small style={{ display: 'block', marginTop: 4, fontSize: 11, color: 'var(--muted)' }}>
                Auto-reopens if issue occurs in a different release
              </small>
            </div>
          )}

          <div>
            {!showNotes ? (
              <button
                type="button"
                onClick={() => setShowNotes(true)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--muted)',
                  cursor: 'pointer',
                  fontSize: 12,
                  padding: 0,
                  textDecoration: 'underline',
                }}
              >
                + Add notes (optional)
              </button>
            ) : (
              <div>
                <label htmlFor="status-notes" style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--muted)', marginBottom: 6 }}>
                  Notes
                </label>
                <textarea
                  id="status-notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add notes about this status change..."
                  rows={2}
                  disabled={loading}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    fontSize: 13,
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 6,
                    background: 'rgba(255,255,255,0.05)',
                    color: 'var(--text)',
                    resize: 'vertical',
                    fontFamily: 'inherit',
                  }}
                />
              </div>
            )}
          </div>

          {error && (
            <div className="fieldError" role="alert" style={{ fontSize: 12, padding: 8 }}>
              {error}
            </div>
          )}

          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 8 }}>
            <button
              className="button"
              type="button"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              className="button button-primary"
              type="button"
              onClick={handleSave}
              disabled={loading || status === currentStatus}
            >
              {loading ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
