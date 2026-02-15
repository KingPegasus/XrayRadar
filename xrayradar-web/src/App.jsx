import { useState, useEffect, useCallback, lazy, Suspense } from 'react'
import { usePathname } from './hooks/usePathname'
import { navigate } from './utils/navigation'
import { fetchMe } from './utils/api'

const LoginPage = lazy(() => import('./pages/LoginPage').then((m) => ({ default: m.LoginPage })))
const LandingPage = lazy(() => import('./pages/LandingPage').then((m) => ({ default: m.LandingPage })))
const PrivacyPolicyPage = lazy(() => import('./pages/PrivacyPolicyPage').then((m) => ({ default: m.PrivacyPolicyPage })))
const TermsOfServicePage = lazy(() => import('./pages/TermsOfServicePage').then((m) => ({ default: m.TermsOfServicePage })))
const VerifyEmailPage = lazy(() => import('./pages/VerifyEmailPage').then((m) => ({ default: m.VerifyEmailPage })))
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage').then((m) => ({ default: m.ForgotPasswordPage })))
const ResetPasswordPage = lazy(() => import('./pages/ResetPasswordPage').then((m) => ({ default: m.ResetPasswordPage })))
const AcceptInvitePage = lazy(() => import('./pages/AcceptInvitePage').then((m) => ({ default: m.AcceptInvitePage })))
const DashboardLayout = lazy(() => import('./components/DashboardLayout').then((m) => ({ default: m.DashboardLayout })))
const DashboardRouter = lazy(() => import('./routes/DashboardRouter').then((m) => ({ default: m.DashboardRouter })))
const SignupModal = lazy(() => import('./components/SignupModal').then((m) => ({ default: m.SignupModal })))

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
    let timeoutId = null
    let loadHandlerRef = null

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
      // Defer /api/me until after load so it's not on the critical request chain (network dependency tree).
      setMeLoaded(true)
      if (typeof window !== 'undefined') {
        const onDone = () => {
          if (!cancelled) fetchMe().then((m) => !cancelled && setMe(m))
        }
        if (document.readyState === 'complete') {
          timeoutId = window.setTimeout(onDone, 0)
        } else {
          window.addEventListener('load', onDone, { once: true })
          loadHandlerRef = onDone
        }
      }
    }

    return () => {
      cancelled = true
      if (timeoutId !== null) {
        window.clearTimeout(timeoutId)
      }
      if (loadHandlerRef !== null && typeof window !== 'undefined') {
        window.removeEventListener('load', loadHandlerRef)
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
