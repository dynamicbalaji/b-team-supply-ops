import { useState } from 'react'
import AgentCard from './AgentCard'
import RiskAgent from './RiskAgent'

const AGENT_ORDER = ['log', 'fin', 'pro', 'sal']

export default function AgentNetwork({ agents, riskAgent }) {
  const [collapsed, setCollapsed] = useState(false)

  const activeCount = agents
    ? Object.values(agents).filter(a => a.statusClass !== 'idle').length
    : 0

  return (
    <div className="agnet">
      {/* Collapsible header */}
      <div className="agnet-hdr" onClick={() => setCollapsed(v => !v)}>
        <div className="agnet-htitle">
          ⬡ Agent Network
          <div className="agnet-live">
            <div className="dot" />
            <span>{activeCount} active</span>
          </div>
        </div>
        <div className={`agnet-chevron${collapsed ? '' : ' up'}`}>
          {collapsed ? '▸ show agents' : '▾'}
        </div>
      </div>

      {/* Body */}
      <div className={`agnet-body${collapsed ? ' hidden' : ''}`}>
        {/* 2×2 grid */}
        <div className="ag-grid">
          {AGENT_ORDER.map(id => (
            <AgentCard
              key={id}
              id={id}
              data={agents?.[id]}
            />
          ))}
        </div>

        {/* Risk agent — slides in when visible */}
        <RiskAgent data={riskAgent} />
      </div>
    </div>
  )
}
