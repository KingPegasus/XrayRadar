import { useState } from 'react'
import { readErrorMessage, fetchMe } from '../utils/api'

export function LoginPage({ onLoggedIn }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    if (submitting) return
    const trimmedEmail = email.trim().toLowerCase()
    if (!trimmedEmail || !trimmedEmail.includes('@')) {
      setError('Please enter a valid email address.')
      return
    }
    if (!password) {
      setError('Password is required.')
      return
    }

    setError('')
    setSubmitting(true)
    try {
      const resp = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email: trimmedEmail, password }),
      })
      if (!resp.ok) {
        setError(await readErrorMessage(resp))
        return
      }
      const me = await fetchMe()
      if (me) {
        onLoggedIn(me)
        // Use hard navigation to ensure auth state is properly checked
        window.location.href = '/dashboard'
      } else {
        setError('Failed to load user info after login')
      }
    } catch {
      setError('Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main style={{ padding: '72px 0 46px' }}>
      <div className="container" style={{ width: 'min(680px, calc(100% - 48px))' }}>
        <div className="panel" style={{ padding: 18 }}>
          <div style={{ fontWeight: 900, letterSpacing: '-0.02em', fontSize: 22 }}>Sign in</div>
          <div className="small" style={{ color: 'var(--muted)', marginTop: 8 }}>
            Use your email + password to access your dashboard.
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

            <label className="fieldLabel" style={{ marginTop: 10 }}>
              Password
            </label>
            <input
              className="fieldInput"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              type="password"
              autoComplete="current-password"
            />

            {error ? (
              <div className="fieldError" role="alert" style={{ marginTop: 10 }}>
                {error}
              </div>
            ) : null}

            <div style={{ display: 'flex', gap: 10, marginTop: 14, flexWrap: 'wrap' }}>
              <button className="button buttonPrimary" type="submit" disabled={submitting}>
                {submitting ? 'Signing in…' : 'Sign in'}
              </button>
              <a className="button" href="/">
                Back
              </a>
            </div>
          </form>
        </div>
      </div>
    </main>
  )
}
