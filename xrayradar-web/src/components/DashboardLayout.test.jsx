import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DashboardLayout } from './DashboardLayout'

vi.mock('./Link', () => ({
  Link: ({ to, children, className }) => <a href={to} className={className}>{children}</a>,
}))

describe('DashboardLayout', () => {
  it('renders header with navigation', () => {
    const me = { email: 'test@example.com' }
    const onLogout = vi.fn()
    render(
      <DashboardLayout me={me} onLogout={onLogout}>
        <div>Test Content</div>
      </DashboardLayout>
    )

    expect(screen.getByText('Xrayradar')).toBeInTheDocument()
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
