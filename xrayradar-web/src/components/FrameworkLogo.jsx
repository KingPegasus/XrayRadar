/**
 * Renders a framework/SDK logo from local assets (SVGs copied from your svg folder).
 */
import fastapiLogo from '../assets/sdk-logos/fastapi.svg'
import djangoLogo from '../assets/sdk-logos/django.svg'
import flaskLogo from '../assets/sdk-logos/flask.svg'
import nodeLogo from '../assets/sdk-logos/node.svg'
import expressLogo from '../assets/sdk-logos/Express.svg'
import koaLogo from '../assets/sdk-logos/koa.svg'
import reactLogo from '../assets/sdk-logos/react.svg'
import nextjsLogo from '../assets/sdk-logos/nextjs.svg'

const LOGOS = {
  fastapi: fastapiLogo,
  django: djangoLogo,
  flask: flaskLogo,
  node: nodeLogo,
  express: expressLogo,
  koa: koaLogo,
  react: reactLogo,
  nextjs: nextjsLogo,
}

export function FrameworkLogo({ logoId, size = 28, alt = '', className = '' }) {
  const src = LOGOS[logoId]
  if (!src) return null
  return (
    <img
      src={src}
      alt={alt}
      width={size}
      height={size}
      className={className}
      loading="lazy"
      decoding="async"
      style={{ display: 'block', flexShrink: 0 }}
    />
  )
}
