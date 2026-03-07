import { useState } from 'react'

// Static agent card data for Phase 1
const AGENTS = [
  { id: 'log', colorClass: 'al', label: 'LOGISTICS' },
  { id: 'fin', colorClass: 'af', label: 'FINANCE' },
  { id: 'pro', colorClass: 'ap', label: 'PROCUREMENT' },
  { id: 'sal', colorClass: 'as_', label: 'SALES' },
]

export default function RightPanel() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="right">
      {/* Agent Network — collapsible */}
      <div className="agnet">
        <div
          className="agnet-hdr"
          onClick={() => setCollapsed(v => !v)}
        >
          <div className="agnet-htitle">
            ⬡ Agent Network
            <div className="agnet-live">
              <div className="dot" />
              <span>0 active</span>
            </div>
          </div>
          <div className={`agnet-chevron${collapsed ? '' : ' up'}`}>
            {collapsed ? '▸ show agents' : '▾'}
          </div>
        </div>

        {!collapsed && (
          <div className="agnet-body">
            {/* 2×2 agent card grid */}
            <div className="ag-grid">
              {AGENTS.map(agent => (
                <div className={`agcard ${agent.colorClass}`} key={agent.id}>
                  <div className="ag-hd">
                    <span className="ag-name">{agent.label}</span>
                    <span className="ag-pulse" />
                  </div>
                  <div className="ag-status idle">STANDBY</div>
                  <div className="confrow">
                    <div className="confbg">
                      <div className="conffill" style={{ width: '0%' }} />
                    </div>
                    <span className="confval">—</span>
                  </div>
                  <div className="tool-pill">idle</div>
                </div>
              ))}
            </div>

            {/* Risk Agent — hidden until Phase 4 activates it */}
            <div className="risk-card agcard hidden" id="riskCard">
              <div className="risk-hd">
                <span className="risk-title">⚠ RISK AGENT</span>
                <span className="risk-badge">DEVIL'S ADVOCATE</span>
                <span
                  className="ag-pulse on"
                  style={{
                    background: '#ff3b5c',
                    marginLeft: 'auto',
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    animation: 'blink .9s infinite',
                  }}
                />
              </div>
              <div className="risk-body">Monitoring...</div>
            </div>
          </div>
        )}
      </div>

      {/* A2A Negotiation Log */}
      <div className="chat">
        <div className="chat-hdr">
          <span className="chat-title">⬡ A2A Negotiation Log</span>
          <span className="chat-cnt">0 messages</span>
        </div>

        <div className="msgs">
          {/* Empty state */}
          <div className="msg-empty">
            <div className="msg-empty-icon">⬡</div>
            <div className="msg-empty-txt">Awaiting scenario start</div>
            <div className="msg-empty-sub">Click ⚙ DEMO CTRL → Start Scenario</div>
          </div>
        </div>

        {/* Approval panel — hidden in Phase 1 */}
        <div className="approval" style={{ display: 'none' }}>
          <div className="apcard">
            <div className="ap-title">⏸ AWAITING HUMAN APPROVAL</div>
            <div className="ap-opt">Hybrid Route — 60% Air / 40% Sea</div>
            <div className="ap-det">
              $280K + $20K reserve · 36h delivery · Backup trigger H20 · Apple: ✓ · Confidence: 94%
            </div>
            <div className="ap-acts">
              <button className="appbtn">✓ APPROVE &amp; EXECUTE</button>
              <button className="rejbtn">✗ Reject</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
