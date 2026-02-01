export function EventFrequencyChart({ eventFrequency, showTitle = true }) {
  if (!eventFrequency || !eventFrequency.data || eventFrequency.data.length === 0) {
    return null
  }

  const { data, maxCount, total } = eventFrequency
  const barAreaHeight = 100
  const yMax = Math.max(maxCount, 1)
  const yMid = Math.ceil(yMax / 2)
  const labelStep = data.length > 14 ? Math.max(1, Math.floor(data.length / 6)) : 1

  const formatDate = (dateStr) => {
    const [y, m, d] = dateStr.split('-').map(Number)
    const date = new Date(Date.UTC(y, m - 1, d))
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' })
  }

  return (
    <div className="freqChart">
      {showTitle && (
        <h3 className="freqChartTitle">Event Frequency</h3>
      )}
      <div className="freqChartWrap">
        <div className="freqChartGrid" aria-hidden />
        <div className="freqChartBody">
          <div className="freqChartBarsWrap">
            {data.map(([date, count], idx) => {
              const barHeight = yMax > 0
                ? Math.round((count / yMax) * barAreaHeight)
                : 0
              const showLabel = idx % labelStep === 0 || idx === data.length - 1
              return (
                <div key={`${date}-${idx}`} className="freqChartBarCol">
                  <div
                    className="freqChartBar"
                    style={{
                      height: `${Math.max(barHeight, count > 0 ? 4 : 0)}px`,
                      animationDelay: `${idx * 0.02}s`,
                    }}
                    title={`${formatDate(date)}: ${count} event${count !== 1 ? 's' : ''}`}
                    role="img"
                    aria-label={`${formatDate(date)}: ${count} events`}
                  >
                    {count > 0 && (
                      <span className="freqChartBarCount">{count}</span>
                    )}
                  </div>
                  <div className="freqChartBarLabel">
                    {showLabel ? formatDate(date) : '\u00A0'}
                  </div>
                </div>
              )
            })}
          </div>
          <div className="freqChartSummary">
            Total: {total} event{total !== 1 ? 's' : ''} across {data.length} day{data.length !== 1 ? 's' : ''}
          </div>
        </div>
      </div>
    </div>
  )
}
