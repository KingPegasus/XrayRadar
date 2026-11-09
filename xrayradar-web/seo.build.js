/** Build-time SEO helpers (used by vite.config.js). Pure string functions, unit-tested. */
import { META_TAGS, OG_IMAGE, PAGES, SITE_URL } from './seo.config.js'

const escapeAttr = (s) => String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;')

/** Fill %SITE_URL% / %OG_IMAGE% placeholders in index.html. */
export function fillPlaceholders(html) {
  return html.replaceAll('%OG_IMAGE%', OG_IMAGE).replaceAll('%SITE_URL%', SITE_URL)
}

/** Rewrite the per-route SEO tags of the built index.html. Replacers are functions so `$` in values is literal. */
export function applySeoToHtml(html, seo) {
  const setMeta = (h, attr, key, value) =>
    h.replace(new RegExp(`(<meta ${attr}="${key}" content=")[^"]*(")`), (_, a, b) => a + escapeAttr(value) + b)
  let out = html.replace(/<title>[^<]*<\/title>/, () => `<title>${escapeAttr(seo.title)}</title>`)
  for (const [attr, key, value] of META_TAGS) out = setMeta(out, attr, key, value(seo))
  if (seo.canonical) {
    out = out.replace(/(<link rel="canonical" href=")[^"]*(")/, (_, a, b) => a + escapeAttr(seo.canonical) + b)
    out = setMeta(out, 'property', 'og:url', seo.canonical)
  } else {
    out = out.replace(/\s*<link rel="canonical" href="[^"]*" \/>/, '')
    out = out.replace(/\s*<meta property="og:url" content="[^"]*" \/>/, '')
  }
  return out
}

export function buildSitemap() {
  const urls = PAGES.filter((p) => p.index)
    .map(
      (p) =>
        `  <url>\n    <loc>${SITE_URL}${p.path}</loc>\n    <lastmod>${p.lastmod}</lastmod>\n` +
        `    <changefreq>${p.changefreq}</changefreq>\n    <priority>${p.priority}</priority>\n  </url>`
    )
    .join('\n')
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`
}

export function buildRobotsTxt() {
  return `User-agent: *\nAllow: /\nDisallow: /dashboard\nDisallow: /api/\nDisallow: /auth/\n\nSitemap: ${SITE_URL}/sitemap.xml\n`
}
