import { useState, useEffect } from 'react'

export function usePathname() {
  const [path, setPath] = useState(() => window.location.pathname || '/')
  useEffect(() => {
    const onPop = () => setPath(window.location.pathname || '/')
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])
  return path
}
