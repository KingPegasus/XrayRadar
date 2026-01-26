import { useState } from 'react'
import logoIcon from '../assets/logo.svg'

export function Logo({ width = 120, height = 36, className = '', onError }) {
  const [hasError, setHasError] = useState(false)

  const handleError = () => {
    setHasError(true)
    if (onError) onError()
  }

  if (hasError) {
    return null
  }

  return (
    <img 
      src={logoIcon} 
      alt=""
      width={width}
      height={height}
      className={className}
      style={{ display: 'block' }}
      onError={handleError}
    />
  )
}
