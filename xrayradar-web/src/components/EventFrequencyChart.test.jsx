import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { EventFrequencyChart } from './EventFrequencyChart'

describe('EventFrequencyChart', () => {
  it('returns null when eventFrequency is undefined', () => {
    const { container } = render(<EventFrequencyChart eventFrequency={undefined} />)
    expect(container.firstChild).toBeNull()
  })

  it('returns null when eventFrequency.data is empty', () => {
    const { container } = render(
      <EventFrequencyChart eventFrequency={{ data: [], maxCount: 0, total: 0 }} />
    )
    expect(container.firstChild).toBeNull()
  })

  it('returns null when eventFrequency.data is missing', () => {
    const { container } = render(
      <EventFrequencyChart eventFrequency={{ maxCount: 0, total: 0 }} />
    )
    expect(container.firstChild).toBeNull()
  })

  it('renders chart with data', () => {
    render(
      <EventFrequencyChart
        eventFrequency={{
          data: [['2024-01-01', 5], ['2024-01-02', 3]],
          maxCount: 5,
          total: 8,
        }}
      />
    )
    expect(screen.getByText('Event Frequency')).toBeInTheDocument()
    expect(screen.getByText(/Total: 8 events across 2 days/i)).toBeInTheDocument()
  })
})
