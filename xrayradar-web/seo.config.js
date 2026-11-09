/**
 * Single source of truth for SEO metadata.
 *
 * Used at build time (vite.config.js) to generate sitemap.xml and a pre-rendered
 * <head> for every route (dist/<route>/index.html), and at runtime (useSeo) to
 * update the <head> on client-side navigation.
 *
 * Only pages with `index: true` appear in the sitemap and are indexable.
 * `lastmod` is the date the page content last changed (not the build date).
 *
 * index.html uses %SITE_URL% and %OG_IMAGE% placeholders, filled from here.
 */
export const SITE_URL = 'https://xrayradar.com'
export const OG_IMAGE = `${SITE_URL}/og-image.png`

export const PAGES = [
  {
    path: '/',
    title: 'XrayRadar — Open-source error tracking that stays out of your way',
    description:
      'XrayRadar is a minimal error tracking stack: open-source server and dashboard, lightweight Python, JavaScript and Android SDKs, and an optional hosted service. Capture exceptions, debug faster, ship with confidence.',
    index: true,
    lastmod: '2026-11-09',
    changefreq: 'weekly',
    priority: '1.0',
  },
  {
    path: '/privacy',
    title: 'Privacy Policy — XrayRadar',
    description:
      'How XrayRadar collects, uses and protects your information, including cookies, subprocessors, data retention and your GDPR and CCPA rights.',
    index: true,
    lastmod: '2026-02-15',
    changefreq: 'yearly',
    priority: '0.3',
  },
  {
    path: '/terms',
    title: 'Terms of Service — XrayRadar',
    description:
      'The terms that govern your use of the XrayRadar error tracking service, including accounts, acceptable use, fees and liability.',
    index: true,
    lastmod: '2026-02-15',
    changefreq: 'yearly',
    priority: '0.3',
  },
  { path: '/login', title: 'Sign in — XrayRadar', description: 'Sign in to your XrayRadar dashboard.', index: false },
  { path: '/forgot-password', title: 'Forgot password — XrayRadar', description: 'Reset your XrayRadar password.', index: false },
  { path: '/reset-password', title: 'Reset password — XrayRadar', description: 'Choose a new XrayRadar password.', index: false },
  { path: '/verify-email', title: 'Verify email — XrayRadar', description: 'Verify your XrayRadar email address.', index: false },
  { path: '/accept-invite', title: 'Accept invite — XrayRadar', description: 'Join a team on XrayRadar.', index: false },
]

export const DASHBOARD_SEO = {
  title: 'Dashboard — XrayRadar',
  description: 'Your XrayRadar error tracking dashboard.',
  index: false,
}

export const NOT_FOUND_SEO = {
  title: 'Page not found — XrayRadar',
  description: 'The page you are looking for does not exist.',
  index: false,
}

/** Strip trailing slashes so '/privacy/' and '/privacy' are the same route. */
export function normalizePath(pathname) {
  const path = (pathname || '/').replace(/\/+$/, '')
  return path || '/'
}

const isDashboardPath = (path) => path === '/dashboard' || path.startsWith('/dashboard/')

/** Resolve SEO metadata for any pathname. */
export function getSeoForPath(pathname) {
  const path = normalizePath(pathname)
  const page = PAGES.find((p) => p.path === path)
  if (page) return { ...page, canonical: page.index ? SITE_URL + page.path : null }
  if (isDashboardPath(path)) return { ...DASHBOARD_SEO, canonical: null }
  return { ...NOT_FOUND_SEO, canonical: null }
}

export function isKnownPath(pathname) {
  const path = normalizePath(pathname)
  return PAGES.some((p) => p.path === path) || isDashboardPath(path)
}

export function robotsFor(seo) {
  return seo.index ? 'index, follow, max-image-preview:large' : 'noindex, follow'
}

/** Head <meta> tags that vary per route: [attribute, key, value(seo)]. */
export const META_TAGS = [
  ['name', 'description', (seo) => seo.description],
  ['name', 'robots', robotsFor],
  ['property', 'og:title', (seo) => seo.title],
  ['property', 'og:description', (seo) => seo.description],
  ['name', 'twitter:title', (seo) => seo.title],
  ['name', 'twitter:description', (seo) => seo.description],
]
