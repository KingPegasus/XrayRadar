import { useState, useEffect } from 'react'
import { Link } from './Link'
import { readErrorMessage, fetchMe } from '../utils/api'

export function SignupModal({ open, plan, onClose }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [agreed, setAgreed] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)

  useEffect(() => {
    if (open) {
      setEmail('')
      setPassword('')
      setConfirm('')
      setAgreed(false)
      setError('')
      setSubmitting(false)
      setDone(false)
    }
  }, [open])

  if (!open) return null

  const submit = async (e) => {
    e.preventDefault()
    if (submitting) return

    const trimmedEmail = email.trim().toLowerCase()
    if (!trimmedEmail || !trimmedEmail.includes('@')) {
      setError('Please enter a valid email address.')
      return
    }
    if (!password || password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }
    if (!agreed) {
      setError('You must agree to the Terms of Service and Privacy Policy.')
      return
    }

    setError('')
    setSubmitting(true)
    try {
      const resp = await fetch('/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email: trimmedEmail, password, plan }),
      })

      if (!resp.ok) {
        setError(await readErrorMessage(resp))
        return
      }

      await fetchMe()
      setDone(true)
    } catch {
      setError('Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="modalOverlay" role="dialog" aria-modal="true" aria-label="Sign up">
      <div className="modalCard panel">
        <div className="modalHeader">
          <div>
            <div className="badge">{plan}</div>
            <div style={{ marginTop: 10, fontWeight: 800, letterSpacing: '-0.02em', fontSize: 18 }}>
              {done ? "You're in!" : 'Create your account'}
            </div>
            <div className="small" style={{ color: 'var(--muted)', marginTop: 6 }}>
              {done
                ? "You can now continue and we'll use this session for the dashboard later."
                : 'Use an email + password to create your account.'}
            </div>
          </div>
          <button type="button" className="modalClose" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        {done ? (
          <div style={{ marginTop: 14 }}>
            <div className="card" style={{ background: 'rgba(255, 255, 255, 0.04)' }}>
              <div className="cardTitle">Next steps</div>
              <p className="cardText">
                1) Create a token in your server
                <br />
                2) Set <code>XRAYRADAR_DSN</code> and <code>XRAYRADAR_AUTH_TOKEN</code>
                <br />
                3) Capture your first exception
              </p>
            </div>
            <div style={{ display: 'flex', gap: 10, marginTop: 14, flexWrap: 'wrap' }}>
              <button type="button" className="button buttonPrimary" onClick={onClose}>
                Done
              </button>
            </div>
          </div>
        ) : (
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
              autoComplete="new-password"
            />

            <label className="fieldLabel" style={{ marginTop: 10 }}>
              Confirm password
            </label>
            <input
              className="fieldInput"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder="••••••••"
              type="password"
              autoComplete="new-password"
            />

            <label className="fieldLabel" style={{ marginTop: 14, display: 'flex', alignItems: 'flex-start', gap: 10, cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={agreed}
                onChange={(e) => setAgreed(e.target.checked)}
                style={{ marginTop: 4, flexShrink: 0 }}
              />
              <span className="small">
                I agree to the <Link to="/terms" className="link">Terms of Service</Link> and <Link to="/privacy" className="link">Privacy Policy</Link>
              </span>
            </label>

            {error ? (
              <div className="fieldError" role="alert" style={{ marginTop: 10 }}>
                {error}
              </div>
            ) : null}

            <div style={{ display: 'flex', gap: 10, marginTop: 14, flexWrap: 'wrap' }}>
              <button className="button buttonPrimary" type="submit">
                Create account
              </button>
              <button className="button" type="button" onClick={onClose}>
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
