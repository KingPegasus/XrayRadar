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

  it('renders chart without title when showTitle is false', () => {
    render(
      <EventFrequencyChart
        eventFrequency={{
          data: [['2024-01-01', 1]],
          maxCount: 1,
          total: 1,
        }}
        showTitle={false}
      />
    )
    expect(screen.queryByText('Event Frequency')).not.toBeInTheDocument()
    expect(screen.getByText(/Total: 1 event across 1 day/i)).toBeInTheDocument()
  })

  it('renders chart with zero-count bar (bar height branch)', () => {
    render(
      <EventFrequencyChart
        eventFrequency={{
          data: [['2024-01-01', 5], ['2024-01-02', 0], ['2024-01-03', 3]],
          maxCount: 5,
          total: 8,
        }}
      />
    )
    expect(screen.getByText(/Total: 8 events across 3 days/i)).toBeInTheDocument()
  })

  it('uses labelStep > 1 when many data points', () => {
    const data = Array.from({ length: 20 }, (_, i) => [`2024-01-${String(i + 1).padStart(2, '0')}`, i % 3])
    render(
      <EventFrequencyChart
        eventFrequency={{
          data,
          maxCount: 2,
          total: 20,
        }}
      />
    )
    expect(screen.getByText(/Total: 20 events across 20 days/i)).toBeInTheDocument()
  })
})
