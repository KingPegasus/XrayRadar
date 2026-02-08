import { useState, useEffect } from 'react'
import { fetchJson } from '../utils/api'
import { EmailAlertSettings } from './EmailAlertSettings'

export function ProjectSettingsModal({ projectId, me, projectName, isOwner, onProjectNameUpdated }) {
  const [open, setOpen] = useState(false)
  const [nameValue, setNameValue] = useState(projectName ?? '')
  const [nameError, setNameError] = useState('')
  const [nameSaving, setNameSaving] = useState(false)

  useEffect(() => {
    if (open) {
      setNameValue(projectName ?? '')
      setNameError('')
    }
  }, [open, projectName])

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        title="Project settings"
        aria-label="Project settings"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 36,
          height: 36,
          padding: 0,
          border: '1px solid rgba(255,255,255,0.2)',
          borderRadius: 8,
          background: 'rgba(0,0,0,0.2)',
          color: 'var(--text)',
          cursor: 'pointer',
        }}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
      </button>

      {open && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="settings-modal-title"
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
          onClick={(e) => { if (e.target === e.currentTarget) setOpen(false) }}
        >
          <div
            style={{
              background: 'var(--panel-bg, #1e293b)',
              borderRadius: 12,
              border: '1px solid rgba(255,255,255,0.1)',
              maxWidth: 480,
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: 20,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2 id="settings-modal-title" style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>Project settings</h2>
              <button
                type="button"
                onClick={() => setOpen(false)}
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

            {isOwner && (
              <div style={{ marginBottom: 20 }}>
                <label className="fieldLabel" htmlFor="project-name-input">Project name</label>
                <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start', marginTop: 6 }}>
                  <input
                    id="project-name-input"
                    className="fieldInput"
                    type="text"
                    value={nameValue}
                    onChange={(e) => setNameValue(e.target.value)}
                    placeholder="Project name"
                    disabled={nameSaving}
                    style={{ flex: 1 }}
                  />
                  <button
                    type="button"
                    className="button buttonPrimary"
                    disabled={nameSaving || (nameValue.trim() === (projectName ?? '').trim())}
                    onClick={async () => {
                      const trimmed = nameValue.trim()
                      if (!trimmed) {
                        setNameError('Name is required')
                        return
                      }
                      setNameError('')
                      setNameSaving(true)
                      try {
                        const updated = await fetchJson(`/api/user/projects/${projectId}`, {
                          method: 'PATCH',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ name: trimmed }),
                        })
                        onProjectNameUpdated?.(updated.name)
                      } catch (e) {
                        setNameError(e.message || 'Failed to update name')
                      } finally {
                        setNameSaving(false)
                      }
                    }}
                  >
                    {nameSaving ? 'Saving…' : 'Save'}
                  </button>
                </div>
                {nameError ? (
                  <div className="fieldError" role="alert" style={{ marginTop: 6 }}>{nameError}</div>
                ) : null}
              </div>
            )}

            <EmailAlertSettings projectId={projectId} me={me} compact />
          </div>
        </div>
      )}
    </>
  )
}
