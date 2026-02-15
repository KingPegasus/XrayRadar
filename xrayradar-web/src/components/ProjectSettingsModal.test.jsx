import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { fireEvent } from '@testing-library/react'
import { ProjectSettingsModal } from './ProjectSettingsModal'
import * as api from '../utils/api'

vi.mock('../utils/api')

describe('ProjectSettingsModal', () => {
  const me = { email: 'test@example.com', email_verified: true }
  const meTeams = { ...me, plan: 'Teams' }

  beforeEach(() => {
    vi.clearAllMocks()
    api.fetchJson.mockResolvedValue({
      enabled: false,
      cooldown_minutes: null,
      additional_emails: [],
      min_cooldown_minutes: 10,
    })
  })

  it('opens modal when settings button clicked', async () => {
    const user = userEvent.setup()
    render(<ProjectSettingsModal projectId={1} me={me} />)

    await user.click(screen.getByRole('button', { name: /Project settings/i }))

    await waitFor(() => {
      expect(screen.getByText('Project settings')).toBeInTheDocument()
    })
  })

  it('closes modal when close button clicked', async () => {
    const user = userEvent.setup()
    render(<ProjectSettingsModal projectId={1} me={me} />)

    await user.click(screen.getByRole('button', { name: /Project settings/i }))
    await waitFor(() => expect(screen.getByText('Project settings')).toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: /Close/i }))
    await waitFor(() => {
      expect(screen.queryByText('Project settings')).not.toBeInTheDocument()
    })
  })

  it('closes modal when clicking overlay backdrop', async () => {
    const user = userEvent.setup()
    render(<ProjectSettingsModal projectId={1} me={me} />)

    await user.click(screen.getByRole('button', { name: /Project settings/i }))
    await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument())

    const dialog = screen.getByRole('dialog')
    fireEvent.click(dialog, { target: dialog, currentTarget: dialog })
    await waitFor(() => {
      expect(screen.queryByText('Project settings')).not.toBeInTheDocument()
    })
  })

  it('keeps modal open when clicking inner content (not backdrop)', async () => {
    const user = userEvent.setup()
    render(<ProjectSettingsModal projectId={1} me={me} />)

    await user.click(screen.getByRole('button', { name: /Project settings/i }))
    await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument())

    await user.click(screen.getByText('Project settings'))
    expect(screen.getByText('Project settings')).toBeInTheDocument()
  })

  it('shows project name editor when isOwner', async () => {
    const user = userEvent.setup()
    render(<ProjectSettingsModal projectId={1} me={me} projectName="My Project" isOwner />)

    await user.click(screen.getByRole('button', { name: /Project settings/i }))
    await waitFor(() => expect(screen.getByLabelText(/Project name/i)).toBeInTheDocument())

    expect(screen.getByDisplayValue('My Project')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^Save$/i })).toBeInTheDocument()
  })

  it('does not show Environment access section for Free/Basic plan', async () => {
    const user = userEvent.setup()
    render(<ProjectSettingsModal projectId={1} me={me} projectName="My Project" isOwner />)

    await user.click(screen.getByRole('button', { name: /Project settings/i }))
    await waitFor(() => expect(screen.getByText('Project settings')).toBeInTheDocument())

    expect(screen.queryByText(/Environment access/i)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Save environment access/i })).not.toBeInTheDocument()
  })

  it('does not show email alert settings for non-owner', async () => {
    const user = userEvent.setup()
    render(<ProjectSettingsModal projectId={1} me={me} isOwner={false} />)

    await user.click(screen.getByRole('button', { name: /Project settings/i }))
    await waitFor(() => expect(screen.getByText('Project settings')).toBeInTheDocument())

    expect(screen.queryByRole('button', { name: /Save alert settings/i })).not.toBeInTheDocument()
    expect(api.fetchJson).not.toHaveBeenCalledWith('/api/user/projects/1/alert-settings')
  })

  it('validates empty project name on save', async () => {
    const user = userEvent.setup()
    render(<ProjectSettingsModal projectId={1} me={me} projectName="My Project" isOwner />)

    await user.click(screen.getByRole('button', { name: /Project settings/i }))
    await waitFor(() => expect(screen.getByLabelText(/Project name/i)).toBeInTheDocument())

    await user.clear(screen.getByLabelText(/Project name/i))
    await user.click(screen.getByRole('button', { name: /^Save$/i }))

    await waitFor(() => {
      expect(screen.getByText(/Name is required/i)).toBeInTheDocument()
    })
    expect(api.fetchJson).not.toHaveBeenCalledWith(
      '/api/user/projects/1',
      expect.objectContaining({ method: 'PATCH' })
    )
  })

  it('saves project name and calls onProjectNameUpdated', async () => {
    const user = userEvent.setup()
    const onProjectNameUpdated = vi.fn()
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/team/members') return Promise.resolve([])
      if (url === '/api/user/projects/1/environments') return Promise.resolve([])
      if (url === '/api/user/projects/1') return Promise.resolve({ name: 'Updated Name' })
      if (url === '/api/user/projects/1/alert-settings') {
        return Promise.resolve({
          enabled: false,
          cooldown_minutes: null,
          additional_emails: [],
          min_cooldown_minutes: 10,
        })
      }
      return Promise.resolve([])
    })

    render(
      <ProjectSettingsModal
        projectId={1}
        me={me}
        projectName="My Project"
        isOwner
        onProjectNameUpdated={onProjectNameUpdated}
      />
    )

    await user.click(screen.getByRole('button', { name: /Project settings/i }))
    await waitFor(() => expect(screen.getByLabelText(/Project name/i)).toBeInTheDocument())

    await user.clear(screen.getByLabelText(/Project name/i))
    await user.type(screen.getByLabelText(/Project name/i), 'Updated Name')
    await user.click(screen.getByRole('button', { name: /^Save$/i }))

    await waitFor(() => {
      expect(api.fetchJson).toHaveBeenCalledWith(
        '/api/user/projects/1',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({ name: 'Updated Name' }),
        })
      )
    })
    expect(onProjectNameUpdated).toHaveBeenCalledWith('Updated Name')
  })

  it('shows error when save fails', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/team/members') return Promise.resolve([])
      if (url === '/api/user/projects/1/environments') return Promise.resolve([])
      if (url === '/api/user/projects/1/alert-settings') {
        return Promise.resolve({
          enabled: false,
          cooldown_minutes: null,
          additional_emails: [],
          min_cooldown_minutes: 10,
        })
      }
      if (url === '/api/user/projects/1') return Promise.reject(new Error('Network error'))
      return Promise.resolve([])
    })

    render(<ProjectSettingsModal projectId={1} me={me} projectName="My Project" isOwner />)

    await user.click(screen.getByRole('button', { name: /Project settings/i }))
    await waitFor(() => expect(screen.getByLabelText(/Project name/i)).toBeInTheDocument())

    await user.clear(screen.getByLabelText(/Project name/i))
    await user.type(screen.getByLabelText(/Project name/i), 'New Name')
    await user.click(screen.getByRole('button', { name: /^Save$/i }))

    await waitFor(() => {
      expect(screen.getByText(/Network error/i)).toBeInTheDocument()
    })
  })

  it('shows success message when environment access is saved', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockImplementation((url, opts) => {
      if (url === '/api/user/team/members') {
        return Promise.resolve([{ user_id: 2, email: 'member@example.com', project_ids: [1] }])
      }
      if (url === '/api/user/projects/1/environments') {
        return Promise.resolve([{ environment: 'production' }, { environment: 'staging' }])
      }
      if (url === '/api/user/projects/1/members/2/environments') {
        if (opts?.method === 'PUT') return Promise.resolve({ ok: true })
        return Promise.resolve([])
      }
      if (url === '/api/user/projects/1/alert-settings') {
        return Promise.resolve({
          enabled: false,
          cooldown_minutes: null,
          additional_emails: [],
          min_cooldown_minutes: 10,
        })
      }
      return Promise.resolve([])
    })

    render(<ProjectSettingsModal projectId={1} me={meTeams} projectName="My Project" isOwner />)

    await user.click(screen.getByRole('button', { name: /Project settings/i }))
    await waitFor(() => expect(screen.getByRole('button', { name: /Save environment access/i })).toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: /Save environment access/i }))

    await waitFor(() => {
      expect(screen.getByText(/Environment access saved\./i)).toBeInTheDocument()
    })
  })

  it('shows empty team and environments when team members fetch fails', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/team/members') return Promise.reject(new Error('Network error'))
      if (url === '/api/user/projects/1/environments') return Promise.resolve([])
      if (url === '/api/user/projects/1/alert-settings') {
        return Promise.resolve({
          enabled: false,
          cooldown_minutes: null,
          additional_emails: [],
          min_cooldown_minutes: 10,
        })
      }
      return Promise.resolve([])
    })

    render(<ProjectSettingsModal projectId={1} me={meTeams} projectName="My Project" isOwner />)
    await user.click(screen.getByRole('button', { name: /Project settings/i }))
    await waitFor(() => expect(screen.getByText('Project settings')).toBeInTheDocument())
    expect(screen.getByText(/No team members assigned to this project/i)).toBeInTheDocument()
  })

  it('shows empty environment options when environments fetch fails', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/team/members') return Promise.resolve([])
      if (url === '/api/user/projects/1/environments') return Promise.reject(new Error('Failed'))
      if (url === '/api/user/projects/1/alert-settings') {
        return Promise.resolve({
          enabled: false,
          cooldown_minutes: null,
          additional_emails: [],
          min_cooldown_minutes: 10,
        })
      }
      return Promise.resolve([])
    })

    render(<ProjectSettingsModal projectId={1} me={meTeams} projectName="My Project" isOwner />)
    await user.click(screen.getByRole('button', { name: /Project settings/i }))
    await waitFor(() => expect(screen.getByText('Project settings')).toBeInTheDocument())
  })

  it('shows no environments detected when owner has members but environments list is empty', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockImplementation((url, opts) => {
      if (url === '/api/user/team/members') {
        return Promise.resolve([{ user_id: 2, email: 'member@example.com', project_ids: [1] }])
      }
      if (url === '/api/user/projects/1/environments') {
        return Promise.resolve([])
      }
      if (url === '/api/user/projects/1/members/2/environments' && opts?.method !== 'PUT') {
        return Promise.resolve([])
      }
      if (url === '/api/user/projects/1/alert-settings') {
        return Promise.resolve({
          enabled: false,
          cooldown_minutes: null,
          additional_emails: [],
          min_cooldown_minutes: 10,
        })
      }
      return Promise.resolve([])
    })

    render(<ProjectSettingsModal projectId={1} me={meTeams} projectName="My Project" isOwner />)
    await user.click(screen.getByRole('button', { name: /Project settings/i }))
    await waitFor(() => expect(screen.getAllByText(/No environments detected yet/i).length).toBeGreaterThan(0))
  })

  it('unchecks environment and shows error when save environment access fails', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockImplementation((url, opts) => {
      if (url === '/api/user/team/members') {
        return Promise.resolve([{ user_id: 2, email: 'member@example.com', project_ids: [1] }])
      }
      if (url === '/api/user/projects/1/environments') {
        return Promise.resolve([{ environment: 'production' }, { environment: 'staging' }])
      }
      if (url === '/api/user/projects/1/members/2/environments') {
        if (opts?.method === 'PUT') return Promise.reject(new Error('Failed to save environment access'))
        return Promise.resolve(['production'])
      }
      if (url === '/api/user/projects/1/alert-settings') {
        return Promise.resolve({
          enabled: false,
          cooldown_minutes: null,
          additional_emails: [],
          min_cooldown_minutes: 10,
        })
      }
      return Promise.resolve([])
    })

    render(<ProjectSettingsModal projectId={1} me={meTeams} projectName="My Project" isOwner />)
    await user.click(screen.getByRole('button', { name: /Project settings/i }))
    await waitFor(() => expect(screen.getByRole('button', { name: /Save environment access/i })).toBeInTheDocument())
    await user.click(screen.getAllByLabelText('staging')[0])
    await user.click(screen.getByRole('button', { name: /Save environment access/i }))
    await waitFor(() => {
      expect(screen.getByText(/Failed to save environment access/i)).toBeInTheDocument()
    })
  })

  it('loads member environments and unchecking env updates selection', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockImplementation((url, opts) => {
      if (url === '/api/user/team/members') {
        return Promise.resolve([{ user_id: 2, email: 'member@example.com', project_ids: [1] }])
      }
      if (url === '/api/user/projects/1/environments') {
        return Promise.resolve([{ environment: 'production' }, { environment: 'staging' }])
      }
      if (url === '/api/user/projects/1/members/2/environments') {
        if (opts?.method === 'PUT') return Promise.resolve({ ok: true })
        return Promise.resolve(['production', 'staging'])
      }
      if (url === '/api/user/projects/1/alert-settings') {
        return Promise.resolve({
          enabled: false,
          cooldown_minutes: null,
          additional_emails: [],
          min_cooldown_minutes: 10,
        })
      }
      return Promise.resolve([])
    })

    render(<ProjectSettingsModal projectId={1} me={meTeams} projectName="My Project" isOwner />)
    await user.click(screen.getByRole('button', { name: /Project settings/i }))
    await waitFor(() => expect(screen.getAllByLabelText('production')[0]).toBeInTheDocument())
    const stagingCheckbox = screen.getAllByLabelText('staging')[0]
    expect(stagingCheckbox).toBeChecked()
    await user.click(stagingCheckbox)
    expect(stagingCheckbox).not.toBeChecked()
  })

  it('changing selected member in dropdown loads that member environments', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockImplementation((url, opts) => {
      if (url === '/api/user/team/members') {
        return Promise.resolve([
          { user_id: 2, email: 'member@example.com', project_ids: [1] },
          { user_id: 3, email: 'other@example.com', project_ids: [1] },
        ])
      }
      if (url === '/api/user/projects/1/environments') {
        return Promise.resolve([{ environment: 'production' }, { environment: 'staging' }])
      }
      if (url === '/api/user/projects/1/members/2/environments') {
        if (opts?.method === 'PUT') return Promise.resolve({ ok: true })
        return Promise.resolve(['production'])
      }
      if (url === '/api/user/projects/1/members/3/environments') {
        if (opts?.method === 'PUT') return Promise.resolve({ ok: true })
        return Promise.resolve(['staging'])
      }
      if (url === '/api/user/projects/1/alert-settings') {
        return Promise.resolve({
          enabled: false,
          cooldown_minutes: null,
          additional_emails: [],
          min_cooldown_minutes: 10,
        })
      }
      return Promise.resolve([])
    })

    render(<ProjectSettingsModal projectId={1} me={meTeams} projectName="My Project" isOwner />)
    await user.click(screen.getByRole('button', { name: /Project settings/i }))
    await waitFor(() => expect(screen.getByRole('combobox')).toBeInTheDocument())

    const select = screen.getByRole('combobox')
    await user.selectOptions(select, '3')
    await waitFor(() => {
      expect(api.fetchJson).toHaveBeenCalledWith('/api/user/projects/1/members/3/environments')
    })
    expect(select).toHaveValue('3')
  })

  it('resets member env selection when member environments fetch fails', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/team/members') {
        return Promise.resolve([{ user_id: 2, email: 'member@example.com', project_ids: [1] }])
      }
      if (url === '/api/user/projects/1/environments') return Promise.resolve([])
      if (url === '/api/user/projects/1/members/2/environments') {
        return Promise.reject(new Error('Failed'))
      }
      if (url === '/api/user/projects/1/alert-settings') {
        return Promise.resolve({
          enabled: false,
          cooldown_minutes: null,
          additional_emails: [],
          min_cooldown_minutes: 10,
        })
      }
      return Promise.resolve([])
    })

    render(<ProjectSettingsModal projectId={1} me={meTeams} projectName="My Project" isOwner />)
    await user.click(screen.getByRole('button', { name: /Project settings/i }))
    await waitFor(() => expect(screen.getByRole('combobox')).toBeInTheDocument())
  })

  it('toggles Project name section when section header is clicked', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/team/members') return Promise.resolve([])
      if (url === '/api/user/projects/1/environments') return Promise.resolve([])
      if (url === '/api/user/projects/1/alert-settings') {
        return Promise.resolve({
          enabled: false,
          cooldown_minutes: null,
          additional_emails: [],
          min_cooldown_minutes: 10,
        })
      }
      return Promise.resolve([])
    })

    render(<ProjectSettingsModal projectId={1} me={me} projectName="My Project" isOwner />)
    await user.click(screen.getByRole('button', { name: /Project settings/i }))
    await waitFor(() => expect(screen.getByLabelText(/Project name/i)).toBeInTheDocument())

    const projectNameHeader = screen.getByRole('button', { name: /Project name/i })
    await user.click(projectNameHeader)
    await waitFor(() => {
      expect(screen.queryByLabelText(/Project name/i)).not.toBeInTheDocument()
    })
    await user.click(projectNameHeader)
    await waitFor(() => {
      expect(screen.getByLabelText(/Project name/i)).toBeInTheDocument()
    })
  })

  it('toggles Email alerts section when section header is clicked', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/team/members') return Promise.resolve([])
      if (url === '/api/user/projects/1/environments') return Promise.resolve([])
      if (url === '/api/user/projects/1/alert-settings') {
        return Promise.resolve({
          enabled: false,
          cooldown_minutes: null,
          additional_emails: [],
          min_cooldown_minutes: 10,
        })
      }
      return Promise.resolve([])
    })

    render(<ProjectSettingsModal projectId={1} me={me} projectName="My Project" isOwner />)
    await user.click(screen.getByRole('button', { name: /Project settings/i }))
    await waitFor(() => expect(screen.getByRole('button', { name: /Email alerts/i })).toBeInTheDocument())

    const emailAlertsHeader = screen.getByRole('button', { name: /Email alerts/i })
    expect(screen.getByRole('button', { name: /Save alert settings/i })).toBeInTheDocument()
    await user.click(emailAlertsHeader)
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /Save alert settings/i })).not.toBeInTheDocument()
    })
    await user.click(emailAlertsHeader)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Save alert settings/i })).toBeInTheDocument()
    })
  })

  it('project name input is associated with label and accepts change', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/team/members') return Promise.resolve([])
      if (url === '/api/user/projects/1/environments') return Promise.resolve([])
      if (url === '/api/user/projects/1/alert-settings') {
        return Promise.resolve({
          enabled: false,
          cooldown_minutes: null,
          additional_emails: [],
          min_cooldown_minutes: 10,
        })
      }
      return Promise.resolve([])
    })

    render(<ProjectSettingsModal projectId={1} me={me} projectName="My Project" isOwner />)
    await user.click(screen.getByRole('button', { name: /Project settings/i }))
    await waitFor(() => expect(screen.getByLabelText(/Project name/i)).toBeInTheDocument())

    const input = document.getElementById('project-name-input')
    expect(input).toBeInTheDocument()
    await user.clear(input)
    await user.type(input, 'New Project Name')
    expect(input).toHaveValue('New Project Name')
  })
})
