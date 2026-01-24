import { useState, useEffect } from 'react'
import { fetchJson } from '../utils/api'
import { navigate } from '../utils/navigation'

export function ProjectIssuesPage({ projectId }) {
  const [issues, setIssues] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    setError('')
    fetchJson(`/api/user/projects/${projectId}/issues`)
      .then((rows) => setIssues(rows || []))
      .catch((e) => setError(e.message || 'Failed to load issues'))
  }, [projectId])

  return (
    <div className="container" style={{ padding: '46px 0' }}>
      <div className="panel" style={{ padding: 18 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontWeight: 900, letterSpacing: '-0.02em', fontSize: 22 }}>Project {projectId}</div>
            <div className="small" style={{ color: 'var(--muted)', marginTop: 8 }}>
              Issues are grouped by fingerprint.
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button className="button" type="button" onClick={() => navigate('/dashboard')}>
              Back
            </button>
          </div>
        </div>

        {error ? (
          <div className="fieldError" role="alert" style={{ marginTop: 10 }}>
            {error}
          </div>
        ) : null}

        <div style={{ marginTop: 14 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ color: 'var(--muted)', fontSize: 13 }}>
                <th style={{ textAlign: 'left', padding: '8px 6px' }}>First seen</th>
                <th style={{ textAlign: 'left', padding: '8px 6px' }}>Last seen</th>
                <th style={{ textAlign: 'left', padding: '8px 6px' }}>Count</th>
                <th style={{ textAlign: 'left', padding: '8px 6px' }}>Level</th>
                <th style={{ textAlign: 'left', padding: '8px 6px' }}>Message</th>
              </tr>
            </thead>
            <tbody>
              {issues.map((it) => (
                <tr
                  key={it.fingerprint}
                  style={{ cursor: 'pointer', borderTop: '1px solid rgba(255,255,255,0.08)' }}
                  onClick={() => navigate(`/dashboard/projects/${projectId}/issues/${it.fingerprint}`)}
                >
                  <td style={{ padding: '10px 6px', fontSize: 13 }}>{new Date(it.first_seen).toLocaleString()}</td>
                  <td style={{ padding: '10px 6px', fontSize: 13 }}>{new Date(it.last_seen).toLocaleString()}</td>
                  <td style={{ padding: '10px 6px', fontSize: 13 }}>{it.count}</td>
                  <td style={{ padding: '10px 6px', fontSize: 13 }}>{it.level}</td>
                  <td style={{ padding: '10px 6px', fontSize: 13, color: 'var(--text)' }}>{it.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
