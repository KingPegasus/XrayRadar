import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { fireEvent } from '@testing-library/react'
import { Logo } from './Logo'

describe('Logo', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders logo image with default props', () => {
    render(<Logo />)

    const img = screen.getByRole('img', { hidden: true })
    expect(img).toBeInTheDocument()
    expect(img).toHaveAttribute('width', '120')
    expect(img).toHaveAttribute('height', '36')
  })

  it('renders logo image with custom props', () => {
    render(<Logo width={200} height={50} className="custom-class" />)

    const img = screen.getByRole('img', { hidden: true })
    expect(img).toHaveAttribute('width', '200')
    expect(img).toHaveAttribute('height', '50')
    expect(img).toHaveClass('custom-class')
  })

  it('calls onError callback when image fails to load', async () => {
    const onError = vi.fn()
    const { container } = render(<Logo onError={onError} />)

    const img = container.querySelector('img')
    expect(img).toBeInTheDocument()
    
    // Simulate image load error
    fireEvent.error(img)

    await waitFor(() => {
      expect(onError).toHaveBeenCalledTimes(1)
    })
  })

  it('returns null after error', async () => {
    const onError = vi.fn()
    const { container } = render(<Logo onError={onError} />)

    const img = container.querySelector('img')
    expect(img).toBeInTheDocument()
    
    // Trigger error
    fireEvent.error(img)

    await waitFor(() => {
      expect(onError).toHaveBeenCalled()
    })

    // After error, component should return null
    await waitFor(() => {
      const updatedImg = container.querySelector('img')
      expect(updatedImg).toBeNull()
    })
  })

  it('handles error without onError callback', async () => {
    const { container } = render(<Logo />)

    const img = container.querySelector('img')
    expect(img).toBeInTheDocument()
    
    // Trigger error
    fireEvent.error(img)

    // Should not throw, just return null
    await waitFor(() => {
      const updatedImg = container.querySelector('img')
      expect(updatedImg).toBeNull()
    })
  })
})
