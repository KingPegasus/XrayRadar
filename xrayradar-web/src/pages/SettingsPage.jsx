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
    <div className="container page">
      <header className="pageHeader">
        <h1 className="pageTitle">Account Settings</h1>
        <p className="pageSubtitle">
          Manage your account and view usage
        </p>
      </header>

      <AccountInfoCard me={me} />
      <UsageDetailsCard usage={usage} loading={loading} error={error} />
      <PlanDetailsCard me={me} />
      <DeleteAccountCard me={me} />
    </div>
  )
}
