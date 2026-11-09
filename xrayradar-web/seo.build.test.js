import { describe, it, expect } from 'vitest'
import { applySeoToHtml, buildRobotsTxt, buildSitemap, fillPlaceholders } from './seo.build.js'
import { getSeoForPath, PAGES } from './seo.config.js'

const HTML = `<title>Home</title>
    <meta name="description" content="home" />
    <meta name="robots" content="index, follow" />
    <link rel="canonical" href="%SITE_URL%/" />
    <meta property="og:title" content="Home" />
    <meta property="og:description" content="home" />
    <meta property="og:url" content="%SITE_URL%/" />
    <meta property="og:image" content="%OG_IMAGE%" />
    <meta name="twitter:title" content="Home" />
    <meta name="twitter:description" content="home" />`

describe('seo build helpers', () => {
  it('fills placeholders', () => {
    const out = fillPlaceholders(HTML)
    expect(out).toContain('href="https://xrayradar.com/"')
    expect(out).toContain('content="https://xrayradar.com/og-image.png"')
    expect(out).not.toContain('%')
  })

  it('rewrites tags for an indexable page', () => {
    const out = applySeoToHtml(fillPlaceholders(HTML), getSeoForPath('/privacy'))
    expect(out).toContain('<title>Privacy Policy — XrayRadar</title>')
    expect(out).toContain('<link rel="canonical" href="https://xrayradar.com/privacy" />')
    expect(out).toContain('<meta property="og:url" content="https://xrayradar.com/privacy" />')
  })

  it('drops canonical and og:url for noindex pages', () => {
    const out = applySeoToHtml(fillPlaceholders(HTML), getSeoForPath('/dashboard'))
    expect(out).toContain('content="noindex, follow"')
    expect(out).not.toContain('rel="canonical"')
    expect(out).not.toContain('og:url')
  })

  it('inserts $ sequences literally', () => {
    const out = applySeoToHtml(HTML, { title: 'From $1 & $&', description: "$' cost", index: true, canonical: null })
    expect(out).toContain('<title>From $1 &amp; $&amp;</title>')
    expect(out).toContain(`<meta name="description" content="$' cost" />`)
  })

  it('uses per-page lastmod in the sitemap, not the build date', () => {
    const xml = buildSitemap()
    for (const p of PAGES.filter((p) => p.index)) expect(xml).toContain(`<lastmod>${p.lastmod}</lastmod>`)
    expect(xml).not.toContain('/login')
  })

  it('points robots.txt at the sitemap', () => {
    expect(buildRobotsTxt()).toContain('Sitemap: https://xrayradar.com/sitemap.xml')
  })
})
