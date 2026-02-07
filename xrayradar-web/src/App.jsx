import { useState, useEffect, useCallback } from 'react'
import { usePathname } from './hooks/usePathname'
import { navigate } from './utils/navigation'
import { fetchMe } from './utils/api'
import { LoginPage } from './pages/LoginPage'
import { LandingPage } from './pages/LandingPage'
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

  const openSignup = (plan) => {
    setSignupPlan(plan)
    setSignupOpen(true)
  }

  useEffect(() => {
    fetchMe()
      .then((m) => setMe(m))
      .finally(() => setMeLoaded(true))
  }, [])

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
