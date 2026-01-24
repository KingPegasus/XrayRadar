import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { Check } from './Check'

describe('Check', () => {
  it('renders dot span', () => {
    const { container } = render(<Check />)
    const dot = container.querySelector('.dot')
    expect(dot).toBeInTheDocument()
    expect(dot).toHaveAttribute('aria-hidden', 'true')
  })
})
