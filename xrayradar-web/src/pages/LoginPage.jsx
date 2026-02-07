import { useState } from 'react'
import { readErrorMessage, fetchMe } from '../utils/api'

export function LoginPage({ onLoggedIn, returnTo }) {
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
        window.location.href = (returnTo && returnTo.startsWith('/')) ? returnTo : '/dashboard'
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
    <main className="page" style={{ paddingTop: 48, paddingBottom: 48 }}>
      <div className="container pageNarrow">
        <div className="pageCard">
          <header className="pageHeader">
            <h1 className="pageTitle">Sign in</h1>
            <p className="pageSubtitle">
              Use your email + password to access your dashboard.
            </p>
          </header>

          <form onSubmit={submit} className="pageForm">
            <div>
              <label className="fieldLabel">Email</label>
              <input
                className="fieldInput"
                style={{ marginTop: 6 }}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                autoComplete="email"
              />
            </div>
            <div>
              <label className="fieldLabel">Password</label>
              <input
                className="fieldInput"
                style={{ marginTop: 6 }}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                type="password"
                autoComplete="current-password"
              />
              <div style={{ marginTop: 8, fontSize: 13 }}>
                <a href="/forgot-password" style={{ color: 'var(--muted)', textDecoration: 'none' }}>
                  Forgot password?
                </a>
              </div>
            </div>

            {error ? (
              <div className="fieldError" role="alert">
                {error}
              </div>
            ) : null}

            <div className="pageActions">
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
