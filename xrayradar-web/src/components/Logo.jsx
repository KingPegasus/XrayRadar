export function Logo({ size = 36, className = '' }) {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 20 20" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <circle cx="10" cy="10" r="8" stroke="white" strokeWidth="1.1" fill="none" opacity="0.9"/>
      <circle cx="10" cy="10" r="5" stroke="white" strokeWidth="1.1" fill="none" opacity="0.7"/>
      <circle cx="10" cy="10" r="2" stroke="white" strokeWidth="1.1" fill="white" opacity="0.9"/>
      <line x1="10" y1="2" x2="10" y2="6" stroke="white" strokeWidth="1.1" opacity="0.9"/>
      <line x1="10" y1="14" x2="10" y2="18" stroke="white" strokeWidth="1.1" opacity="0.9"/>
      <line x1="2" y1="10" x2="6" y2="10" stroke="white" strokeWidth="1.1" opacity="0.9"/>
      <line x1="14" y1="10" x2="18" y2="10" stroke="white" strokeWidth="1.1" opacity="0.9"/>
    </svg>
  )
}
