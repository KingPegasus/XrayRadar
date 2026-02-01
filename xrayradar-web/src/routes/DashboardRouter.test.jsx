import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DashboardRouter } from './DashboardRouter'

vi.mock('../pages/ProjectsPage', () => ({
  ProjectsPage: ({ me }) => <div>ProjectsPage: {me?.email}</div>,
}))

vi.mock('../pages/TokensPage', () => ({
  TokensPage: ({ me }) => <div>TokensPage: {me?.email}</div>,
}))

vi.mock('../pages/SettingsPage', () => ({
  SettingsPage: ({ me }) => <div>SettingsPage: {me?.email}</div>,
}))

vi.mock('../pages/ProjectIssuesPage', () => ({
  ProjectIssuesPage: ({ projectId }) => <div>ProjectIssuesPage: {projectId}</div>,
}))

vi.mock('../pages/IssueDetailPage', () => ({
  IssueDetailPage: ({ projectId, fingerprint }) => (
    <div>IssueDetailPage: {projectId} - {fingerprint}</div>
  ),
}))

vi.mock('../pages/EventDetailPage', () => ({
  EventDetailPage: ({ projectId, fingerprint, eventId }) => (
    <div>EventDetailPage: {projectId} - {fingerprint} - {eventId}</div>
  ),
}))

vi.mock('../pages/DashboardHome', () => ({
  DashboardHome: ({ me }) => <div>DashboardHome: {me?.email}</div>,
}))

describe('DashboardRouter', () => {
  const me = { email: 'test@example.com' }

  it('renders DashboardHome (overview) for /dashboard', () => {
    render(<DashboardRouter path="/dashboard" me={me} />)
    expect(screen.getByText(/DashboardHome:/i)).toBeInTheDocument()
  })

  it('renders ProjectsPage for /dashboard/projects', () => {
    render(<DashboardRouter path="/dashboard/projects" me={me} />)
    expect(screen.getByText(/ProjectsPage:/i)).toBeInTheDocument()
  })

  it('renders TokensPage for /dashboard/tokens', () => {
    render(<DashboardRouter path="/dashboard/tokens" me={me} />)
    expect(screen.getByText(/TokensPage:/i)).toBeInTheDocument()
  })

  it('renders SettingsPage for /dashboard/settings', () => {
    render(<DashboardRouter path="/dashboard/settings" me={me} />)
    expect(screen.getByText(/SettingsPage:/i)).toBeInTheDocument()
  })

  it('renders ProjectIssuesPage for /dashboard/projects/:id', () => {
    render(<DashboardRouter path="/dashboard/projects/123" me={me} />)
    expect(screen.getByText(/ProjectIssuesPage: 123/i)).toBeInTheDocument()
  })

  it('renders IssueDetailPage for /dashboard/projects/:id/issues/:fingerprint', () => {
    render(<DashboardRouter path="/dashboard/projects/123/issues/abc123" me={me} />)
    expect(screen.getByText(/IssueDetailPage: 123 - abc123/i)).toBeInTheDocument()
  })

  it('renders EventDetailPage for /dashboard/projects/:id/issues/:fingerprint/events/:eventId', () => {
    render(<DashboardRouter path="/dashboard/projects/123/issues/abc123/events/event456" me={me} />)
    expect(screen.getByText(/EventDetailPage: 123 - abc123 - event456/i)).toBeInTheDocument()
  })

  it('renders DashboardHome as fallback', () => {
    render(<DashboardRouter path="/dashboard/unknown" me={me} />)
    expect(screen.getByText(/DashboardHome:/i)).toBeInTheDocument()
  })
})
