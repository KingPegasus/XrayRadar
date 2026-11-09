import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { DASHBOARD_SEO, NOT_FOUND_SEO, PAGES, getSeoForPath } from './seo.config.js'
import { applySeoToHtml, buildRobotsTxt, buildSitemap, fillPlaceholders } from './seo.build.js'

/**
 * Fill site placeholders in index.html (dev + build), and at build time emit sitemap.xml,
 * robots.txt, per-route HTML (dist/<route>/index.html), dashboard.html and 404.html.
 */
function seoPlugin() {
  let outDir = 'dist'
  let isBuild = false
  return {
    name: 'xrayradar-seo',
    configResolved(config) {
      outDir = resolve(config.root, config.build.outDir)
      isBuild = config.command === 'build'
    },
    transformIndexHtml: { order: 'pre', handler: fillPlaceholders },
    closeBundle() {
      if (!isBuild) return
      const indexHtml = readFileSync(join(outDir, 'index.html'), 'utf-8')
      for (const page of PAGES) {
        if (page.path === '/') continue
        const dir = join(outDir, page.path.slice(1))
        mkdirSync(dir, { recursive: true })
        writeFileSync(join(dir, 'index.html'), applySeoToHtml(indexHtml, getSeoForPath(page.path)))
      }
      writeFileSync(join(outDir, 'dashboard.html'), applySeoToHtml(indexHtml, { ...DASHBOARD_SEO, canonical: null }))
      writeFileSync(join(outDir, '404.html'), applySeoToHtml(indexHtml, { ...NOT_FOUND_SEO, canonical: null }))
      // Apply the homepage entry too, so seo.config.js is the source for '/' as well.
      writeFileSync(join(outDir, 'index.html'), applySeoToHtml(indexHtml, getSeoForPath('/')))
      writeFileSync(join(outDir, 'sitemap.xml'), buildSitemap())
      writeFileSync(join(outDir, 'robots.txt'), buildRobotsTxt())
    },
  }
}

/** Defer main stylesheet so it doesn't block LCP; load with preload + onload. */
function deferCssPlugin() {
  return {
    name: 'defer-css',
    transformIndexHtml(html) {
      return html.replace(
        /<link rel="stylesheet" crossorigin href="([^"]+)">/g,
        (_, href) =>
          `<link rel="preload" href="${href}" as="style" onload="this.onload=null;this.rel='stylesheet'" crossorigin><noscript><link rel="stylesheet" href="${href}" crossorigin></noscript>`
      )
    },
  }
}

export default defineConfig({
  plugins: [react(), deferCssPlugin(), seoPlugin()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          if (id.includes('node_modules/react/') || id.includes('node_modules/react-dom/')) {
            return 'vendor-react'
          }
        },
      },
    },
  },
  server: {
    port: 5173,
    strictPort: true,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    fileParallelism: false,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      include: ['src/**/*.{js,jsx}'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.test.{js,jsx}',
        '**/*.config.{js,ts}',
        'dist/',
      ],
    },
  },
})
