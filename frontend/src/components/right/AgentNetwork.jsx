import { useState } from 'react'
import AgentCard from './AgentCard'
import RiskAgent from './RiskAgent'

const AGENT_ORDER = ['log', 'fin', 'pro', 'sal']

export default function AgentNetwork({ agents, riskAgent }) {
  const [collapsed, setCollapsed] = useState(false)
  const activeCount = Object.values(agents).filter(a => a.statusClass !== 'idle').length

  return (
    <div className="agnet">
      <div className="agnet-hdr" onClick={() => setCollapsed(v => !v)}>
        <div className="agnet-htitle">
          ⬡ Agent Network
          <div className="agnet-live">
            <div className="dot" />
            <span>{activeCount} active</span>
          </div>
        </div>
        <div className="agnet-chevron">
          {collapsed ? '▸ show' : '▾ hide'}
        </div>
      </div>

      {!collapsed && (
        <div className="agnet-body">
          <div className="ag-grid">
            {AGENT_ORDER.map(id => (
              <AgentCard key={id} id={id} data={agents[id]} />
            ))}
          </div>
          <RiskAgent data={riskAgent} />
        </div>
      )}
    </div>
  )
}
