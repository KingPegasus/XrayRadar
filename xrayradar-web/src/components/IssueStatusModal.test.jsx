import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { IssueStatusModal } from './IssueStatusModal'
import * as api from '../utils/api'

vi.mock('../utils/api')

describe('IssueStatusModal', () => {
  const defaultProps = {
    projectId: 1,
    fingerprint: 'fp123',
    currentStatus: 'open',
    onStatusChange: vi.fn(),
    onClose: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders modal with current status', () => {
    render(<IssueStatusModal {...defaultProps} />)
    expect(screen.getByText('Update Issue Status')).toBeInTheDocument()
    expect(screen.getByText('Current:')).toBeInTheDocument()
    // There are multiple "Open" elements (badge and button), so use getAllByText
    const openElements = screen.getAllByText('Open')
    expect(openElements.length).toBeGreaterThan(0)
  })

  it('shows current status badge', () => {
    render(<IssueStatusModal {...defaultProps} currentStatus="resolved" resolvedRelease="v1.0.0" />)
    expect(screen.getByText('Current:')).toBeInTheDocument()
    // "Resolved" appears in badge and as a button - use getAllByText
    const resolvedElements = screen.getAllByText('Resolved')
    expect(resolvedElements.length).toBeGreaterThan(0)
  })

  it('shows resolution info when resolved', () => {
    const resolvedAt = new Date('2024-01-01T00:00:00Z')
    render(
      <IssueStatusModal
        {...defaultProps}
        currentStatus="resolved"
        resolvedRelease="v1.0.0"
        resolvedAt={resolvedAt.toISOString()}
      />
    )
    expect(screen.getByText(/Resolved in release:/i)).toBeInTheDocument()
    expect(screen.getByText('v1.0.0')).toBeInTheDocument()
    expect(screen.getByText(/Resolved on:/i)).toBeInTheDocument()
  })

  it('renders status buttons', () => {
    render(<IssueStatusModal {...defaultProps} />)
    // Use getAllByText since "Open" appears multiple times (badge and button)
    const openButtons = screen.getAllByText('Open')
    expect(openButtons.length).toBeGreaterThan(0)
    expect(screen.getByText('In Progress')).toBeInTheDocument()
    expect(screen.getByText('Resolved')).toBeInTheDocument()
    expect(screen.getByText('Ignored')).toBeInTheDocument()
  })

  it('allows selecting different status', async () => {
    const user = userEvent.setup()
    render(<IssueStatusModal {...defaultProps} />)
    
    // Find the Resolved button (not the badge)
    const resolvedButtons = screen.getAllByText('Resolved')
    const resolvedButton = resolvedButtons.find(btn => btn.tagName === 'BUTTON')
    expect(resolvedButton).toBeDefined()
    await user.click(resolvedButton)
    
    // Should show release input when resolved is selected
    await waitFor(() => {
      expect(screen.getByLabelText(/Resolve until release/i)).toBeInTheDocument()
    })
  })

  it('shows release input when resolved is selected', async () => {
    const user = userEvent.setup()
    render(<IssueStatusModal {...defaultProps} />)
    
    // Find the Resolved button (not the badge)
    const resolvedButtons = screen.getAllByText('Resolved')
    const resolvedButton = resolvedButtons.find(btn => btn.tagName === 'BUTTON')
    expect(resolvedButton).toBeDefined()
    await user.click(resolvedButton)
    
    await waitFor(() => {
      const input = screen.getByLabelText(/Resolve until release/i)
      expect(input).toBeInTheDocument()
      expect(input).toHaveAttribute('placeholder', 'e.g., v1.2.3')
    })
  })

  it('shows notes field when expanded', async () => {
    const user = userEvent.setup()
    render(<IssueStatusModal {...defaultProps} />)
    
    const addNotesButton = screen.getByText('+ Add notes (optional)')
    await user.click(addNotesButton)
    
    await waitFor(() => {
      expect(screen.getByLabelText(/Notes/i)).toBeInTheDocument()
    })
  })

  it('saves status change', async () => {
    const user = userEvent.setup()
    api.updateIssueStatus.mockResolvedValue({
      status: 'resolved',
      resolved_release: 'v1.0.0',
      reopened: false,
    })
    
    render(<IssueStatusModal {...defaultProps} />)
    
    // Find the Resolved button (not the badge)
    const resolvedButtons = screen.getAllByText('Resolved')
    const resolvedButton = resolvedButtons.find(btn => btn.tagName === 'BUTTON')
    expect(resolvedButton).toBeDefined()
    await user.click(resolvedButton)
    
    await waitFor(() => {
      const releaseInput = screen.getByLabelText(/Resolve until release/i)
      expect(releaseInput).toBeInTheDocument()
    })
    
    const releaseInput = screen.getByLabelText(/Resolve until release/i)
    await user.type(releaseInput, 'v1.0.0')
    
    const saveButton = screen.getByText('Save')
    await user.click(saveButton)
    
    await waitFor(() => {
      expect(api.updateIssueStatus).toHaveBeenCalledWith(1, 'fp123', {
        status: 'resolved',
        resolved_release: 'v1.0.0',
        notes: null,
      })
      expect(defaultProps.onStatusChange).toHaveBeenCalled()
      expect(defaultProps.onClose).toHaveBeenCalled()
    })
  })

  it('handles save error', async () => {
    const user = userEvent.setup()
    api.updateIssueStatus.mockRejectedValue(new Error('Failed to update'))
    
    render(<IssueStatusModal {...defaultProps} />)
    
    // Find the Resolved button (not the badge)
    const resolvedButtons = screen.getAllByText('Resolved')
    const resolvedButton = resolvedButtons.find(btn => btn.tagName === 'BUTTON')
    expect(resolvedButton).toBeDefined()
    await user.click(resolvedButton)
    
    await waitFor(() => {
      const saveButton = screen.getByText('Save')
      expect(saveButton).toBeInTheDocument()
    })
    
    const saveButton = screen.getByText('Save')
    await user.click(saveButton)
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to update/i)).toBeInTheDocument()
    })
    expect(defaultProps.onClose).not.toHaveBeenCalled()
  })

  it('closes modal on cancel', async () => {
    const user = userEvent.setup()
    render(<IssueStatusModal {...defaultProps} />)
    
    const cancelButton = screen.getByText('Cancel')
    await user.click(cancelButton)
    
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1)
  })

  it('closes modal on overlay click', async () => {
    render(<IssueStatusModal {...defaultProps} />)
    
    const overlay = screen.getByRole('dialog')
    await userEvent.click(overlay)
    
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1)
  })

  it('does not close modal on content click', async () => {
    const user = userEvent.setup()
    render(<IssueStatusModal {...defaultProps} />)
    
    const modalContent = screen.getByText('Update Issue Status').closest('div')
    await user.click(modalContent)
    
    expect(defaultProps.onClose).not.toHaveBeenCalled()
  })

  it('disables save button when status unchanged', () => {
    render(<IssueStatusModal {...defaultProps} currentStatus="open" />)
    
    const saveButton = screen.getByText('Save')
    expect(saveButton).toBeDisabled()
  })

  it('shows loading state when saving', async () => {
    const user = userEvent.setup()
    api.updateIssueStatus.mockImplementation(() => new Promise(() => {})) // Never resolves
    
    render(<IssueStatusModal {...defaultProps} />)
    
    const resolvedButtons = screen.getAllByText('Resolved')
    const resolvedButton = resolvedButtons.find(btn => btn.tagName === 'BUTTON')
    expect(resolvedButton).toBeDefined()
    await user.click(resolvedButton)
    
    await waitFor(() => {
      const saveButton = screen.getByText('Save')
      expect(saveButton).toBeInTheDocument()
    })
    
    const saveButton = screen.getByText('Save')
    await user.click(saveButton)
    
    await waitFor(() => {
      expect(screen.getByText('Saving...')).toBeInTheDocument()
    })
  })

  it('clears notes after successful save', async () => {
    const user = userEvent.setup()
    api.updateIssueStatus.mockResolvedValue({
      status: 'resolved',
      resolved_release: 'v1.0.0',
      reopened: false,
    })
    
    render(<IssueStatusModal {...defaultProps} />)
    
    // Expand notes
    const addNotesButton = screen.getByText('+ Add notes (optional)')
    await user.click(addNotesButton)
    
    await waitFor(() => {
      const notesInput = screen.getByLabelText(/Notes/i)
      expect(notesInput).toBeInTheDocument()
    })
    
    const notesInput = screen.getByLabelText(/Notes/i)
    await user.type(notesInput, 'Test note')
    
    // Find the Resolved button (not the badge)
    const resolvedButtons = screen.getAllByText('Resolved')
    const resolvedButton = resolvedButtons.find(btn => btn.tagName === 'BUTTON')
    expect(resolvedButton).toBeDefined()
    await user.click(resolvedButton)
    
    await waitFor(() => {
      const saveButton = screen.getByText('Save')
      expect(saveButton).toBeInTheDocument()
    })
    
    const saveButton = screen.getByText('Save')
    await user.click(saveButton)
    
    await waitFor(() => {
      expect(api.updateIssueStatus).toHaveBeenCalled()
    })
  })
})
