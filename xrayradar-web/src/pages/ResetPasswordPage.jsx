import { useState, useEffect } from 'react'
import { readErrorMessage } from '../utils/api'
import { navigate } from '../utils/navigation'

export function ResetPasswordPage() {
  const [token, setToken] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const t = params.get('token')
    if (t) setToken(t)
  }, [])

  const submit = async (e) => {
    e.preventDefault()
    if (submitting || !token) return
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }

    setError('')
    setSubmitting(true)
    try {
      const resp = await fetch('/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ token, new_password: password }),
      })
      if (!resp.ok) {
        setError(await readErrorMessage(resp))
        return
      }
      setSuccess(true)
    } catch {
      setError('Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (success) {
    return (
      <main className="page" style={{ paddingTop: 48, paddingBottom: 48 }}>
        <div className="container pageNarrow">
          <div className="pageCard">
            <header className="pageHeader">
              <h1 className="pageTitle">Password reset</h1>
              <p className="pageSubtitle">
                Your password has been updated. You can now sign in with your new password.
              </p>
            </header>
            <div className="pageActions">
              <button type="button" className="button buttonPrimary" onClick={() => navigate('/login')}>
                Sign in
              </button>
            </div>
          </div>
        </div>
      </main>
    )
  }

  if (!token) {
    return (
      <main className="page" style={{ paddingTop: 48, paddingBottom: 48 }}>
        <div className="container pageNarrow">
          <div className="pageCard">
            <header className="pageHeader">
              <h1 className="pageTitle">Invalid link</h1>
              <p className="pageSubtitle">
                This reset link is missing a token. Please request a new link from the forgot password page.
              </p>
            </header>
            <div className="pageActions">
              <a className="button buttonPrimary" href="/forgot-password">Request new link</a>
            </div>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="page" style={{ paddingTop: 48, paddingBottom: 48 }}>
      <div className="container pageNarrow">
        <div className="pageCard">
          <header className="pageHeader">
            <h1 className="pageTitle">Set new password</h1>
            <p className="pageSubtitle">
              Enter your new password below. It must be at least 8 characters.
            </p>
          </header>

          <form onSubmit={submit} className="pageForm">
            <div>
              <label className="fieldLabel">New password</label>
              <input
                className="fieldInput"
                style={{ marginTop: 6 }}
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="new-password"
              />
            </div>
            <div>
              <label className="fieldLabel">Confirm password</label>
              <input
                className="fieldInput"
                style={{ marginTop: 6 }}
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                placeholder="••••••••"
                autoComplete="new-password"
              />
            </div>

            {error ? (
              <div className="fieldError" role="alert">
                {error}
              </div>
            ) : null}

            <div className="pageActions">
              <button className="button buttonPrimary" type="submit" disabled={submitting}>
                {submitting ? 'Resetting…' : 'Reset password'}
              </button>
              <a className="button" href="/login">Back to sign in</a>
            </div>
          </form>
        </div>
      </div>
    </main>
  )
}
