import { SCENARIOS } from '../constants/scenarios'

export default function CrisisBanner({ scenario, tickerValue, isApproved }) {
  const s = SCENARIOS[scenario] || SCENARIOS.port_strike
  const formatted = '$' + (tickerValue || 0).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')

  return (
    <div className="crisis">
      <div style={{ display:'flex', alignItems:'center', minWidth:0, overflow:'hidden' }}>
        <span className="cbadge" style={isApproved ? { background:'#39d98a22', color:'#39d98a', borderColor:'#39d98a44' } : {}}>
          {isApproved ? 'RESOLVED' : 'CRITICAL'}
        </span>
        <span className="ctxt">
          <b>{s.title}</b> {s.crisis}
        </span>
      </div>
      <div className="ticker-wrap">
        <div className="ticker-lbl" style={isApproved ? { color:'#39d98a' } : {}}>
          {isApproved ? '✓ Cost locked' : 'Cost accumulating'}
        </div>
        <div
          className="ticker-val"
          style={isApproved ? { color:'#39d98a', textShadow:'0 0 12px #39d98a66' } : {}}
        >
          {formatted}
        </div>
        <div className="ticker-sub">Traditional: {s.traditional}</div>
      </div>
    </div>
  )
}
