import { useState, useEffect } from 'react'
import { navigate } from '../utils/navigation'

export function VerifyEmailPage({ onVerified }) {
  const [status, setStatus] = useState('verifying') // verifying, success, error
  const [message, setMessage] = useState('')

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')

    if (!token) {
      setStatus('error')
      setMessage('No verification token provided.')
      return
    }

    fetch(`/auth/verify-email?token=${encodeURIComponent(token)}`, {
      credentials: 'include',
    })
      .then(async (res) => {
        const data = await res.json()
        if (res.ok) {
          setStatus('success')
          setMessage(data.message || 'Email verified successfully!')
          // Refresh the user state so the banner disappears
          if (onVerified) onVerified()
        } else {
          setStatus('error')
          setMessage(data.detail || 'Verification failed.')
        }
      })
      .catch(() => {
        setStatus('error')
        setMessage('Network error. Please try again.')
      })
  }, [onVerified])

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 20 }}>
      <div className="panel" style={{ padding: 32, textAlign: 'center', maxWidth: 400 }}>
        {status === 'verifying' && (
          <>
            <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 12 }}>Verifying your email...</div>
            <div className="small" style={{ color: 'var(--muted)' }}>Please wait</div>
          </>
        )}
        {status === 'success' && (
          <>
            <div style={{ fontSize: 48, marginBottom: 16 }}>✓</div>
            <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 12, color: '#86efac' }}>Email Verified!</div>
            <div className="small" style={{ color: 'var(--muted)', marginBottom: 20 }}>{message}</div>
            <button
              type="button"
              className="button buttonPrimary"
              onClick={() => navigate('/dashboard')}
            >
              Go to Dashboard
            </button>
          </>
        )}
        {status === 'error' && (
          <>
            <div style={{ fontSize: 48, marginBottom: 16 }}>✗</div>
            <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 12, color: '#fca5a5' }}>Verification Failed</div>
            <div className="small" style={{ color: 'var(--muted)', marginBottom: 20 }}>{message}</div>
            <button
              type="button"
              className="button"
              onClick={() => navigate('/dashboard')}
            >
              Go to Dashboard
            </button>
          </>
        )}
      </div>
    </div>
  )
}
