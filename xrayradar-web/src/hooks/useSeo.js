import { useEffect } from 'react'
import { getSeoForPath, META_TAGS } from '../../seo.config.js'

function setMeta(attr, key, value) {
  let el = document.head.querySelector(`meta[${attr}="${key}"]`)
  if (!el) {
    el = document.createElement('meta')
    el.setAttribute(attr, key)
    document.head.appendChild(el)
  }
  el.setAttribute('content', value)
}

/** Keep <title>, description, robots and canonical in sync with the current route. */
export function useSeo(path) {
  useEffect(() => {
    const seo = getSeoForPath(path)
    document.title = seo.title
    for (const [attr, key, value] of META_TAGS) setMeta(attr, key, value(seo))

    let canonical = document.head.querySelector('link[rel="canonical"]')
    if (seo.canonical) {
      if (!canonical) {
        canonical = document.createElement('link')
        canonical.setAttribute('rel', 'canonical')
        document.head.appendChild(canonical)
      }
      canonical.setAttribute('href', seo.canonical)
      setMeta('property', 'og:url', seo.canonical)
    } else {
      canonical?.remove()
      document.head.querySelector('meta[property="og:url"]')?.remove()
    }
  }, [path])
}
