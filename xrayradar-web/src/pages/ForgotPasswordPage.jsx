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
      <main className="page" style={{ paddingTop: 48, paddingBottom: 48 }}>
        <div className="container pageNarrow">
          <div className="pageCard">
            <header className="pageHeader">
              <h1 className="pageTitle">Check your email</h1>
              <p className="pageSubtitle">
                If an account exists for that email, we sent a link to reset your password. The link expires in 1 hour.
              </p>
            </header>
            <div className="pageActions">
              <a className="button buttonPrimary" href="/login">Back to sign in</a>
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
            <h1 className="pageTitle">Forgot password</h1>
            <p className="pageSubtitle">
              Enter your email and we'll send you a link to reset your password.
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

            {error ? (
              <div className="fieldError" role="alert">
                {error}
              </div>
            ) : null}

            <div className="pageActions">
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
