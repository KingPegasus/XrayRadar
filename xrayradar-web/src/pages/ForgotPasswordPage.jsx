import { useState } from 'react'
import { readErrorMessage } from '../utils/api'

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [sent, setSent] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    if (submitting) return
    const trimmedEmail = email.trim().toLowerCase()
    if (!trimmedEmail || !trimmedEmail.includes('@')) {
      setError('Please enter a valid email address.')
      return
    }

    setError('')
    setSubmitting(true)
    try {
      const resp = await fetch('/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email: trimmedEmail }),
      })
      if (!resp.ok) {
        setError(await readErrorMessage(resp))
        return
      }
      setSent(true)
    } catch {
      setError('Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (sent) {
    return (
      <main style={{ padding: '72px 0 46px' }}>
        <div className="container" style={{ width: 'min(680px, calc(100% - 48px))' }}>
          <div className="panel" style={{ padding: 18 }}>
            <div style={{ fontWeight: 900, letterSpacing: '-0.02em', fontSize: 22 }}>Check your email</div>
            <div className="small" style={{ color: 'var(--muted)', marginTop: 8 }}>
              If an account exists for that email, we sent a link to reset your password. The link expires in 1 hour.
            </div>
            <div style={{ marginTop: 14 }}>
              <a className="button buttonPrimary" href="/login">Back to sign in</a>
            </div>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main style={{ padding: '72px 0 46px' }}>
      <div className="container" style={{ width: 'min(680px, calc(100% - 48px))' }}>
        <div className="panel" style={{ padding: 18 }}>
          <div style={{ fontWeight: 900, letterSpacing: '-0.02em', fontSize: 22 }}>Forgot password</div>
          <div className="small" style={{ color: 'var(--muted)', marginTop: 8 }}>
            Enter your email and we’ll send you a link to reset your password.
          </div>

          <form onSubmit={submit} style={{ marginTop: 14 }}>
            <label className="fieldLabel">Email</label>
            <input
              className="fieldInput"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              autoComplete="email"
            />

            {error ? (
              <div className="fieldError" role="alert" style={{ marginTop: 10 }}>
                {error}
              </div>
            ) : null}

            <div style={{ display: 'flex', gap: 10, marginTop: 14, flexWrap: 'wrap' }}>
              <button className="button buttonPrimary" type="submit" disabled={submitting}>
                {submitting ? 'Sending…' : 'Send reset link'}
              </button>
              <a className="button" href="/login">Back to sign in</a>
            </div>
          </form>
        </div>
      </div>
    </main>
  )
}
