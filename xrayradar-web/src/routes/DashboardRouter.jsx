import { ProjectsPage } from '../pages/ProjectsPage'
import { TokensPage } from '../pages/TokensPage'
import { SettingsPage } from '../pages/SettingsPage'
import { ProjectIssuesPage } from '../pages/ProjectIssuesPage'
import { IssueDetailPage } from '../pages/IssueDetailPage'
import { EventDetailPage } from '../pages/EventDetailPage'
import { DashboardHome } from '../pages/DashboardHome'

export function DashboardRouter({ path, me }) {
  // /dashboard = overview (stats)
  if (path === '/dashboard') return <DashboardHome me={me} />

  if (path === '/dashboard/projects') return <ProjectsPage me={me} />

  if (path === '/dashboard/tokens') return <TokensPage me={me} />

  if (path === '/dashboard/settings') return <SettingsPage me={me} />

  const m1 = path.match(/^\/dashboard\/projects\/(\d+)$/)
  if (m1) return <ProjectIssuesPage projectId={Number(m1[1])} me={me} />

  const m2 = path.match(/^\/dashboard\/projects\/(\d+)\/issues\/([a-f0-9]+)$/)
  if (m2) return <IssueDetailPage projectId={Number(m2[1])} fingerprint={m2[2]} />

  const m3 = path.match(/^\/dashboard\/projects\/(\d+)\/issues\/([a-f0-9]+)\/events\/([^/]+)$/i)
  if (m3) return <EventDetailPage projectId={Number(m3[1])} fingerprint={m3[2]} eventId={m3[3]} />

  // fallback
  return <DashboardHome me={me} />
}
