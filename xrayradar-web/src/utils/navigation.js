const NAVIGATE_EVENT = 'xrayradar-navigate'

export function navigate(to) {
  if (to === window.location.pathname) return
  window.history.pushState({}, '', to)
  window.dispatchEvent(new PopStateEvent('popstate'))
  window.dispatchEvent(new CustomEvent(NAVIGATE_EVENT, { detail: { path: to } }))
}

export { NAVIGATE_EVENT }
