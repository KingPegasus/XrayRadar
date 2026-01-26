import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { DashboardLayout } from './DashboardLayout'

vi.mock('./Link', () => ({
  Link: ({ to, children, className }) => <a href={to} className={className}>{children}</a>,
}))

vi.mock('./Logo', () => ({
  Logo: ({ onError }) => {
    // Trigger error callback after render to show fallback text
    if (onError) {
      // Use setTimeout to avoid React warning about updating during render
      setTimeout(() => onError(), 0)
    }
    return null
  },
}))

describe('DashboardLayout', () => {
  it('renders header with navigation', async () => {
    const me = { email: 'test@example.com' }
    const onLogout = vi.fn()
    render(
      <DashboardLayout me={me} onLogout={onLogout}>
        <div>Test Content</div>
      </DashboardLayout>
    )

    // Wait for logo error to trigger and show fallback text
    await waitFor(() => {
      expect(screen.getByText('XrayRadar')).toBeInTheDocument()
    })
    expect(screen.getByRole('link', { name: /Projects/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Tokens/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Sign out/i })).toBeInTheDocument()
  })

  it('renders children', () => {
    const me = { email: 'test@example.com' }
    const onLogout = vi.fn()
    render(
      <DashboardLayout me={me} onLogout={onLogout}>
        <div>Test Content</div>
      </DashboardLayout>
    )

    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('calls onLogout when sign out is clicked', async () => {
    const user = await import('@testing-library/user-event').then(m => m.default.setup())
    const me = { email: 'test@example.com' }
    const onLogout = vi.fn()
    render(
      <DashboardLayout me={me} onLogout={onLogout}>
        <div>Test Content</div>
      </DashboardLayout>
    )

    const signOutButton = screen.getByRole('button', { name: /Sign out/i })
    await user.click(signOutButton)
    expect(onLogout).toHaveBeenCalledTimes(1)
  })
})
