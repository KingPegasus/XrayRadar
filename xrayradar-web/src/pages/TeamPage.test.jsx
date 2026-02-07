import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TeamPage } from './TeamPage'

vi.mock('../utils/api', () => ({
  fetchJson: vi.fn(),
}))

describe('TeamPage', () => {
  const me = { email: 'teams@example.com', plan: 'Teams' }
  let fetchJson
  const loadData = { members: [], invites: [], projects: [] }

  beforeEach(async () => {
    const api = await import('../utils/api')
    fetchJson = api.fetchJson
    loadData.members = []
    loadData.invites = []
    loadData.projects = []
    vi.mocked(fetchJson).mockImplementation((url) => {
      if (url === '/api/user/team/members') return Promise.resolve(Array.isArray(loadData.members) ? loadData.members : [])
      if (url === '/api/user/team/invites') return Promise.resolve(Array.isArray(loadData.invites) ? loadData.invites : [])
      if (url === '/api/user/projects') return Promise.resolve(Array.isArray(loadData.projects) ? loadData.projects : [])
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

  it('shows error when load returns non-array and uses fallback', async () => {
    loadData.members = null
    loadData.invites = null
    loadData.projects = null
    render(<TeamPage me={me} />)
    await screen.findByText(/No team members yet/i)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('sendInvite shows error when email is empty', async () => {
    render(<TeamPage me={me} />)
    await screen.findByText(/No team members yet/i)
    const form = screen.getByRole('button', { name: /Send invite/i }).closest('form')
    fireEvent.submit(form)
    expect(await screen.findByRole('alert')).toHaveTextContent(/Email is required/i)
  })

  it('sendInvite shows error when no project selected', async () => {
    render(<TeamPage me={me} />)
    await screen.findByText(/No team members yet/i)
    await userEvent.type(screen.getByPlaceholderText(/teammate@example.com/i), 'new@example.com')
    const form = screen.getByRole('button', { name: /Send invite/i }).closest('form')
    fireEvent.submit(form)
    expect(await screen.findByRole('alert')).toHaveTextContent(/Select at least one project/i)
  })

  it('sendInvite submits and reloads on success', async () => {
    vi.mocked(fetchJson).mockImplementation((url, opts) => {
      if (url === '/api/user/team/members') return Promise.resolve([])
      if (url === '/api/user/team/invites') return Promise.resolve([])
      if (url === '/api/user/projects') return Promise.resolve([{ id: 1, name: 'Proj A' }])
      if (opts?.method === 'POST' && url === '/api/user/team/invites') return Promise.resolve({})
      return Promise.resolve([])
    })
    render(<TeamPage me={me} />)
    await screen.findByText(/No team members yet/i)
    expect(screen.getByRole('checkbox', { name: /Proj A/i })).toBeInTheDocument()
    await userEvent.type(screen.getByPlaceholderText(/teammate@example.com/i), 'new@example.com')
    await userEvent.click(screen.getByRole('checkbox', { name: /Proj A/i }))
    await userEvent.click(screen.getByRole('button', { name: /Send invite/i }))
    expect(fetchJson).toHaveBeenCalledWith(
      '/api/user/team/invites',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ email: 'new@example.com', project_ids: [1] }),
      })
    )
  })

  it('addMemberToProject shows error when project or email empty', async () => {
    render(<TeamPage me={me} />)
    await screen.findByText(/No team members yet/i)
    const addForm = screen.getByRole('button', { name: 'Add' }).closest('form')
    fireEvent.submit(addForm)
    expect(await screen.findByRole('alert')).toHaveTextContent(/Project and email are required/i)
  })

  it('addMemberToProject submits and reloads on success', async () => {
    vi.mocked(fetchJson).mockImplementation((url, opts) => {
      if (url === '/api/user/team/members') return Promise.resolve([])
      if (url === '/api/user/team/invites') return Promise.resolve([])
      if (url === '/api/user/projects') return Promise.resolve([{ id: 1, name: 'Proj A' }])
      if (opts?.method === 'POST' && url?.includes('/projects/') && url?.includes('/members')) return Promise.resolve({})
      return Promise.resolve([])
    })
    render(<TeamPage me={me} />)
    await screen.findByText(/No team members yet/i)
    expect(screen.getByRole('option', { name: 'Proj A' })).toBeInTheDocument()
    const projectSelect = screen.getByRole('combobox')
    await userEvent.selectOptions(projectSelect, '1')
    await userEvent.type(screen.getByPlaceholderText(/user@example.com/i), 'member@example.com')
    await userEvent.click(screen.getByRole('button', { name: 'Add' }))
    expect(fetchJson).toHaveBeenCalledWith(
      '/api/user/projects/1/members',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ email: 'member@example.com' }),
      })
    )
  })

  it('revokeProjectAccess calls DELETE and reloads', async () => {
    loadData.projects = [{ id: 1, name: 'Proj A' }]
    loadData.members = [{ user_id: 10, email: 'm@example.com', project_ids: [1] }]
    render(<TeamPage me={me} />)
    await screen.findByText('m@example.com')
    const revokeBtn = screen.getByRole('button', { name: /Revoke/i })
    await userEvent.click(revokeBtn)
    expect(fetchJson).toHaveBeenCalledWith(
      '/api/user/projects/1/members/10',
      expect.objectContaining({ method: 'DELETE' })
    )
  })

  it('removeFromTeam confirms and calls DELETE', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)
    loadData.projects = [{ id: 1, name: 'Proj A' }]
    loadData.members = [{ user_id: 10, email: 'm@example.com', project_ids: [1] }]
    render(<TeamPage me={me} />)
    await screen.findByText('m@example.com')
    await userEvent.click(screen.getByRole('button', { name: /Remove from team/i }))
    expect(fetchJson).toHaveBeenCalledWith(
      '/api/user/team/members/10',
      expect.objectContaining({ method: 'DELETE' })
    )
    confirmSpy.mockRestore()
  })

  it('removeFromTeam does nothing when user cancels confirm', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    loadData.members = [{ user_id: 10, email: 'm@example.com', project_ids: [1] }]
    loadData.projects = [{ id: 1, name: 'P' }]
    render(<TeamPage me={me} />)
    await screen.findByText('m@example.com')
    await userEvent.click(screen.getByRole('button', { name: /Remove from team/i }))
    const deleteCalls = vi.mocked(fetchJson).mock.calls.filter((c) => c[0]?.includes('/team/members/') && c[1]?.method === 'DELETE')
    expect(deleteCalls).toHaveLength(0)
    window.confirm.mockRestore()
  })

  it('renders pending invites section when invites exist', async () => {
    loadData.projects = [{ id: 1, name: 'Proj One' }]
    loadData.invites = [{ id: 1, email: 'pending@example.com', project_ids: [1] }]
    render(<TeamPage me={me} />)
    expect(await screen.findByText(/pending@example.com/i)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Pending invites/i })).toBeInTheDocument()
    expect(screen.getAllByText('Proj One').length).toBeGreaterThanOrEqual(1)
  })

  it('projectIdToName fallback for unknown project id', async () => {
    loadData.invites = [{ id: 1, email: 'x@example.com', project_ids: [999] }]
    loadData.projects = []
    render(<TeamPage me={me} />)
    expect(await screen.findByText(/Project 999/)).toBeInTheDocument()
  })

  it('sendInvite shows error when API fails', async () => {
    vi.mocked(fetchJson).mockImplementation((url, opts) => {
      if (opts?.method === 'POST' && url === '/api/user/team/invites') {
        return Promise.reject(new Error('Limit reached'))
      }
      if (url === '/api/user/team/members') return Promise.resolve([])
      if (url === '/api/user/team/invites') return Promise.resolve([])
      if (url === '/api/user/projects') return Promise.resolve([{ id: 1, name: 'ProjForInvite' }])
      return Promise.resolve([])
    })
    render(<TeamPage me={me} />)
    await screen.findByText(/No team members yet/i)
    expect(screen.getByRole('checkbox', { name: /ProjForInvite/i })).toBeInTheDocument()
    await userEvent.type(screen.getByPlaceholderText(/teammate@example.com/i), 'a@b.com')
    await userEvent.click(screen.getByRole('checkbox', { name: /ProjForInvite/i }))
    await userEvent.click(screen.getByRole('button', { name: /Send invite/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Limit reached')
  })

  it('addMemberToProject shows error when API fails', async () => {
    vi.mocked(fetchJson).mockImplementation((url, opts) => {
      if (opts?.method === 'POST' && url?.includes('/members')) {
        return Promise.reject(new Error('User not found'))
      }
      if (url === '/api/user/team/members') return Promise.resolve([])
      if (url === '/api/user/team/invites') return Promise.resolve([])
      if (url === '/api/user/projects') return Promise.resolve([{ id: 1, name: 'ProjForAdd' }])
      return Promise.resolve([])
    })
    render(<TeamPage me={me} />)
    await screen.findByText(/No team members yet/i)
    expect(screen.getByRole('option', { name: 'ProjForAdd' })).toBeInTheDocument()
    await userEvent.selectOptions(screen.getByRole('combobox'), '1')
    await userEvent.type(screen.getByPlaceholderText(/user@example.com/i), 'x@b.com')
    await userEvent.click(screen.getByRole('button', { name: 'Add' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('User not found')
  })

  it('revokeProjectAccess shows error when API fails', async () => {
    loadData.projects = [{ id: 1, name: 'ProjRevoke' }]
    loadData.members = [{ user_id: 5, email: 'u@example.com', project_ids: [1] }]
    fetchJson.mockImplementation((url, opts) => {
      if (opts?.method === 'DELETE' && url?.includes('/projects/')) {
        return Promise.reject(new Error('Failed to revoke'))
      }
      if (url === '/api/user/team/members') return Promise.resolve([{ user_id: 5, email: 'u@example.com', project_ids: [1] }])
      if (url === '/api/user/team/invites') return Promise.resolve([])
      if (url === '/api/user/projects') return Promise.resolve([{ id: 1, name: 'ProjRevoke' }])
      return Promise.resolve([])
    })
    render(<TeamPage me={me} />)
    await screen.findByText('u@example.com')
    await userEvent.click(screen.getByRole('button', { name: /Revoke/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/Failed to revoke/i)
  })

  it('removeFromTeam shows error when API fails', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    loadData.members = [{ user_id: 5, email: 'u@example.com', project_ids: [1] }]
    loadData.projects = [{ id: 1, name: 'ProjRemove' }]
    fetchJson.mockImplementation((url, opts) => {
      if (opts?.method === 'DELETE' && url?.includes('/team/members/')) {
        return Promise.reject(new Error('Failed to remove'))
      }
      if (url === '/api/user/team/members') return Promise.resolve([{ user_id: 5, email: 'u@example.com', project_ids: [1] }])
      if (url === '/api/user/team/invites') return Promise.resolve([])
      if (url === '/api/user/projects') return Promise.resolve([{ id: 1, name: 'ProjRemove' }])
      return Promise.resolve([])
    })
    render(<TeamPage me={me} />)
    await screen.findByText('u@example.com')
    await userEvent.click(screen.getByRole('button', { name: /Remove from team/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/Failed to remove/i)
    window.confirm.mockRestore()
  })
})
