import { useState, useEffect } from 'react'
import { fetchJson } from '../utils/api'

function normalizeEmailList(items) {
  const seen = new Set()
  const out = []
  for (const item of Array.isArray(items) ? items : []) {
    const value = String(item || '').trim().toLowerCase()
    if (!value || seen.has(value)) continue
    seen.add(value)
    out.push(value)
  }
  return out
}

function normalizeEnvSettings(items) {
  const out = []
  for (const item of Array.isArray(items) ? items : []) {
    const environment = String(item?.environment || '').trim()
    if (!environment) continue
    out.push({
      environment,
      enabled: item?.enabled ?? true,
      cooldown_minutes: item?.cooldown_minutes == null ? null : Number(item.cooldown_minutes),
      additional_emails: normalizeEmailList(item?.additional_emails),
    })
  }
  return out.sort((a, b) => a.environment.localeCompare(b.environment))
}

function parseCooldownValue(raw) {
  const value = String(raw ?? '').trim()
  if (!value) return null
  const num = parseInt(value, 10)
  return Number.isNaN(num) ? null : num
}

export function EmailAlertSettings({ projectId, me, compact = false, projectName = 'Project' }) {
  const [alertEnabled, setAlertEnabled] = useState(false)
  const [alertCooldown, setAlertCooldown] = useState('')
  const [minCooldownMinutes, setMinCooldownMinutes] = useState(null)
  const [additionalEmails, setAdditionalEmails] = useState([])
  const [environmentSettings, setEnvironmentSettings] = useState([])
  const [environmentOptions, setEnvironmentOptions] = useState([])
  const [newEmail, setNewEmail] = useState('')
  const [newEnvEmailByEnv, setNewEnvEmailByEnv] = useState({})
  const [alertSaveBusy, setAlertSaveBusy] = useState(false)
  const [alertSaveError, setAlertSaveError] = useState('')
  const [alertSaveSuccess, setAlertSaveSuccess] = useState('')
  const [settingsLoaded, setSettingsLoaded] = useState(false)

  useEffect(() => {
    setSettingsLoaded(false)
    Promise.all([
      fetchJson(`/api/user/projects/${projectId}/alert-settings`),
      fetchJson(`/api/user/projects/${projectId}/environments`).catch(() => []),
    ])
      .then(([data, envRows]) => {
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
        setAdditionalEmails(normalizeEmailList(data?.additional_emails))
        setEnvironmentSettings(normalizeEnvSettings(data?.environment_settings))
        setEnvironmentOptions(
          (Array.isArray(envRows) ? envRows : [])
            .map((row) => String(row?.environment || '').trim())
            .filter(Boolean)
        )
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

  const knownEnvNames = Array.from(
    new Set([...environmentOptions, ...environmentSettings.map((item) => item.environment)])
  ).sort((a, b) => a.localeCompare(b))
  const envByName = new Map(environmentSettings.map((item) => [item.environment, item]))

  const updateEnv = (envName, updater) => {
    setEnvironmentSettings((prev) => {
      const next = [...prev]
      const idx = next.findIndex((item) => item.environment === envName)
      if (idx >= 0) {
        next[idx] = updater(next[idx])
      } else {
        next.push(
          updater({
            environment: envName,
            enabled: true,
            cooldown_minutes: null,
            additional_emails: [],
          })
        )
      }
      return next.sort((a, b) => a.environment.localeCompare(b.environment))
    })
  }

  const addProjectEmail = () => {
    const value = String(newEmail || '').trim().toLowerCase()
    if (!value) return
    setAdditionalEmails((prev) => normalizeEmailList([...prev, value]))
    setNewEmail('')
  }

  const addEnvEmail = (envName) => {
    const value = String(newEnvEmailByEnv[envName] || '').trim().toLowerCase()
    if (!value) return
    updateEnv(envName, (row) => ({
      ...row,
      additional_emails: normalizeEmailList([...(row.additional_emails || []), value]),
    }))
    setNewEnvEmailByEnv((prev) => ({ ...prev, [envName]: '' }))
  }

  return (
    <div style={compact ? {} : { marginTop: 20, marginBottom: 20 }}>
      {!compact && (
        <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 10, color: '#cbd5e1' }}>Email alerts</div>
      )}
      <div style={{ background: compact ? 'transparent' : 'rgba(0, 0, 0, 0.2)', padding: compact ? 0 : 16, borderRadius: compact ? 0 : 8, border: compact ? 'none' : '1px solid rgba(255,255,255,0.1)' }}>
        <p className="small" style={{ color: 'var(--muted)', marginBottom: 12 }}>
          Configure where digest emails go and how often they send.
        </p>

        <div style={{ marginBottom: 14, padding: '10px 12px', borderRadius: 8, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Project-wide alerts (all events)</div>
          <div className="small" style={{ color: 'var(--muted)' }}>
            Sends: [XrayRadar] {projectName}: Error digest
          </div>
        </div>

        <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <input type="checkbox" checked={alertEnabled} onChange={(e) => setAlertEnabled(e.target.checked)} />
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
        <div style={{ marginBottom: 16 }}>
          <div style={{ marginBottom: 6, fontSize: 13 }}>Additional emails</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
            {additionalEmails.map((email, i) => (
              <span
                key={`${email}-${i}`}
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
                  addProjectEmail()
                }
              }}
            />
            <button type="button" className="button" onClick={addProjectEmail}>Add</button>
          </div>
        </div>

        <div style={{ marginBottom: 18 }}>
          <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Environment-specific alerts</div>
          <div className="small" style={{ color: 'var(--muted)', marginBottom: 10 }}>
            These overrides send emails with an environment tag in the subject.
          </div>
          {knownEnvNames.length === 0 ? (
            <div className="small" style={{ color: 'var(--muted)' }}>No environments detected yet.</div>
          ) : (
            knownEnvNames.map((envName) => {
              const envSettings = envByName.get(envName) || {
                environment: envName,
                enabled: false,
                cooldown_minutes: null,
                additional_emails: [],
              }
              return (
                <div
                  key={envName}
                  style={{
                    marginBottom: 10,
                    padding: 10,
                    borderRadius: 8,
                    border: '1px solid rgba(255,255,255,0.12)',
                    background: 'rgba(0,0,0,0.12)',
                  }}
                >
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <input
                      type="checkbox"
                      checked={!!envSettings.enabled}
                      onChange={(e) => updateEnv(envName, (row) => ({ ...row, enabled: e.target.checked }))}
                    />
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{envName}</span>
                  </label>
                  <div className="small" style={{ color: 'var(--muted)', marginBottom: 8 }}>
                    Sends: [XrayRadar] [{envName}] {projectName}: Error digest
                  </div>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <span style={{ minWidth: 140 }}>Cooldown (minutes)</span>
                    <input
                      type="number"
                      className="fieldInput"
                      style={{ width: 80 }}
                      min={minCooldownMinutes ?? 10}
                      placeholder="Default"
                      value={envSettings.cooldown_minutes == null ? '' : String(envSettings.cooldown_minutes)}
                      onChange={(e) => updateEnv(envName, (row) => ({ ...row, cooldown_minutes: parseCooldownValue(e.target.value) }))}
                    />
                  </label>
                  <div style={{ marginBottom: 8 }}>
                    <div style={{ marginBottom: 6, fontSize: 13 }}>Additional emails</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
                      {(envSettings.additional_emails || []).map((email, i) => (
                        <span
                          key={`${envName}-${email}-${i}`}
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
                            aria-label={`Remove ${email} from ${envName}`}
                            style={{ background: 'none', border: 'none', color: 'var(--muted)', cursor: 'pointer', padding: 0, fontSize: 16, lineHeight: 1 }}
                            onClick={() => {
                              updateEnv(envName, (row) => ({
                                ...row,
                                additional_emails: (row.additional_emails || []).filter((_, j) => j !== i),
                              }))
                            }}
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
                        placeholder={`Add email for ${envName}`}
                        value={newEnvEmailByEnv[envName] || ''}
                        onChange={(e) => setNewEnvEmailByEnv((prev) => ({ ...prev, [envName]: e.target.value }))}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault()
                            addEnvEmail(envName)
                          }
                        }}
                      />
                      <button type="button" className="button" onClick={() => addEnvEmail(envName)}>Add</button>
                    </div>
                  </div>
                  <button
                    type="button"
                    className="button"
                    onClick={() => setEnvironmentSettings((prev) => prev.filter((item) => item.environment !== envName))}
                  >
                    Remove environment override
                  </button>
                </div>
              )
            })
          )}
        </div>

        {alertSaveError ? <div className="fieldError" style={{ marginBottom: 10 }}>{alertSaveError}</div> : null}
        {alertSaveSuccess ? <div className="small" style={{ marginBottom: 10, color: '#86efac' }}>{alertSaveSuccess}</div> : null}
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
            const cooldownNum = parseCooldownValue(alertCooldown)
            if (cooldownNum != null && cooldownNum > 0 && minCooldownMinutes != null && cooldownNum < minCooldownMinutes) {
              setAlertSaveError(`Cooldown minimum for your plan is ${minCooldownMinutes} minutes.`)
              return
            }
            for (const envSetting of environmentSettings) {
              const envCooldown = envSetting.cooldown_minutes
              if (envCooldown != null && envCooldown > 0 && minCooldownMinutes != null && envCooldown < minCooldownMinutes) {
                setAlertSaveError(`Cooldown minimum for your plan is ${minCooldownMinutes} minutes.`)
                return
              }
            }
            setAlertSaveBusy(true)
            try {
              await fetchJson(`/api/user/projects/${projectId}/alert-settings`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  enabled: alertEnabled,
                  cooldown_minutes: cooldownNum,
                  additional_emails: normalizeEmailList(additionalEmails),
                  environment_settings: environmentSettings.map((item) => ({
                    environment: item.environment,
                    enabled: !!item.enabled,
                    cooldown_minutes: item.cooldown_minutes,
                    additional_emails: normalizeEmailList(item.additional_emails),
                  })),
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
