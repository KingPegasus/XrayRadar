import { useState, useEffect } from 'react'
import { NAVIGATE_EVENT } from '../utils/navigation'
import { normalizePath } from '../../seo.config.js'

export function usePathname() {
  const [path, setPath] = useState(() => normalizePath(window.location.pathname))
  useEffect(() => {
    const updatePath = () => setPath(normalizePath(window.location.pathname))
    const onNavigate = (e) => setPath(normalizePath(e.detail?.path || window.location.pathname))

    window.addEventListener('popstate', updatePath)
    window.addEventListener(NAVIGATE_EVENT, onNavigate)
    return () => {
      window.removeEventListener('popstate', updatePath)
      window.removeEventListener(NAVIGATE_EVENT, onNavigate)
    }
  }, [])
  return path
}
