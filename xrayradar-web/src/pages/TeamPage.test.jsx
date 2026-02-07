import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TeamPage } from './TeamPage'

vi.mock('../utils/api', () => ({
  fetchJson: vi.fn(),
}))

describe('TeamPage', () => {
  const me = { email: 'teams@example.com', plan: 'Teams' }

  beforeEach(async () => {
    const { fetchJson } = await import('../utils/api')
    vi.mocked(fetchJson).mockImplementation((url) => {
      if (url === '/api/user/team/members') return Promise.resolve([])
      if (url === '/api/user/team/invites') return Promise.resolve([])
      if (url === '/api/user/projects') return Promise.resolve([])
      return Promise.resolve([])
    })
  })

  it('renders Team page with invite and members sections', async () => {
    render(<TeamPage me={me} />)
    expect(screen.getByText(/Invite by email/i)).toBeInTheDocument()
    expect(screen.getByText(/Add member to project/i)).toBeInTheDocument()
    await screen.findByText(/No team members yet/i)
    expect(screen.getByRole('heading', { name: /Team members/i })).toBeInTheDocument()
  })

  it('shows invite form and add member section', async () => {
    render(<TeamPage me={me} />)
    await screen.findByText(/No team members yet/i)
    expect(screen.getByPlaceholderText(/teammate@example.com/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/user@example.com/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Send invite/i })).toBeInTheDocument()
  })
})
