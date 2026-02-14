import { useState, useEffect, useCallback } from 'react'
import { usePathname } from './hooks/usePathname'
import { navigate } from './utils/navigation'
import { fetchMe } from './utils/api'
import { LoginPage } from './pages/LoginPage'
import { LandingPage } from './pages/LandingPage'
import { PrivacyPolicyPage } from './pages/PrivacyPolicyPage'
import { TermsOfServicePage } from './pages/TermsOfServicePage'
import { VerifyEmailPage } from './pages/VerifyEmailPage'
import { ForgotPasswordPage } from './pages/ForgotPasswordPage'
import { ResetPasswordPage } from './pages/ResetPasswordPage'
import { AcceptInvitePage } from './pages/AcceptInvitePage'
import { DashboardLayout } from './components/DashboardLayout'
import { DashboardRouter } from './routes/DashboardRouter'
import { SignupModal } from './components/SignupModal'

export default function App() {
  const path = usePathname()
  const [signupOpen, setSignupOpen] = useState(false)
  const [signupPlan, setSignupPlan] = useState('Free')
  const [me, setMe] = useState(null)
  const [meLoaded, setMeLoaded] = useState(false)
  const isTestEnv = typeof import.meta !== 'undefined' && import.meta.env?.MODE === 'test'

  const openSignup = (plan) => {
    setSignupPlan(plan)
    setSignupOpen(true)
  }

  useEffect(() => {
    let cancelled = false
    let idleId = null
    let timeoutId = null

    const loadMe = () => {
      fetchMe()
        .then((m) => {
          if (!cancelled) setMe(m)
        })
        .finally(() => {
          if (!cancelled) setMeLoaded(true)
        })
    }

    const deferAuthHydration = path === '/' && !isTestEnv

    if (!deferAuthHydration) {
      setMeLoaded(false)
      loadMe()
    } else {
      // Keep first paint focused on marketing/public pages and hydrate auth in idle time.
      setMeLoaded(true)
      if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
        idleId = window.requestIdleCallback(() => {
          if (!cancelled) fetchMe().then((m) => !cancelled && setMe(m))
        }, { timeout: 2500 })
      } else {
        timeoutId = window.setTimeout(() => {
          if (!cancelled) fetchMe().then((m) => !cancelled && setMe(m))
        }, 1200)
      }
    }

    return () => {
      cancelled = true
      if (typeof window !== 'undefined' && idleId !== null && 'cancelIdleCallback' in window) {
        window.cancelIdleCallback(idleId)
      }
      if (timeoutId !== null) {
        window.clearTimeout(timeoutId)
      }
    }
  }, [path])

  const doLogout = async () => {
    try {
      await fetch('/auth/logout', { method: 'POST', credentials: 'include' })
    } finally {
      setMe(null)
      navigate('/')
    }
  }

  if (path === '/login') {
    const returnTo = typeof window !== 'undefined' ? new URLSearchParams(window.location.search).get('next') : null
    return <LoginPage onLoggedIn={(m) => setMe(m)} returnTo={returnTo} />
  }

  if (path === '/accept-invite') {
    if (!meLoaded) return null
    const token = typeof window !== 'undefined' ? new URLSearchParams(window.location.search).get('token') : null
    if (!me) {
      const next = '/accept-invite' + (typeof window !== 'undefined' && window.location.search ? window.location.search : '')
      navigate('/login?next=' + encodeURIComponent(next))
      return null
    }
    return (
      <DashboardLayout me={me} onLogout={doLogout}>
        <AcceptInvitePage token={token} onSuccess={() => navigate('/dashboard')} />
      </DashboardLayout>
    )
  }

  if (path === '/forgot-password') {
    return <ForgotPasswordPage />
  }

  if (path === '/reset-password') {
    return <ResetPasswordPage />
  }

  if (path === '/privacy') {
    return <PrivacyPolicyPage />
  }

  if (path === '/terms') {
    return <TermsOfServicePage />
  }

  const refreshMe = useCallback(() => fetchMe().then((m) => setMe(m)), [])

  if (path === '/verify-email') {
    return <VerifyEmailPage onVerified={refreshMe} />
  }

  if (path === '/dashboard' || path.startsWith('/dashboard/')) {
    if (!meLoaded) return null
    if (!me) {
      navigate('/login')
      return null
    }
    return (
      <DashboardLayout me={me} onLogout={doLogout}>
        <DashboardRouter path={path} me={me} />
      </DashboardLayout>
    )
  }

  return (
    <>
      <LandingPage me={me} onSignupOpen={openSignup} onLogout={doLogout} />
      <SignupModal open={signupOpen} plan={signupPlan} onClose={() => setSignupOpen(false)} />
    </>
  )
}
