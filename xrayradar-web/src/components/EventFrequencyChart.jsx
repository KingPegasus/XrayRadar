export function EventFrequencyChart({ eventFrequency }) {
  if (!eventFrequency || !eventFrequency.data || eventFrequency.data.length === 0) {
    return null
  }

  return (
    <div style={{ marginTop: 20, marginBottom: 20 }}>
      <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 10, color: '#cbd5e1' }}>Event Frequency</div>
      <div style={{ background: 'rgba(0, 0, 0, 0.2)', padding: 16, borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)' }}>
        <div style={{ overflowX: 'auto', overflowY: 'visible' }}>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 1, height: 120, paddingBottom: '4px' }}>
            {eventFrequency.data.map(([date, count], idx) => {
              // Reserve space for date labels (32px) + gap (4px) + padding = 40px
              const availableHeight = 80 // Reserve space for date labels and spacing
              const barHeight = eventFrequency.maxCount > 0 
                ? Math.min((count / eventFrequency.maxCount) * availableHeight, availableHeight)
                : (count > 0 ? 4 : 0)
              return (
                <div key={idx} style={{ 
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center', 
                  justifyContent: 'flex-end', 
                  gap: 4, 
                  height: '100%',
                  flex: 1,
                  minWidth: 0,
                }}>
                  <div
                    style={{
                      width: '40%',
                      background: 'linear-gradient(to top, #2563eb, #3b82f6)',
                      height: `${barHeight}px`,
                      maxHeight: `${availableHeight}px`,
                      minHeight: count > 0 ? '4px' : '0',
                      borderRadius: '4px 4px 0 0',
                      transition: 'all 0.2s',
                      position: 'relative',
                      display: 'flex',
                      alignItems: 'flex-start',
                      justifyContent: 'center',
                      boxSizing: 'border-box',
                      flexShrink: 0,
                    }}
                    title={`${date}: ${count} event${count !== 1 ? 's' : ''}`}
                  >
                    {count > 0 && (
                      <span style={{ fontSize: 10, color: '#fff', fontWeight: 600, textShadow: '0 1px 2px rgba(0,0,0,0.5)' }}>
                        {count}
                      </span>
                    )}
                  </div>
                  <div style={{ 
                    fontSize: 10, 
                    color: '#94a3b8', 
                    writingMode: 'vertical-rl', 
                    textOrientation: 'mixed', 
                    transform: 'rotate(180deg)', 
                    flexShrink: 0,
                    height: '32px',
                    lineHeight: '32px',
                  }}>
                    {(() => {
                      // Parse date string (YYYY-MM-DD) and format it properly to avoid timezone issues
                      const [year, month, day] = date.split('-').map(Number)
                      const dateObj = new Date(Date.UTC(year, month - 1, day))
                      return dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' })
                    })()}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
        <div style={{ marginTop: 8, fontSize: 11, color: '#94a3b8', textAlign: 'center' }}>
          Total: {eventFrequency.total} event{eventFrequency.total !== 1 ? 's' : ''} across {eventFrequency.data.length} day{eventFrequency.data.length !== 1 ? 's' : ''}
        </div>
      </div>
    </div>
  )
}
