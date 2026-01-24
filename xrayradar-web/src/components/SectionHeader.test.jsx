import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SectionHeader } from './SectionHeader'

describe('SectionHeader', () => {
  it('renders title', () => {
    render(<SectionHeader title="Test Title" />)
    expect(screen.getByText('Test Title')).toBeInTheDocument()
  })

  it('renders description when provided', () => {
    render(<SectionHeader title="Test Title" desc="Test description" />)
    expect(screen.getByText('Test description')).toBeInTheDocument()
  })

  it('does not render description when not provided', () => {
    render(<SectionHeader title="Test Title" />)
    expect(screen.queryByText('Test description')).not.toBeInTheDocument()
  })

  it('handles null description', () => {
    render(<SectionHeader title="Test Title" desc={null} />)
    expect(screen.queryByText('Test description')).not.toBeInTheDocument()
  })
})
