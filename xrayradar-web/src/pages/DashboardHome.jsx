import { useState, useCallback, useEffect, useMemo } from 'react'
import { fetchJson } from '../utils/api'
import { Link } from '../components/Link'
import { EventFrequencyChart } from '../components/EventFrequencyChart'

export function DashboardHome({ me }) {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setError('')
    try {
      const data = await fetchJson('/api/user/dashboard/stats')
      setStats(data)
    } catch (e) {
      setError(e.message || 'Failed to load dashboard stats')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  // Event frequency for chart: last 30 days on x-axis (zeros for days with no events), like Project Event Frequency
  const trendDailyForChart = useMemo(() => {
    if (!stats) return null
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
    const trendDaily = stats.trend_daily || {}
    const data = last30Days.map((dateKey) => [dateKey, trendDaily[dateKey] ?? 0])
    const counts = data.map(([, c]) => c)
    const maxCount = counts.length > 0 ? Math.max(...counts) : 1
    const total = stats.totals?.last_30d ?? 0
    return { data, maxCount, total }
  }, [stats])

  const trendClass = (direction) => {
    if (direction === 'up') return 'dashboardTrendValue--up'
    if (direction === 'down') return 'dashboardTrendValue--down'
    return 'dashboardTrendValue--same'
  }

  return (
    <main className="dashboardPage">
      <div className="container">
        <header className="dashboardHeader">
          <h1 className="dashboardTitle">Error overview</h1>
          <p className="dashboardSubtitle">
            Signed in as <code>{me?.email}</code>
          </p>
        </header>

        {loading && (
          <div className="dashboardLoading">
            <div className="dashboardLoadingDots" aria-hidden>
              <span />
              <span />
              <span />
            </div>
            <span>Loading stats…</span>
          </div>
        )}

        {error && (
          <div className="dashboardErrorCard">
            <p style={{ margin: 0, color: 'rgba(255,255,255,0.9)' }}>{error}</p>
            <button type="button" className="button" style={{ marginTop: 12 }} onClick={load}>
              Retry
            </button>
          </div>
        )}

        {!loading && !error && stats && (
          <>
            <h2 className="dashboardSectionTitle">Summary</h2>
            <div className="dashboardStatsGrid">
              <div className="dashboardStatCard">
                <div className="dashboardStatLabel">Errors (24h)</div>
                <div className="dashboardStatValue">{stats.totals?.last_24h ?? 0}</div>
              </div>
              <div className="dashboardStatCard">
                <div className="dashboardStatLabel">Errors (7d)</div>
                <div className="dashboardStatValue">{stats.totals?.last_7d ?? 0}</div>
              </div>
              <div className="dashboardStatCard">
                <div className="dashboardStatLabel">Errors (30d)</div>
                <div className="dashboardStatValue">{stats.totals?.last_30d ?? 0}</div>
              </div>
              <div className="dashboardStatCard">
                <div className="dashboardStatLabel">Unique issues (30d)</div>
                <div className="dashboardStatValue">{stats.unique_issues?.last_30d ?? 0}</div>
              </div>
            </div>

            <div className="dashboardTrendRow">
              {stats.trend_7d && (
                <div className="dashboardTrendCard">
                  <span className="dashboardTrendLabel">7d trend</span>
                  <span className={`dashboardTrendValue ${trendClass(stats.trend_7d.direction)}`}>
                    {stats.trend_7d.direction === 'up' && '↑ '}
                    {stats.trend_7d.direction === 'down' && '↓ '}
                    {stats.trend_7d.percent_change > 0 ? '+' : ''}{stats.trend_7d.percent_change}%
                  </span>
                </div>
              )}
              {stats.trend_30d && (
                <div className="dashboardTrendCard">
                  <span className="dashboardTrendLabel">30d trend</span>
                  <span className={`dashboardTrendValue ${trendClass(stats.trend_30d.direction)}`}>
                    {stats.trend_30d.direction === 'up' && '↑ '}
                    {stats.trend_30d.direction === 'down' && '↓ '}
                    {stats.trend_30d.percent_change > 0 ? '+' : ''}{stats.trend_30d.percent_change}%
                  </span>
                </div>
              )}
            </div>

            {trendDailyForChart && trendDailyForChart.data.length > 0 && (
              <div className="dashboardChartCard">
                <h2 className="dashboardSectionTitle">Event frequency (30d)</h2>
                <EventFrequencyChart eventFrequency={trendDailyForChart} showTitle={false} />
              </div>
            )}

            {stats.top_5_errors && stats.top_5_errors.length > 0 && (
              <div className="dashboardTopErrorsCard">
                <h2 className="dashboardSectionTitle">Top 5 errors (30d)</h2>
                <ul className="dashboardTopErrorsList">
                  {stats.top_5_errors.map((err, idx) => (
                    <li key={err.fingerprint + String(err.project_id)}>
                      <Link
                        to={`/dashboard/projects/${err.project_id}/issues/${err.fingerprint}`}
                        className="dashboardTopErrorItem"
                      >
                        <span className="dashboardTopErrorRank">{idx + 1}</span>
                        <div className="dashboardTopErrorContent">
                          <div className="dashboardTopErrorMessage" title={err.message || '(no message)'}>
                            {err.message || '(no message)'}
                          </div>
                          <div className="dashboardTopErrorMeta">
                            {err.project_name} · last 30 days
                          </div>
                        </div>
                        <span className="dashboardTopErrorCount">
                          {err.count} event{err.count !== 1 ? 's' : ''}
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {!loading && !error && stats && stats.totals?.last_30d === 0 && (
              <div className="dashboardEmptyCard card">
                <div className="cardTitle">Getting started</div>
                <p className="cardText">
                  Set up your first project in three steps.
                </p>
                <ol className="cardText" style={{ marginTop: 10, marginBottom: 0, paddingLeft: 18 }}>
                  <li>Create a project in Projects.</li>
                  <li>Request a token from an admin in Tokens.</li>
                  <li>Assign token access to your project from Tokens.</li>
                </ol>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12 }}>
                  <Link to="/dashboard/projects" className="button" style={{ display: 'inline-block' }}>
                    Create project
                  </Link>
                  <Link to="/dashboard/tokens" className="button" style={{ display: 'inline-block' }}>
                    Request and assign token
                  </Link>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </main>
  )
}
