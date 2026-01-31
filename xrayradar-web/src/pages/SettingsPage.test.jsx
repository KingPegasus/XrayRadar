import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SettingsPage } from './SettingsPage'
import * as api from '../utils/api'

vi.mock('../utils/api')

describe('SettingsPage', () => {
  const me = { email: 'test@example.com', email_verified: true, plan: 'Free', created_at: '2024-01-01T00:00:00Z' }

  beforeEach(() => {
    vi.clearAllMocks()
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/usage') {
        return Promise.resolve({
          current_count: 100,
          limit: 5000,
          plan: 'Free',
          percentage_used: 2,
          is_exceeded: false,
          is_near_limit: false,
        })
      }
      if (url === '/api/user/deletion-request') {
        return Promise.resolve(null)
      }
      return Promise.resolve({})
    })
  })

  it('renders account settings page', async () => {
    render(<SettingsPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText('Account Settings')).toBeInTheDocument()
    })
    expect(screen.getByText(/Manage your account and view usage/i)).toBeInTheDocument()
  })

  it('shows AccountInfoCard with user email', async () => {
    render(<SettingsPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText('test@example.com')).toBeInTheDocument()
    })
    expect(screen.getByText('Account')).toBeInTheDocument()
  })

  it('shows usage when loaded', async () => {
    render(<SettingsPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText(/100/)).toBeInTheDocument()
    })
  })

  it('shows error when usage fetch fails', async () => {
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/usage') {
        return Promise.reject(new Error('Failed to load usage'))
      }
      if (url === '/api/user/deletion-request') {
        return Promise.resolve(null)
      }
      return Promise.resolve({})
    })

    render(<SettingsPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load usage/i)).toBeInTheDocument()
    })
  })

  it('shows fallback error when usage fetch fails with no message', async () => {
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/usage') {
        return Promise.reject(new Error())
      }
      if (url === '/api/user/deletion-request') {
        return Promise.resolve(null)
      }
      return Promise.resolve({})
    })

    render(<SettingsPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load usage/i)).toBeInTheDocument()
    })
  })

  it('shows loading state initially', () => {
    api.fetchJson.mockImplementation(() => new Promise(() => {}))

    render(<SettingsPage me={me} />)
    expect(screen.getByText(/Loading usage/i)).toBeInTheDocument()
  })
})
