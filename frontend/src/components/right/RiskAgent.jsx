export default function RiskAgent({ data }) {
  const { visible = false, text = '' } = data ?? {}

  return (
    <div
      className="risk-card agcard"
      style={{
        opacity:       visible ? 1 : 0,
        transform:     visible ? 'none' : 'translateY(8px)',
        transition:    'opacity 0.4s ease, transform 0.4s ease',
        pointerEvents: visible ? 'auto' : 'none',
        // Keep it in the layout at all times so the transition is smooth;
        // collapse it to zero height when not visible to avoid phantom space
        maxHeight:     visible ? '120px' : '0',
        overflow:      'hidden',
        marginTop:     visible ? '7px' : '0',
      }}
    >
      <div className="risk-hd">
        <span className="risk-title">⚠ RISK AGENT</span>
        <span className="risk-badge">DEVIL'S ADVOCATE</span>
        <span
          style={{
            display:      'inline-block',
            width:        '6px',
            height:       '6px',
            borderRadius: '50%',
            background:   '#ff3b5c',
            marginLeft:   'auto',
            flexShrink:   0,
            animation:    'blink .9s infinite',
          }}
        />
      </div>
      <div className="risk-body">
        {text || 'Monitoring for failure modes…'}
      </div>
    </div>
  )
}
