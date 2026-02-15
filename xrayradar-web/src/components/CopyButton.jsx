import { useState, useCallback } from 'react'

/**
 * Reusable icon-only copy button. Copies given text to clipboard and shows
 * check icon for 2s on success. Optional onError called when clipboard fails.
 */
export function CopyButton({
  textToCopy,
  ariaLabel = 'Copy',
  title,
  className = '',
  style,
  onError,
}) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(() => {
    if (textToCopy == null || textToCopy === '') return
    navigator.clipboard.writeText(String(textToCopy)).then(
      () => {
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      },
      () => {
        setCopied(false)
        onError?.()
      }
    )
  }, [textToCopy, onError])

  const label = copied ? 'Copied' : ariaLabel
  const titleAttr = title != null ? (copied ? 'Copied' : title) : label

  return (
    <button
      type="button"
      className={className || 'codeCopy'}
      onClick={handleCopy}
      aria-label={label}
      title={titleAttr}
      style={style}
    >
      {copied ? (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      ) : (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
        </svg>
      )}
    </button>
  )
}
