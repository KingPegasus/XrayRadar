import { parseCooldownValue } from '../utils/emailAlertSettingsUtils'

export function EnvironmentAlertOverrides({
  knownEnvNames,
  envByName,
  minCooldownMinutes,
  projectName,
  newEnvEmailByEnv,
  setNewEnvEmailByEnv,
  updateEnv,
  addEnvEmail,
  setEnvironmentSettings,
}) {
  return (
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
  )
}
