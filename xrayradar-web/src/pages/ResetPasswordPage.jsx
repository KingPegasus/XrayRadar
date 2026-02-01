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
      <main style={{ padding: '72px 0 46px' }}>
        <div className="container" style={{ width: 'min(680px, calc(100% - 48px))' }}>
          <div className="panel" style={{ padding: 18 }}>
            <div style={{ fontWeight: 900, letterSpacing: '-0.02em', fontSize: 22 }}>Password reset</div>
            <div className="small" style={{ color: 'var(--muted)', marginTop: 8 }}>
              Your password has been updated. You can now sign in with your new password.
            </div>
            <div style={{ marginTop: 14 }}>
              <button
                type="button"
                className="button buttonPrimary"
                onClick={() => navigate('/login')}
              >
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
      <main style={{ padding: '72px 0 46px' }}>
        <div className="container" style={{ width: 'min(680px, calc(100% - 48px))' }}>
          <div className="panel" style={{ padding: 18 }}>
            <div style={{ fontWeight: 900, letterSpacing: '-0.02em', fontSize: 22 }}>Invalid link</div>
            <div className="small" style={{ color: 'var(--muted)', marginTop: 8 }}>
              This reset link is missing a token. Please request a new link from the forgot password page.
            </div>
            <div style={{ marginTop: 14 }}>
              <a className="button buttonPrimary" href="/forgot-password">Request new link</a>
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
          <div style={{ fontWeight: 900, letterSpacing: '-0.02em', fontSize: 22 }}>Set new password</div>
          <div className="small" style={{ color: 'var(--muted)', marginTop: 8 }}>
            Enter your new password below. It must be at least 8 characters.
          </div>

          <form onSubmit={submit} style={{ marginTop: 14 }}>
            <label className="fieldLabel">New password</label>
            <input
              className="fieldInput"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="new-password"
            />

            <label className="fieldLabel" style={{ marginTop: 10 }}>Confirm password</label>
            <input
              className="fieldInput"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder="••••••••"
              autoComplete="new-password"
            />

            {error ? (
              <div className="fieldError" role="alert" style={{ marginTop: 10 }}>
                {error}
              </div>
            ) : null}

            <div style={{ display: 'flex', gap: 10, marginTop: 14, flexWrap: 'wrap' }}>
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
