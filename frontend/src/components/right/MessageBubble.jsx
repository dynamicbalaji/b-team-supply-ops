export default function MessageBubble({ msg }) {
  const {
    agentColor = '#00d4ff',
    agentClass = 'al',
    from       = '',
    to         = '',
    time       = '',
    text       = '',
    tools      = [],
    isStreaming = false,
  } = msg

  const hasMemory = tools.some(t => t.includes('memory_recall'))

  return (
    <div className="msg">
      {/* Header row */}
      <div className="mh">
        <span className="mfrom" style={{ color: agentColor }}>{from}</span>
        <span className="mto">{to}</span>
        <span className="mtime">{time}</span>
      </div>

      {/* Bubble */}
      <div className={`mbub ${agentClass}`}>
        {/* Text — may contain HTML like <br> */}
        <span dangerouslySetInnerHTML={{ __html: text }} />

        {/* Streaming cursor */}
        {isStreaming && (
          <span
            style={{
              opacity:   0.6,
              animation: 'cursorBlink 1s infinite',
              marginLeft: '1px',
            }}
          >
            ▌
          </span>
        )}

        {/* Tool pills + memory badge */}
        {tools.length > 0 && (
          <div className="mtools">
            {tools.map((t, i) => (
              <span key={i} className="tool-pill">{t}</span>
            ))}
            {hasMemory && (
              <span className="membadge">
                📚 {tools.find(t => t.includes('memory_recall'))}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
