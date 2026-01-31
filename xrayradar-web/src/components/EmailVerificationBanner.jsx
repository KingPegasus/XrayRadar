import { useState } from 'react'

export function EmailVerificationBanner({ me }) {
  const [resending, setResending] = useState(false)
  const [resent, setResent] = useState(false)
  const [error, setError] = useState('')

  if (!me || me.email_verified) return null

  const handleResend = async () => {
    setResending(true)
    setError('')
    try {
      const res = await fetch('/auth/resend-verification', {
        method: 'POST',
        credentials: 'include',
      })
      if (res.ok) {
        setResent(true)
      } else {
        const data = await res.json()
        setError(data.detail || 'Failed to resend')
      }
    } catch {
      setError('Network error')
    } finally {
      setResending(false)
    }
  }

  return (
    <div
      style={{
        background: 'rgba(245, 158, 11, 0.15)',
        borderBottom: '1px solid rgba(245, 158, 11, 0.3)',
        padding: '10px 20px',
        fontSize: 13,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 12,
        flexWrap: 'wrap',
      }}
    >
      <span style={{ color: '#fbbf24' }}>
        Please verify your email address. Check your inbox for the verification link.
      </span>
      {resent ? (
        <span style={{ color: '#86efac' }}>Verification email sent!</span>
      ) : error ? (
        <span style={{ color: '#fca5a5' }}>{error}</span>
      ) : (
        <button
          type="button"
          className="button"
          style={{ fontSize: 11, padding: '4px 10px' }}
          onClick={handleResend}
          disabled={resending}
        >
          {resending ? 'Sending...' : 'Resend email'}
        </button>
      )}
    </div>
  )
}
