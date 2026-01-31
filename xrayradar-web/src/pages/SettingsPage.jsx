import { useState, useEffect } from 'react'
import { fetchJson } from '../utils/api'
import { AccountInfoCard } from '../components/AccountInfoCard'
import { UsageDetailsCard } from '../components/UsageDetailsCard'
import { PlanDetailsCard } from '../components/PlanDetailsCard'
import { DeleteAccountCard } from '../components/DeleteAccountCard'

export function SettingsPage({ me }) {
  const [usage, setUsage] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchJson('/api/user/usage')
      .then((data) => {
        setUsage(data)
        setLoading(false)
      })
      .catch((e) => {
        setError(e.message || 'Failed to load usage')
        setLoading(false)
      })
  }, [])

  return (
    <div className="container" style={{ padding: '46px 0' }}>
      <div className="panel" style={{ padding: 18 }}>
        <div style={{ fontWeight: 900, letterSpacing: '-0.02em', fontSize: 22 }}>Account Settings</div>
        <div className="small" style={{ color: 'var(--muted)', marginTop: 8 }}>
          Manage your account and view usage
        </div>

        <AccountInfoCard me={me} />
        <UsageDetailsCard usage={usage} loading={loading} error={error} />
        <PlanDetailsCard me={me} />
        <DeleteAccountCard me={me} />
      </div>
    </div>
  )
}
