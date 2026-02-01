import { useState, useEffect } from 'react'
import { navigate } from '../utils/navigation'

export function VerifyEmailPage({ onVerified }) {
  const [status, setStatus] = useState('verifying')
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
    <div className="page" style={{ minHeight: '80vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <div className="container pageNarrow">
        <div className="pageCard" style={{ textAlign: 'center', padding: 32 }}>
          {status === 'verifying' && (
            <>
              <h1 className="pageTitle" style={{ fontSize: 20 }}>Verifying your email…</h1>
              <p className="pageEmpty" style={{ marginTop: 8 }}>Please wait</p>
            </>
          )}
          {status === 'success' && (
            <>
              <div style={{ fontSize: 48, marginBottom: 16, color: '#10b981' }}>✓</div>
              <h1 className="pageTitle" style={{ fontSize: 20, color: '#86efac' }}>Email Verified!</h1>
              <p className="pageSubtitle" style={{ marginTop: 8, marginBottom: 20 }}>{message}</p>
              <div className="pageActions" style={{ justifyContent: 'center' }}>
                <button type="button" className="button buttonPrimary" onClick={() => navigate('/dashboard')}>
                  Go to Dashboard
                </button>
              </div>
            </>
          )}
          {status === 'error' && (
            <>
              <div style={{ fontSize: 48, marginBottom: 16, color: '#ef4444' }}>✗</div>
              <h1 className="pageTitle" style={{ fontSize: 20, color: '#fca5a5' }}>Verification Failed</h1>
              <p className="pageSubtitle" style={{ marginTop: 8, marginBottom: 20 }}>{message}</p>
              <div className="pageActions" style={{ justifyContent: 'center' }}>
                <button type="button" className="button" onClick={() => navigate('/dashboard')}>
                  Go to Dashboard
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
