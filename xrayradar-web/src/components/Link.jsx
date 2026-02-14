function isInternalPath(href) {
  if (!href || typeof href !== 'string') return false
  if (href.startsWith('http://') || href.startsWith('https://')) return false
  if (href.startsWith('mailto:') || href.startsWith('tel:')) return false
  if (href.startsWith('#') && href.length > 1) return false
  return true
}

export function Link({ to, children, className, ...rest }) {
  const handleClick = (e) => {
    if (!isInternalPath(to)) return
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return
    e.preventDefault()
    e.stopPropagation()
    window.location.href = to
  }

  return (
    <a href={to} className={className} onClick={handleClick} {...rest}>
      {children}
    </a>
  )
}
