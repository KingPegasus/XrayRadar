import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { EmailAlertSettings } from './EmailAlertSettings'
import * as api from '../utils/api'

vi.mock('../utils/api')

describe('EmailAlertSettings', () => {
  const me = { email: 'test@example.com', email_verified: true }
  const meBasic = { ...me, plan: 'Basic' }
  const meTeams = { ...me, plan: 'Teams' }
  const meTeamsPro = { ...me, plan: 'Teams Pro' }

  beforeEach(() => {
    vi.clearAllMocks()
    api.fetchJson.mockResolvedValue({
      enabled: false,
      cooldown_minutes: null,
      additional_emails: [],
      min_cooldown_minutes: 10,
    })
  })

  it('renders alert settings', async () => {
    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => {
      expect(screen.getByText(/Email alerts for errors/i)).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/Add email/i)).toBeInTheDocument()
    })
  })

  it('adds email and saves', async () => {
    const user = userEvent.setup()
    api.fetchJson
      .mockResolvedValueOnce({ enabled: false, cooldown_minutes: null, additional_emails: [], min_cooldown_minutes: 10 })
      .mockResolvedValueOnce({})

    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => expect(screen.getByPlaceholderText(/Add email/i)).toBeInTheDocument())

    await user.type(screen.getByPlaceholderText(/Add email/i), 'alert@example.com')
    await user.click(screen.getByRole('button', { name: /Add/i }))

    expect(screen.getByText('alert@example.com')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /Save alert settings/i }))

    await waitFor(() => {
      expect(api.fetchJson).toHaveBeenCalledWith(
        '/api/user/projects/1/alert-settings',
        expect.objectContaining({
          method: 'PATCH',
          body: expect.stringContaining('alert@example.com'),
        })
      )
    })
    expect(screen.getByText(/Alert settings saved\./i)).toBeInTheDocument()
  })

  it('shows verify email message when not verified', async () => {
    render(<EmailAlertSettings projectId={1} me={{ ...me, email_verified: false }} />)

    await waitFor(() => {
      expect(screen.getByText(/Verify your email to save alert settings/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Save alert settings/i })).toBeDisabled()
    })
  })

  it('handles fetch error on load', async () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    api.fetchJson.mockRejectedValueOnce(new Error('Failed to load'))

    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Failed to load alert settings:', expect.any(Error))
    })
    consoleSpy.mockRestore()
  })

  it('loads with clamped cooldown when stored < min', async () => {
    api.fetchJson.mockResolvedValue({
      enabled: true,
      cooldown_minutes: 5,
      min_cooldown_minutes: 10,
      additional_emails: [],
    })

    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => {
      expect(screen.getByDisplayValue('10')).toBeInTheDocument()
      expect(screen.getByText(/Minimum 10 minutes for your plan/i)).toBeInTheDocument()
    })
  })

  it('toggles alert checkbox', async () => {
    const user = userEvent.setup()
    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => expect(screen.getByLabelText(/Email alerts for errors/i)).toBeInTheDocument())

    const checkbox = screen.getByLabelText(/Email alerts for errors/i)
    await user.click(checkbox)
    expect(checkbox).toBeChecked()
  })

  it('removes email from list', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockResolvedValue({
      enabled: false,
      cooldown_minutes: null,
      additional_emails: ['a@b.com', 'c@d.com'],
      min_cooldown_minutes: 10,
    })

    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => expect(screen.getByText('a@b.com')).toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: /Remove a@b.com/i }))

    expect(screen.queryByText('a@b.com')).not.toBeInTheDocument()
    expect(screen.getByText('c@d.com')).toBeInTheDocument()
  })

  it('adds email via Enter key', async () => {
    const user = userEvent.setup()
    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => expect(screen.getByPlaceholderText(/Add email/i)).toBeInTheDocument())

    const input = screen.getByPlaceholderText(/Add email/i)
    await user.type(input, 'new@example.com{Enter}')

    expect(screen.getByText('new@example.com')).toBeInTheDocument()
  })

  it('shows cooldown validation error when below min', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockResolvedValue({ enabled: false, cooldown_minutes: null, additional_emails: [], min_cooldown_minutes: 10 })

    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => expect(screen.getByPlaceholderText(/Add email/i)).toBeInTheDocument())

    const cooldownInput = screen.getByRole('spinbutton', { name: /Cooldown/i }) || screen.getByPlaceholderText('None')
    await user.type(cooldownInput, '5')
    await user.click(screen.getByRole('button', { name: /Save alert settings/i }))

    await waitFor(() => {
      expect(screen.getByText(/Cooldown minimum for your plan is 10 minutes/i)).toBeInTheDocument()
    })
  })

  it('shows error when save fails', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockImplementation((url, opts) => {
      if (opts?.method === 'PATCH') return Promise.reject(new Error('Server error'))
      if (url === '/api/user/projects/1/environments') return Promise.resolve([])
      return Promise.resolve({ enabled: false, cooldown_minutes: null, additional_emails: [], min_cooldown_minutes: 10 })
    })

    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => expect(screen.getByRole('button', { name: /Save alert settings/i })).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: /Save alert settings/i }))

    await waitFor(() => {
      expect(screen.getByText(/Server error/i)).toBeInTheDocument()
    })
  })

  it('shows upgrade message for Free plan (min_cooldown_minutes null)', async () => {
    api.fetchJson.mockResolvedValue({ enabled: false, cooldown_minutes: null, additional_emails: [], min_cooldown_minutes: null })

    render(<EmailAlertSettings projectId={1} me={me} />)

    await waitFor(() => {
      expect(screen.getByText(/Email alerts are not available on the Free plan/i)).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /Contact to Upgrade/i })).toBeInTheDocument()
    })
    expect(screen.queryByText(/Email alerts for errors/i)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Save alert settings/i })).not.toBeInTheDocument()
  })

  it('Teams Pro plan: shows 1 min cooldown and environment-specific section when envs exist', async () => {
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/projects/1/environments') {
        return Promise.resolve([{ environment: 'production' }])
      }
      return Promise.resolve({
        enabled: false,
        cooldown_minutes: null,
        additional_emails: [],
        min_cooldown_minutes: 1,
        environment_settings: [],
      })
    })
    render(<EmailAlertSettings projectId={1} me={meTeamsPro} projectName="Proj" />)
    await waitFor(() => {
      expect(screen.getByText(/Minimum 1 minute for your plan/i)).toBeInTheDocument()
      expect(screen.getByText(/Environment-specific alerts/i)).toBeInTheDocument()
    })
  })

  it('renders compact mode when compact=true (Basic plan)', async () => {
    api.fetchJson.mockResolvedValue({ enabled: false, cooldown_minutes: null, additional_emails: [], min_cooldown_minutes: 10 })

    render(<EmailAlertSettings projectId={1} me={meBasic} compact />)

    await waitFor(() => expect(screen.getByText(/Email alerts for errors/i)).toBeInTheDocument())
    expect(screen.queryByText(/^Email alerts$/)).not.toBeInTheDocument()
  })

  it('hides environment-specific alerts section for Basic plan', async () => {
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/projects/1/environments') {
        return Promise.resolve([{ environment: 'development' }])
      }
      return Promise.resolve({
        enabled: true,
        cooldown_minutes: 10,
        min_cooldown_minutes: 10,
        additional_emails: [],
        environment_settings: [
          {
            environment: 'development',
            enabled: true,
            cooldown_minutes: 15,
            additional_emails: ['dev@example.com'],
          },
        ],
      })
    })

    render(<EmailAlertSettings projectId={1} me={{ ...me, plan: 'Basic' }} projectName="basic-project" />)

    await waitFor(() => {
      expect(screen.getByText(/Project-wide alerts \(all events\)/i)).toBeInTheDocument()
    })
    expect(screen.queryByText(/Environment-specific alerts/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/\[XrayRadar\] \[development\] basic-project: Error digest/i)).not.toBeInTheDocument()
  })

  it('loads with stored cooldown when stored >= min', async () => {
    api.fetchJson.mockResolvedValue({
      enabled: false,
      cooldown_minutes: 15,
      min_cooldown_minutes: 10,
      additional_emails: [],
    })

    render(<EmailAlertSettings projectId={1} me={me} />)

    await waitFor(() => {
      expect(screen.getByDisplayValue('15')).toBeInTheDocument()
      expect(screen.getByText(/Minimum 10 minutes for your plan/i)).toBeInTheDocument()
    })
  })

  it('shows singular minute when minCooldownMinutes is 1', async () => {
    api.fetchJson.mockResolvedValue({
      enabled: false,
      cooldown_minutes: null,
      additional_emails: [],
      min_cooldown_minutes: 1,
    })

    render(<EmailAlertSettings projectId={1} me={me} />)

    await waitFor(() => {
      expect(screen.getByText(/Minimum 1 minute for your plan/i)).toBeInTheDocument()
    })
  })

  it('renders environment-specific section from environment_settings', async () => {
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/projects/1/environments') {
        return Promise.resolve([{ environment: 'development' }])
      }
      return Promise.resolve({
        enabled: true,
        cooldown_minutes: 10,
        min_cooldown_minutes: 10,
        additional_emails: [],
        environment_settings: [
          {
            environment: 'development',
            enabled: true,
            cooldown_minutes: 15,
            additional_emails: ['dev@example.com'],
          },
        ],
      })
    })
    render(<EmailAlertSettings projectId={1} me={meTeams} projectName="team1" />)

    await waitFor(() => {
      expect(screen.getByText(/Project-wide alerts \(all events\)/i)).toBeInTheDocument()
      expect(screen.getByText(/Environment-specific alerts/i)).toBeInTheDocument()
      expect(screen.getByText(/\[XrayRadar\] \[development\] team1: Error digest/i)).toBeInTheDocument()
      expect(screen.getByText('dev@example.com')).toBeInTheDocument()
    })
  })

  it('sends environment_settings in PATCH payload', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockImplementation((url, opts) => {
      if (url === '/api/user/projects/1/environments') {
        return Promise.resolve([{ environment: 'development' }])
      }
      if (opts?.method === 'PATCH') return Promise.resolve({})
      return Promise.resolve({
        enabled: true,
        cooldown_minutes: 10,
        min_cooldown_minutes: 10,
        additional_emails: [],
        environment_settings: [
          {
            environment: 'development',
            enabled: true,
            cooldown_minutes: 15,
            additional_emails: ['dev@example.com'],
          },
        ],
      })
    })

    render(<EmailAlertSettings projectId={1} me={meTeams} projectName="team1" />)
    await waitFor(() => expect(screen.getByRole('button', { name: /Save alert settings/i })).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: /Save alert settings/i }))

    await waitFor(() => {
      const patchCall = api.fetchJson.mock.calls.find((call) => call[1]?.method === 'PATCH')
      expect(patchCall).toBeTruthy()
      expect(patchCall[1].body).toContain('"environment_settings"')
      expect(patchCall[1].body).toContain('"environment":"development"')
    })
  })

  it('does not add duplicate email via Add button', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockResolvedValue({
      enabled: false,
      cooldown_minutes: null,
      additional_emails: ['existing@example.com'],
      min_cooldown_minutes: 10,
    })

    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => expect(screen.getByText('existing@example.com')).toBeInTheDocument())

    await user.type(screen.getByPlaceholderText(/Add email/i), 'existing@example.com')
    await user.click(screen.getByRole('button', { name: /Add/i }))

    expect(screen.getAllByText('existing@example.com').length).toBe(1)
  })

  it('does not add empty email via Enter key', async () => {
    const user = userEvent.setup()
    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => expect(screen.getByPlaceholderText(/Add email/i)).toBeInTheDocument())

    const input = screen.getByPlaceholderText(/Add email/i)
    await user.type(input, '{Enter}')

    expect(screen.queryByText(/@/)).not.toBeInTheDocument()
  })

  it('shows e.detail when save fails with detail', async () => {
    const user = userEvent.setup()
    const err = new Error()
    err.detail = 'Validation failed'
    err.message = ''
    api.fetchJson.mockImplementation((url, opts) => {
      if (opts?.method === 'PATCH') return Promise.reject(err)
      if (url === '/api/user/projects/1/environments') return Promise.resolve([])
      return Promise.resolve({ enabled: false, cooldown_minutes: null, additional_emails: [], min_cooldown_minutes: 10 })
    })

    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => expect(screen.getByRole('button', { name: /Save alert settings/i })).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: /Save alert settings/i }))

    await waitFor(() => {
      expect(screen.getByText(/Validation failed/i)).toBeInTheDocument()
    })
  })

  it('shows fallback when save fails with no message or detail', async () => {
    const user = userEvent.setup()
    const err = new Error()
    err.message = ''
    delete err.detail
    api.fetchJson.mockImplementation((url, opts) => {
      if (opts?.method === 'PATCH') return Promise.reject(err)
      if (url === '/api/user/projects/1/environments') return Promise.resolve([])
      return Promise.resolve({ enabled: false, cooldown_minutes: null, additional_emails: [], min_cooldown_minutes: 10 })
    })

    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => expect(screen.getByRole('button', { name: /Save alert settings/i })).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: /Save alert settings/i }))

    await waitFor(() => {
      expect(screen.getByText(/Failed to save/i)).toBeInTheDocument()
    })
  })

  it('removes email from environment override', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/projects/1/environments') {
        return Promise.resolve([{ environment: 'development' }])
      }
      return Promise.resolve({
        enabled: false,
        cooldown_minutes: null,
        min_cooldown_minutes: 10,
        additional_emails: [],
        environment_settings: [
          { environment: 'development', enabled: true, cooldown_minutes: null, additional_emails: ['dev@example.com', 'other@example.com'] },
        ],
      })
    })
    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => expect(screen.getByText('dev@example.com')).toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: /Remove dev@example.com from development/i }))

    await waitFor(() => {
      expect(screen.queryByText('dev@example.com')).not.toBeInTheDocument()
      expect(screen.getByText('other@example.com')).toBeInTheDocument()
    })
  })

  it('adds email for environment via Enter key and Add button', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/projects/1/environments') {
        return Promise.resolve([{ environment: 'staging' }])
      }
      return Promise.resolve({
        enabled: false,
        cooldown_minutes: null,
        min_cooldown_minutes: 10,
        additional_emails: [],
        environment_settings: [],
      })
    })
    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => expect(screen.getByPlaceholderText(/Add email for staging/i)).toBeInTheDocument())

    const envInput = screen.getByPlaceholderText(/Add email for staging/i)
    await user.type(envInput, 'staging@example.com{Enter}')
    await waitFor(() => expect(screen.getByText('staging@example.com')).toBeInTheDocument())

    await user.type(envInput, 'second@staging.com')
    const addButtons = screen.getAllByRole('button', { name: /Add/i })
    await user.click(addButtons[addButtons.length - 1])
    await waitFor(() => expect(screen.getByText('second@staging.com')).toBeInTheDocument())
  })

  it('removes environment override', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/projects/1/environments') {
        return Promise.resolve([{ environment: 'production' }])
      }
      return Promise.resolve({
        enabled: false,
        cooldown_minutes: null,
        min_cooldown_minutes: 10,
        additional_emails: [],
        environment_settings: [
          { environment: 'production', enabled: true, cooldown_minutes: null, additional_emails: [] },
        ],
      })
    })
    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => expect(screen.getByRole('button', { name: /Remove environment override/i })).toBeInTheDocument())

    const removeBtn = screen.getByRole('button', { name: /Remove environment override/i })
    await user.click(removeBtn)

    await waitFor(() => {
      expect(screen.getByText(/Environment-specific alerts/i)).toBeInTheDocument()
    })
  })

  it('shows cooldown validation error when env override cooldown below min', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/projects/1/environments') {
        return Promise.resolve([{ environment: 'development' }])
      }
      return Promise.resolve({
        enabled: false,
        cooldown_minutes: 10,
        min_cooldown_minutes: 10,
        additional_emails: [],
        environment_settings: [
          { environment: 'development', enabled: true, cooldown_minutes: 5, additional_emails: [] },
        ],
      })
    })
    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => expect(screen.getByDisplayValue('5')).toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: /Save alert settings/i }))

    await waitFor(() => {
      expect(screen.getByText(/Cooldown minimum for your plan is 10 minutes/i)).toBeInTheDocument()
    })
  })

  it('shows loading state with compact=true', async () => {
    let resolveSettings
    const settingsPromise = new Promise((resolve) => {
      resolveSettings = () => resolve({ enabled: false, cooldown_minutes: null, additional_emails: [], min_cooldown_minutes: 10 })
    })
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/projects/1/alert-settings') return settingsPromise
      if (url === '/api/user/projects/1/environments') return Promise.resolve([])
      return Promise.resolve({})
    })

    render(<EmailAlertSettings projectId={1} me={meBasic} compact />)

    expect(screen.getByText(/Loading…/i)).toBeInTheDocument()
    expect(screen.queryByText(/^Email alerts$/)).not.toBeInTheDocument()

    resolveSettings()
    await waitFor(() => expect(screen.getByText(/Email alerts for errors/i)).toBeInTheDocument())
  })

  it('loads with enabled true from API', async () => {
    api.fetchJson.mockResolvedValue({
      enabled: true,
      cooldown_minutes: 15,
      additional_emails: [],
      min_cooldown_minutes: 10,
    })

    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => {
      expect(screen.getByLabelText(/Email alerts for errors/i)).toBeChecked()
      expect(screen.getByDisplayValue('15')).toBeInTheDocument()
    })
  })

  it('does not add empty email via Add button', async () => {
    const user = userEvent.setup()
    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => expect(screen.getByPlaceholderText(/Add email/i)).toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: /Add/i }))

    expect(screen.queryByText(/@/)).not.toBeInTheDocument()
  })

  it('shows non-compact header and project-wide digest text when compact is false', async () => {
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/projects/1/environments') return Promise.resolve([])
      return Promise.resolve({ enabled: false, cooldown_minutes: null, additional_emails: [], min_cooldown_minutes: 10 })
    })

    render(<EmailAlertSettings projectId={1} me={meTeams} projectName="MyProject" />)

    await waitFor(() => {
      expect(screen.getByText(/^Email alerts$/)).toBeInTheDocument()
      expect(screen.getByText(/Project-wide alerts \(all events\)/i)).toBeInTheDocument()
      expect(screen.getByText(/Sends: \[XrayRadar\] MyProject: Error digest/i)).toBeInTheDocument()
    })
  })

  it('save success shows saved message and clears error', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockImplementation((url, opts) => {
      if (url === '/api/user/projects/1/environments') return Promise.resolve([])
      if (opts?.method === 'PATCH') return Promise.resolve({})
      return Promise.resolve({ enabled: false, cooldown_minutes: null, additional_emails: [], min_cooldown_minutes: 10 })
    })

    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => expect(screen.getByRole('button', { name: /Save alert settings/i })).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: /Save alert settings/i }))

    await waitFor(() => {
      expect(screen.getByText(/Alert settings saved\./i)).toBeInTheDocument()
    })
  })

  it('filters out empty environment names from options', async () => {
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/projects/1/environments') {
        return Promise.resolve([
          { environment: 'prod' },
          { environment: '' },
          { environment: '  ' },
        ])
      }
      return Promise.resolve({
        enabled: false,
        cooldown_minutes: null,
        additional_emails: [],
        min_cooldown_minutes: 10,
        environment_settings: [],
      })
    })

    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => {
      expect(screen.getByText(/Environment-specific alerts/i)).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/Add email for prod/i)).toBeInTheDocument()
    })
  })

  it('handles environments fetch failure and still loads settings', async () => {
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/projects/1/environments') return Promise.reject(new Error('Network error'))
      return Promise.resolve({ enabled: false, cooldown_minutes: null, additional_emails: [], min_cooldown_minutes: 10 })
    })

    render(<EmailAlertSettings projectId={1} me={meTeams} />)

    await waitFor(() => expect(screen.getByText(/Email alerts for errors/i)).toBeInTheDocument())
  })

  it('Free plan upgrade link uses empty string when me has no email', async () => {
    api.fetchJson.mockResolvedValue({ enabled: false, cooldown_minutes: null, additional_emails: [], min_cooldown_minutes: null })

    render(<EmailAlertSettings projectId={1} me={{}} />)

    await waitFor(() => {
      const link = screen.getByRole('link', { name: /Contact to Upgrade/i })
      expect(link).toHaveAttribute('href', expect.stringContaining('Email:%20'))
    })
  })
})
