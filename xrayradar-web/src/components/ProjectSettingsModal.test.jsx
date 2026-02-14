import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { fireEvent } from '@testing-library/react'
import { ProjectSettingsModal } from './ProjectSettingsModal'
import * as api from '../utils/api'

vi.mock('../utils/api')

describe('ProjectSettingsModal', () => {
  const me = { email: 'test@example.com', email_verified: true }

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
})
