import { navigate } from '../utils/navigation'

export function Link({ to, children, className }) {
  return (
    <a
      href={to}
      className={className}
      onClick={(e) => {
        // allow opening in new tab etc
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return
        e.preventDefault()
        navigate(to)
      }}
    >
      {children}
    </a>
  )
}
