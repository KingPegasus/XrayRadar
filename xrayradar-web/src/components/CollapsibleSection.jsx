export function CollapsibleSection({ title, open: isOpen, onToggle, children }) {
  return (
    <div className="collapsibleSection">
      <button
        type="button"
        onClick={onToggle}
        className="collapsibleSectionHeader"
      >
        {title}
        <span className={`collapsibleChevron ${isOpen ? 'isOpen' : ''}`}>
          ▼
        </span>
      </button>
      {isOpen && (
        <div className="collapsibleSectionBody">
          {children}
        </div>
      )}
    </div>
  )
}
