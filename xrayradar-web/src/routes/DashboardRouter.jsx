import { lazy, Suspense } from 'react'

const DashboardHome = lazy(() => import('../pages/DashboardHome').then((m) => ({ default: m.DashboardHome })))
const ProjectsPage = lazy(() => import('../pages/ProjectsPage').then((m) => ({ default: m.ProjectsPage })))
const TokensPage = lazy(() => import('../pages/TokensPage').then((m) => ({ default: m.TokensPage })))
const TeamPage = lazy(() => import('../pages/TeamPage').then((m) => ({ default: m.TeamPage })))
const SettingsPage = lazy(() => import('../pages/SettingsPage').then((m) => ({ default: m.SettingsPage })))
const ProjectIssuesPage = lazy(() => import('../pages/ProjectIssuesPage').then((m) => ({ default: m.ProjectIssuesPage })))
const IssueDetailPage = lazy(() => import('../pages/IssueDetailPage').then((m) => ({ default: m.IssueDetailPage })))
const EventDetailPage = lazy(() => import('../pages/EventDetailPage').then((m) => ({ default: m.EventDetailPage })))

export function DashboardRouter({ path, me }) {
  const fallback = null
  // /dashboard = overview (stats)
  if (path === '/dashboard') {
    return (
      <Suspense fallback={fallback}>
        <DashboardHome me={me} />
      </Suspense>
    )
  }
  if (path === '/dashboard/projects') {
    return (
      <Suspense fallback={fallback}>
        <ProjectsPage me={me} />
      </Suspense>
    )
  }
  if (path === '/dashboard/tokens') {
    return (
      <Suspense fallback={fallback}>
        <TokensPage me={me} />
      </Suspense>
    )
  }
  if (path === '/dashboard/team') {
    return (
      <Suspense fallback={fallback}>
        <TeamPage me={me} />
      </Suspense>
    )
  }
  if (path === '/dashboard/settings') {
    return (
      <Suspense fallback={fallback}>
        <SettingsPage me={me} />
      </Suspense>
    )
  }
  const m1 = path.match(/^\/dashboard\/projects\/(\d+)$/)
  if (m1) {
    return (
      <Suspense fallback={fallback}>
        <ProjectIssuesPage projectId={Number(m1[1])} me={me} />
      </Suspense>
    )
  }
  const m2 = path.match(/^\/dashboard\/projects\/(\d+)\/issues\/([a-f0-9]+)$/)
  if (m2) {
    return (
      <Suspense fallback={fallback}>
        <IssueDetailPage projectId={Number(m2[1])} fingerprint={m2[2]} />
      </Suspense>
    )
  }
  const m3 = path.match(/^\/dashboard\/projects\/(\d+)\/issues\/([a-f0-9]+)\/events\/([^/]+)$/i)
  if (m3) {
    return (
      <Suspense fallback={fallback}>
        <EventDetailPage projectId={Number(m3[1])} fingerprint={m3[2]} eventId={m3[3]} />
      </Suspense>
    )
  }
  return (
    <Suspense fallback={fallback}>
      <DashboardHome me={me} />
    </Suspense>
  )
}
