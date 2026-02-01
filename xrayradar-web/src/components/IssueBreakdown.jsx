/**
 * Shows event counts by release (app version) and by environment for an issue.
 * Helps answer "which versions/environments is this error affecting?"
 */
export function IssueBreakdown({ byRelease = [], byEnvironment = [] }) {
  const hasRelease = Array.isArray(byRelease) && byRelease.length > 0
  const hasEnv = Array.isArray(byEnvironment) && byEnvironment.length > 0
  if (!hasRelease && !hasEnv) return null

  const label = (v) => (v == null || v === '' ? '(not set)' : String(v))
  const maxRelease = hasRelease ? Math.max(...byRelease.map((r) => r.count || 0), 1) : 1
  const maxEnv = hasEnv ? Math.max(...byEnvironment.map((e) => e.count || 0), 1) : 1

  return (
    <div className="issueBreakdown">
      {hasRelease && (
        <div className="issueBreakdownSection">
          <h3 className="issueBreakdownTitle">Affected releases (last 30 days)</h3>
          <p className="issueBreakdownDesc">Which app versions this issue came from</p>
          <div className="issueBreakdownBars">
            {byRelease.map(({ release, count }, idx) => (
              <div key={`release-${idx}-${release ?? 'null'}`} className="issueBreakdownRow">
                <span className="issueBreakdownLabel" title={label(release)}>
                  {label(release)}
                </span>
                <div className="issueBreakdownBarWrap">
                  <div
                    className="issueBreakdownBar"
                    style={{
                      width: `${Math.round(((count || 0) / maxRelease) * 100)}%`,
                    }}
                    role="img"
                    aria-label={`${label(release)}: ${count} events`}
                  />
                </div>
                <span className="issueBreakdownCount">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      {hasEnv && (
        <div className="issueBreakdownSection">
          <h3 className="issueBreakdownTitle">Environments</h3>
          <p className="issueBreakdownDesc">Where this issue occurred</p>
          <div className="issueBreakdownBars">
            {byEnvironment.map(({ environment, count }, idx) => (
              <div key={`env-${idx}-${environment ?? 'null'}`} className="issueBreakdownRow">
                <span className="issueBreakdownLabel" title={label(environment)}>
                  {label(environment)}
                </span>
                <div className="issueBreakdownBarWrap">
                  <div
                    className="issueBreakdownBar issueBreakdownBar--env"
                    style={{
                      width: `${Math.round(((count || 0) / maxEnv) * 100)}%`,
                    }}
                    role="img"
                    aria-label={`${label(environment)}: ${count} events`}
                  />
                </div>
                <span className="issueBreakdownCount">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
