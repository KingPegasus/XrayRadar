import { BreadcrumbTimeline } from './BreadcrumbTimeline'
import { CopyButton } from './CopyButton'

export function EventDetailView({ event }) {
  const payload = event.payload || {}
  const exception = payload.exception
  const breadcrumbs = payload.breadcrumbs || []
  const contexts = payload.contexts || {}
  const tags = payload.tags || {}
  const user = payload.user || {}
  const device = contexts.device || {}
  const os = contexts.os || {}
  const runtime = contexts.runtime || {}
  const fingerprint = payload.fingerprint || []

  // Extract exception info
  let exceptionType = ''
  let exceptionValue = ''
  let stackTrace = null
  if (exception && exception.values && exception.values.length > 0) {
    const exc = exception.values[0]
    exceptionType = exc.type || ''
    exceptionValue = exc.value || ''
    stackTrace = exc.stacktrace || null
  }

  // Extract grouping info
  const groupingInfo = []
  if (fingerprint && fingerprint.length > 0) {
    groupingInfo.push(`SDK fingerprint: ${fingerprint.join(', ')}`)
  } else if (exceptionType || exceptionValue) {
    groupingInfo.push(`Exception type: ${exceptionType}`)
    groupingInfo.push(`Exception value: ${exceptionValue}`)
    if (stackTrace && stackTrace.frames && stackTrace.frames.length > 0) {
      const frame = stackTrace.frames.find((f) => f.in_app) || stackTrace.frames[0]
      if (frame) {
        groupingInfo.push(`Location: ${frame.filename || ''}:${frame.lineno || ''} in ${frame.function || ''}`)
      }
    }
  }

  const Section = ({ title, children }) => (
    <div style={{ marginBottom: 24 }}>
      <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, color: '#cbd5e1', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {title}
      </h3>
      {children}
    </div>
  )

  const CodeBlock = ({ children, style = {} }) => (
    <pre className="code" style={{ whiteSpace: 'pre-wrap', fontSize: 12, padding: 12, borderRadius: 6, background: 'rgba(0, 0, 0, 0.3)', border: '1px solid rgba(255,255,255,0.1)', margin: 0, ...style }}>
      {children}
    </pre>
  )

  const KeyValue = ({ label, value }) => (
    <div style={{ marginBottom: 8 }}>
      <span style={{ color: '#94a3b8', fontSize: 12 }}>{label}:</span>{' '}
      <span style={{ color: '#e5e7eb', fontSize: 13 }}>{value || <span style={{ color: '#64748b' }}>—</span>}</span>
    </div>
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
      {/* Exception Details */}
      {(exceptionType || exceptionValue) && (
        <Section title="Exception">
          <div style={{ background: 'rgba(0, 0, 0, 0.2)', padding: 12, borderRadius: 6, border: '1px solid rgba(255,255,255,0.1)' }}>
            <div style={{ marginBottom: 8 }}>
              <div style={{ color: '#fca5a5', fontSize: 16, fontWeight: 600, marginBottom: 4 }}>{exceptionType}</div>
              <div style={{ color: '#e5e7eb', fontSize: 13 }}>{exceptionValue || event.message}</div>
            </div>
          </div>
        </Section>
      )}

      {/* Stack Trace */}
      {stackTrace && stackTrace.frames && stackTrace.frames.length > 0 && (
        <Section title="Stack Trace">
          <div style={{ background: 'rgba(0, 0, 0, 0.2)', padding: 12, borderRadius: 6, border: '1px solid rgba(255,255,255,0.1)', maxHeight: '400px', overflowY: 'auto' }}>
            {stackTrace.frames
              .slice()
              .reverse()
              .map((frame, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '8px 0',
                    borderBottom: idx < stackTrace.frames.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
                    fontFamily: 'ui-monospace, monospace',
                    fontSize: 12,
                  }}
                >
                  <div style={{ color: frame.in_app ? '#86efac' : '#94a3b8', marginBottom: 2 }}>
                    {frame.filename || '<unknown>'}
                    {frame.lineno ? `:${frame.lineno}` : ''}
                    {frame.function ? ` in ${frame.function}` : ''}
                  </div>
                  {frame.context_line && (
                    <div style={{ color: '#64748b', marginTop: 4, paddingLeft: 12 }}>
                      {frame.pre_context &&
                        frame.pre_context.map((line, i) => (
                          <div key={`pre-${i}`} style={{ color: '#64748b' }}>
                            {line}
                          </div>
                        ))}
                      <div style={{ color: '#fca5a5', fontWeight: 600 }}>{frame.context_line}</div>
                      {frame.post_context &&
                        frame.post_context.map((line, i) => (
                          <div key={`post-${i}`} style={{ color: '#64748b' }}>
                            {line}
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              ))}
          </div>
        </Section>
      )}

      {/* Breadcrumbs */}
      {breadcrumbs.length > 0 && (
        <Section title="Breadcrumbs">
          <BreadcrumbTimeline 
            breadcrumbs={breadcrumbs} 
            errorTimestamp={event.timestamp}
          />
        </Section>
      )}

      {/* Environment & Context */}
      <Section title="Environment & Context">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 12 }}>
          <div style={{ background: 'rgba(0, 0, 0, 0.2)', padding: 12, borderRadius: 6, border: '1px solid rgba(255,255,255,0.1)' }}>
            <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 8, color: '#cbd5e1' }}>Environment</div>
            <KeyValue label="Environment" value={event.environment || contexts.environment} />
            <KeyValue label="Release" value={event.release || contexts.release} />
            <KeyValue label="Server" value={event.server_name || contexts.server_name} />
            <KeyValue label="Platform" value={payload.platform} />
          </div>

          {/* User Data */}
          {(user.id || user.email || user.username || user.ip_address) && (
            <div style={{ background: 'rgba(0, 0, 0, 0.2)', padding: 12, borderRadius: 6, border: '1px solid rgba(255,255,255,0.1)' }}>
              <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 8, color: '#cbd5e1' }}>User</div>
              <KeyValue label="ID" value={user.id} />
              <KeyValue label="Email" value={user.email} />
              <KeyValue label="Username" value={user.username} />
              <KeyValue label="IP Address" value={user.ip_address} />
            </div>
          )}

          {/* Device Info */}
          {(device.name || device.model || os.name || runtime.name) && (
            <div style={{ background: 'rgba(0, 0, 0, 0.2)', padding: 12, borderRadius: 6, border: '1px solid rgba(255,255,255,0.1)' }}>
              <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 8, color: '#cbd5e1' }}>Device</div>
              <KeyValue label="Device" value={device.name || device.model} />
              <KeyValue label="OS" value={os.name ? `${os.name} ${os.version || ''}`.trim() : null} />
              <KeyValue label="Runtime" value={runtime.name ? `${runtime.name} ${runtime.version || ''}`.trim() : null} />
              <KeyValue label="Screen" value={device.screen_width && device.screen_height ? `${device.screen_width}x${device.screen_height}` : null} />
            </div>
          )}
        </div>
      </Section>

      {/* Tags */}
      {Object.keys(tags).length > 0 && (
        <Section title="Tags">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {Object.entries(tags).map(([key, value]) => (
              <span
                key={key}
                style={{
                  display: 'inline-block',
                  padding: '4px 10px',
                  borderRadius: 4,
                  background: 'rgba(37, 99, 235, 0.2)',
                  border: '1px solid rgba(37, 99, 235, 0.4)',
                  color: '#93c5fd',
                  fontSize: 12,
                }}
              >
                {key}: {String(value)}
              </span>
            ))}
          </div>
        </Section>
      )}

      {/* Grouping Info */}
      {groupingInfo.length > 0 && (
        <Section title="Grouping Information">
          <div style={{ background: 'rgba(0, 0, 0, 0.2)', padding: 12, borderRadius: 6, border: '1px solid rgba(255,255,255,0.1)' }}>
            <div className="small" style={{ color: '#94a3b8', marginBottom: 8 }}>
              This error was grouped with others based on:
            </div>
            <ul style={{ margin: 0, paddingLeft: 20, color: '#e5e7eb', fontSize: 12 }}>
              {groupingInfo.map((info, idx) => (
                <li key={idx} style={{ marginBottom: 4 }}>
                  {info}
                </li>
              ))}
            </ul>
          </div>
        </Section>
      )}

      {/* Raw Payload (collapsible): Copy button stays at top; JSON scrolls below */}
      <Section title="Raw Event Data">
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', marginBottom: 8 }}>
          <details style={{ flex: '1 1 auto', minWidth: 0 }}>
            <summary style={{ cursor: 'pointer', color: '#93c5fd', fontSize: 12 }}>Show raw JSON payload</summary>
            <div style={{ maxHeight: 360, overflowY: 'auto', marginTop: 8 }}>
              <CodeBlock>{JSON.stringify(payload, null, 2)}</CodeBlock>
            </div>
          </details>
          <CopyButton
            textToCopy={JSON.stringify(payload, null, 2)}
            ariaLabel="Copy JSON payload"
            className="button codeCopy"
            style={{ flexShrink: 0 }}
          />
        </div>
      </Section>
    </div>
  )
}
