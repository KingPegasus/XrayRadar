import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { EmailAlertSettings } from './EmailAlertSettings'
import * as api from '../utils/api'

vi.mock('../utils/api')

describe('EmailAlertSettings', () => {
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

  it('renders alert settings', async () => {
    render(<EmailAlertSettings projectId={1} me={me} />)

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

    render(<EmailAlertSettings projectId={1} me={me} />)

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

    render(<EmailAlertSettings projectId={1} me={me} />)

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

    render(<EmailAlertSettings projectId={1} me={me} />)

    await waitFor(() => {
      expect(screen.getByDisplayValue('10')).toBeInTheDocument()
      expect(screen.getByText(/Minimum 10 minutes for your plan/i)).toBeInTheDocument()
    })
  })

  it('toggles alert checkbox', async () => {
    const user = userEvent.setup()
    render(<EmailAlertSettings projectId={1} me={me} />)

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

    render(<EmailAlertSettings projectId={1} me={me} />)

    await waitFor(() => expect(screen.getByText('a@b.com')).toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: /Remove a@b.com/i }))

    expect(screen.queryByText('a@b.com')).not.toBeInTheDocument()
    expect(screen.getByText('c@d.com')).toBeInTheDocument()
  })

  it('adds email via Enter key', async () => {
    const user = userEvent.setup()
    render(<EmailAlertSettings projectId={1} me={me} />)

    await waitFor(() => expect(screen.getByPlaceholderText(/Add email/i)).toBeInTheDocument())

    const input = screen.getByPlaceholderText(/Add email/i)
    await user.type(input, 'new@example.com{Enter}')

    expect(screen.getByText('new@example.com')).toBeInTheDocument()
  })

  it('shows cooldown validation error when below min', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockResolvedValue({ enabled: false, cooldown_minutes: null, additional_emails: [], min_cooldown_minutes: 10 })

    render(<EmailAlertSettings projectId={1} me={me} />)

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
    api.fetchJson
      .mockResolvedValueOnce({ enabled: false, cooldown_minutes: null, additional_emails: [], min_cooldown_minutes: 10 })
      .mockRejectedValueOnce(new Error('Server error'))

    render(<EmailAlertSettings projectId={1} me={me} />)

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

  it('renders compact mode when compact=true (Basic plan)', async () => {
    api.fetchJson.mockResolvedValue({ enabled: false, cooldown_minutes: null, additional_emails: [], min_cooldown_minutes: 10 })

    render(<EmailAlertSettings projectId={1} me={me} compact />)

    await waitFor(() => expect(screen.getByText(/Email alerts for errors/i)).toBeInTheDocument())
    expect(screen.queryByText(/^Email alerts$/)).not.toBeInTheDocument()
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

  it('does not add duplicate email via Add button', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockResolvedValue({
      enabled: false,
      cooldown_minutes: null,
      additional_emails: ['existing@example.com'],
      min_cooldown_minutes: 10,
    })

    render(<EmailAlertSettings projectId={1} me={me} />)

    await waitFor(() => expect(screen.getByText('existing@example.com')).toBeInTheDocument())

    await user.type(screen.getByPlaceholderText(/Add email/i), 'existing@example.com')
    await user.click(screen.getByRole('button', { name: /Add/i }))

    expect(screen.getAllByText('existing@example.com').length).toBe(1)
  })

  it('does not add empty email via Enter key', async () => {
    const user = userEvent.setup()
    render(<EmailAlertSettings projectId={1} me={me} />)

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
    api.fetchJson
      .mockResolvedValueOnce({ enabled: false, cooldown_minutes: null, additional_emails: [], min_cooldown_minutes: 10 })
      .mockRejectedValueOnce(err)

    render(<EmailAlertSettings projectId={1} me={me} />)

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
    api.fetchJson
      .mockResolvedValueOnce({ enabled: false, cooldown_minutes: null, additional_emails: [], min_cooldown_minutes: 10 })
      .mockRejectedValueOnce(err)

    render(<EmailAlertSettings projectId={1} me={me} />)

    await waitFor(() => expect(screen.getByRole('button', { name: /Save alert settings/i })).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: /Save alert settings/i }))

    await waitFor(() => {
      expect(screen.getByText(/Failed to save/i)).toBeInTheDocument()
    })
  })
})
