import { useState, useEffect } from 'react'
import { fetchJson } from '../utils/api'

export function EmailAlertSettings({ projectId, me, compact = false }) {
  const [alertEnabled, setAlertEnabled] = useState(false)
  const [alertCooldown, setAlertCooldown] = useState('')
  const [minCooldownMinutes, setMinCooldownMinutes] = useState(null) // null = Free (no alerts) or not loaded
  const [additionalEmails, setAdditionalEmails] = useState([])
  const [newEmail, setNewEmail] = useState('')
  const [alertSaveBusy, setAlertSaveBusy] = useState(false)
  const [alertSaveError, setAlertSaveError] = useState('')
  const [alertSaveSuccess, setAlertSaveSuccess] = useState('')
  const [settingsLoaded, setSettingsLoaded] = useState(false)

  useEffect(() => {
    setSettingsLoaded(false)
    fetchJson(`/api/user/projects/${projectId}/alert-settings`)
      .then((data) => {
        setAlertEnabled(data?.enabled ?? false)
        const min = data?.min_cooldown_minutes ?? null
        setMinCooldownMinutes(min)
        const stored = data?.cooldown_minutes
        if (stored == null) {
          setAlertCooldown('')
        } else {
          const effective = min != null && stored < min ? min : stored
          setAlertCooldown(String(effective))
        }
        setAdditionalEmails(data?.additional_emails ?? [])
        setSettingsLoaded(true)
      })
      .catch((e) => {
        console.warn('Failed to load alert settings:', e)
        setSettingsLoaded(true)
      })
  }, [projectId])

  const isFreePlan = settingsLoaded && minCooldownMinutes === null

  if (!settingsLoaded) {
    return (
      <div style={compact ? {} : { marginTop: 20, marginBottom: 20 }}>
        {!compact && (
          <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 10, color: '#cbd5e1' }}>Email alerts</div>
        )}
        <div style={{ background: compact ? 'transparent' : 'rgba(0, 0, 0, 0.2)', padding: compact ? 0 : 16, borderRadius: compact ? 0 : 8, border: compact ? 'none' : '1px solid rgba(255,255,255,0.1)' }}>
          <p className="small" style={{ color: 'var(--muted)' }}>Loading…</p>
        </div>
      </div>
    )
  }

  if (isFreePlan) {
    return (
      <div style={compact ? {} : { marginTop: 20, marginBottom: 20 }}>
        {!compact && (
          <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 10, color: '#cbd5e1' }}>Email alerts</div>
        )}
        <div style={{ background: compact ? 'transparent' : 'rgba(0, 0, 0, 0.2)', padding: compact ? 0 : 16, borderRadius: compact ? 0 : 8, border: compact ? 'none' : '1px solid rgba(255,255,255,0.1)' }}>
          <p className="small" style={{ color: 'var(--muted)', marginBottom: 12 }}>
            Email alerts are not available on the Free plan. Upgrade to Basic, Teams, or Teams Pro to get notified when errors occur.
          </p>
          <a
            href={`mailto:dev@xrayradar.com?subject=Upgrade%20to%20Basic%20Plan&body=Hi,%0A%0AI'd%20like%20to%20upgrade%20my%20XrayRadar%20account.%0A%0AEmail:%20${encodeURIComponent(me?.email || '')}%0A%0AThanks!`}
            className="button buttonPrimary"
            style={{ display: 'inline-block' }}
          >
            Contact to Upgrade
          </a>
        </div>
      </div>
    )
  }

  return (
    <div style={compact ? {} : { marginTop: 20, marginBottom: 20 }}>
      {!compact && (
        <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 10, color: '#cbd5e1' }}>Email alerts</div>
      )}
      <div style={{ background: compact ? 'transparent' : 'rgba(0, 0, 0, 0.2)', padding: compact ? 0 : 16, borderRadius: compact ? 0 : 8, border: compact ? 'none' : '1px solid rgba(255,255,255,0.1)' }}>
        <p className="small" style={{ color: 'var(--muted)', marginBottom: 12 }}>
          Project owner (you) will receive alerts. Add additional emails below.
        </p>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <input
            type="checkbox"
            checked={alertEnabled}
            onChange={(e) => setAlertEnabled(e.target.checked)}
          />
          <span>Email alerts for errors</span>
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <span style={{ minWidth: 140 }}>Cooldown (minutes)</span>
          <input
            type="number"
            className="fieldInput"
            style={{ width: 80 }}
            min={minCooldownMinutes ?? 10}
            placeholder="None"
            value={alertCooldown}
            onChange={(e) => setAlertCooldown(e.target.value)}
          />
          <span className="small" style={{ color: 'var(--muted)' }}>
            {minCooldownMinutes != null
              ? `Minimum ${minCooldownMinutes} minute${minCooldownMinutes === 1 ? '' : 's'} for your plan. `
              : ''}
          </span>
        </label>
        <div style={{ marginBottom: 12 }}>
          <div style={{ marginBottom: 6, fontSize: 13 }}>Additional emails</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
            {additionalEmails.map((email, i) => (
              <span
                key={i}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 4,
                  padding: '4px 8px',
                  background: 'rgba(255,255,255,0.1)',
                  borderRadius: 6,
                  fontSize: 13,
                }}
              >
                {email}
                <button
                  type="button"
                  aria-label={`Remove ${email}`}
                  style={{ background: 'none', border: 'none', color: 'var(--muted)', cursor: 'pointer', padding: 0, fontSize: 16, lineHeight: 1 }}
                  onClick={() => setAdditionalEmails(additionalEmails.filter((_, j) => j !== i))}
                >
                  ×
                </button>
              </span>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              type="email"
              className="fieldInput"
              style={{ flex: 1, maxWidth: 280 }}
              placeholder="Add email"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  const v = newEmail.trim().toLowerCase()
                  if (v && !additionalEmails.includes(v)) {
                    setAdditionalEmails([...additionalEmails, v])
                    setNewEmail('')
                  }
                }
              }}
            />
            <button
              type="button"
              className="button"
              onClick={() => {
                const v = newEmail.trim().toLowerCase()
                if (v && !additionalEmails.includes(v)) {
                  setAdditionalEmails([...additionalEmails, v])
                  setNewEmail('')
                }
              }}
            >
              Add
            </button>
          </div>
        </div>
        {alertSaveError ? (
          <div className="fieldError" style={{ marginBottom: 10 }}>{alertSaveError}</div>
        ) : null}
        {alertSaveSuccess ? (
          <div className="small" style={{ marginBottom: 10, color: '#86efac' }}>{alertSaveSuccess}</div>
        ) : null}
        {!me?.email_verified && (
          <div className="small" style={{ marginBottom: 10, color: '#fbbf24' }}>
            Verify your email to save alert settings.
          </div>
        )}
        <button
          type="button"
          className="button buttonPrimary"
          disabled={alertSaveBusy || !me?.email_verified}
          onClick={async () => {
            setAlertSaveError('')
            setAlertSaveSuccess('')
            const cooldown = alertCooldown.trim() === '' ? null : parseInt(alertCooldown, 10)
            const cooldownNum = cooldown != null && !isNaN(cooldown) ? cooldown : null
            if (cooldownNum != null && cooldownNum > 0 && minCooldownMinutes != null && cooldownNum < minCooldownMinutes) {
              setAlertSaveError(`Cooldown minimum for your plan is ${minCooldownMinutes} minutes.`)
              return
            }
            setAlertSaveBusy(true)
            try {
              await fetchJson(`/api/user/projects/${projectId}/alert-settings`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  enabled: alertEnabled,
                  cooldown_minutes: cooldownNum,
                  additional_emails: additionalEmails,
                }),
              })
              setAlertSaveSuccess('Alert settings saved.')
            } catch (e) {
              setAlertSaveError(e.message || e.detail || 'Failed to save')
            } finally {
              setAlertSaveBusy(false)
            }
          }}
        >
          {alertSaveBusy ? 'Saving…' : 'Save alert settings'}
        </button>
      </div>
    </div>
  )
}
