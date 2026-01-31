import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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

    // Click the dialog backdrop (outer div) - dispatch click on the dialog element
    const dialog = screen.getByRole('dialog')
    dialog.click()
    await waitFor(() => {
      expect(screen.queryByText('Project settings')).not.toBeInTheDocument()
    })
  })
})
