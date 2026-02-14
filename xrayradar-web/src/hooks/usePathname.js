import { useState, useEffect } from 'react'
import { NAVIGATE_EVENT } from '../utils/navigation'

export function usePathname() {
  const [path, setPath] = useState(() => window.location.pathname || '/')
  useEffect(() => {
    const updatePath = () => setPath(window.location.pathname || '/')
    const onNavigate = (e) => setPath(e.detail?.path || window.location.pathname || '/')

    window.addEventListener('popstate', updatePath)
    window.addEventListener(NAVIGATE_EVENT, onNavigate)
    return () => {
      window.removeEventListener('popstate', updatePath)
      window.removeEventListener(NAVIGATE_EVENT, onNavigate)
    }
  }, [])
  return path
}
