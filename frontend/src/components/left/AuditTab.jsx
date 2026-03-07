const STATIC_AUDIT_ITEMS = [
  {
    color: '#ff3b5c',
    time: '00:00 — Crisis Detected',
    agent: '🔴 System Monitor',
    desc: 'Strike detected. SC-2024-8891 BLOCKED at Long Beach. P0 broadcast to all agents.',
    data: 'penalty_risk: $2M · deadline: 48h · contract: Apple',
    memory: null,
  },
  {
    color: '#00d4ff',
    time: '00:12 — Route Options',
    agent: '🔵 Logistics Agent',
    desc: '3 options generated. Memory recalled March 2024 LA port strike — hybrid saved $180K.',
    data: 'check_freight_rates() · memory_recall("LA_strike_2024")',
    memory: '📚 Historical: LA Strike Mar 2024 — hybrid saved $180K',
  },
  {
    color: '#00e676',
    time: '01:04 — Monte Carlo',
    agent: '🟢 Finance Agent',
    desc: '100-iteration simulation run. Challenged customs assumption — Air revised $450K → $500K.',
    data: 'run_monte_carlo(100) · query_customs_rates()',
    memory: null,
  },
  {
    color: '#9b5de5',
    time: '02:18 — SLA Confirmed',
    agent: '🟣 Sales Agent',
    desc: 'Apple 36h extension negotiated. Reputational risk only — zero financial penalty.',
    data: 'query_contract_terms() · draft_sla_amendment()',
    memory: null,
  },
  {
    color: '#ff3b5c',
    time: "03:45 — Risk Flagged",
    agent: "🔴 Risk Agent (Devil's Advocate)",
    desc: 'LAX ground crew unconfirmed during strike. Single point of failure. Hour-20 backup trigger added. Finance +$20K reserve.',
    data: 'risk: operational · severity: medium · mitigation: tucson_backup_H20',
    memory: null,
  },
  {
    color: '#00e676',
    time: '04:32 — Approved & Executed',
    agent: '✅ VP Operations',
    desc: 'Hybrid route approved. Cascade: freight booked, Apple notified, budget released, spot order cancelled.',
    data: 'option: hybrid · cost: $280K · savings: $220K · CI: 94%',
    memory: null,
  },
]

// Map SSE audit event shape → display shape
function normalizeItem(item) {
  // If it's already a display-ready object (from STATIC_AUDIT_ITEMS), pass through
  if (item.agent) return item

  // SSE audit event shape from App.jsx: { time, agentColor, agentLabel, description, data, hasMemory }
  return {
    color:  item.agentColor  || '#00d4ff',
    time:   item.time        || '',
    agent:  item.agentLabel  || '',
    desc:   item.description || '',
    data:   item.data        || '',
    memory: item.hasMemory
      ? `📚 ${item.description?.split('Memory recalled')[1]?.trim() || 'Memory context available'}`
      : null,
  }
}

export default function AuditTab({ auditItems }) {
  const items = (auditItems && auditItems.length > 0)
    ? auditItems.map(normalizeItem)
    : STATIC_AUDIT_ITEMS

  return (
    <div className="aud">
      <div className="sec-hd">
        <div className="sec-ttl">Decision Audit Trail</div>
        <button
          className="expbtn"
          onClick={() => alert('PDF export in production build')}
        >
          ⬇ Export PDF
        </button>
      </div>

      <div className="atl">
        {items.map((item, idx) => (
          <div className="aitem" key={idx}>
            <div
              className="adot"
              style={{ background: item.color, borderColor: item.color }}
            />
            <div className="atime">{item.time}</div>
            <div className="acard">
              <div className="aagent" style={{ color: item.color }}>{item.agent}</div>
              <div className="adesc">{item.desc}</div>
              <div className="adata">{item.data}</div>
              {item.memory && (
                <div className="membadge">{item.memory}</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
