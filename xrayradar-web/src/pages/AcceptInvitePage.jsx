import { useEffect, useState } from 'react'
import { fetchJson } from '../utils/api'
import { navigate } from '../utils/navigation'

export function AcceptInvitePage({ token, onSuccess }) {
  const [status, setStatus] = useState('loading') // loading | ok | error
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!token) {
      setStatus('error')
      setMessage('Invalid invite link: missing token')
      return
    }
    fetchJson('/api/user/team/invites/accept', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token }),
    })
      .then(() => {
        setStatus('ok')
        if (typeof onSuccess === 'function') onSuccess()
        else navigate('/dashboard')
      })
      .catch((e) => {
        setStatus('error')
        setMessage(e.message || 'Failed to accept invite')
      })
  }, [token, onSuccess])

  if (status === 'loading') {
    return (
      <div className="container page">
        <p>Accepting invite…</p>
      </div>
    )
  }
  if (status === 'error') {
    return (
      <div className="container page">
        <div className="fieldError" role="alert">{message}</div>
        <p><a href="/dashboard">Go to dashboard</a></p>
      </div>
    )
  }
  return (
    <div className="container page">
      <p>Invite accepted. Redirecting…</p>
    </div>
  )
}
