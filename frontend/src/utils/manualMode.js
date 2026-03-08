// ─── Manual Mode Demo Engine ──────────────────────────────────────────────────
// Fires SSE-shaped events at timed intervals so the demo runs fully offline.
// Shape of every event is identical to what the real backend SSE stream sends.

const AGENT_CLASS  = { log:'al',   fin:'af',  pro:'ap',   sal:'as_', risk:'ar', orc:'orc' }
const AGENT_COLOR  = { log:'#00d4ff', fin:'#00e676', pro:'#ffb340', sal:'#9b5de5', risk:'#ff3b5c', orc:'#00d4ff' }
const AGENT_LABEL  = { log:'✈ LOGISTICS', fin:'💰 FINANCE', pro:'📦 PROCUREMENT', sal:'📧 SALES', risk:'⚠ RISK', orc:'🎯 ORCHESTRATOR' }

// ─── Pre-approval event sequence ──────────────────────────────────────────────
const MANUAL_EVENTS = [

  // ── Phase 1 — Activation ─────────────────────────────────────────── t=0
  { t: 0,    evt: { type:'phase', phase:1 }},
  { t: 100,  evt: { type:'agent_state', agent:'log', status:'ACTIVATING',  statusClass:'working', confidence:0, tool:'📡 broadcast_received()', pulseOn:true }},
  { t: 200,  evt: { type:'agent_state', agent:'fin', status:'ACTIVATING',  statusClass:'working', confidence:0, tool:'📡 broadcast_received()', pulseOn:true }},
  { t: 300,  evt: { type:'agent_state', agent:'pro', status:'ACTIVATING',  statusClass:'working', confidence:0, tool:'📡 broadcast_received()', pulseOn:true }},
  { t: 400,  evt: { type:'agent_state', agent:'sal', status:'ACTIVATING',  statusClass:'working', confidence:0, tool:'📡 broadcast_received()', pulseOn:true }},
  { t: 500,  evt: { type:'message', agent:'orc',
      from:'🎯 ORCHESTRATOR', to:'→ ALL',
      text:'Crisis P0: SC-2024-8891 blocked at Long Beach. Budget cap $500K. Deadline 48h. Begin parallel evaluation.',
      tools:[] }},
  { t: 600,  evt: { type:'map_update', status:'AGENTS ACTIVE', statusColor:'#ffb340', route:'— Evaluating routes' }},

  // ── Phase 2 — Logistics proposes ─────────────────────────────────── t=1.5s
  { t: 1500, evt: { type:'phase', phase:2 }},
  { t: 1550, evt: { type:'agent_state', agent:'log', status:'PROPOSING', statusClass:'working', confidence:0, tool:'📦 check_freight_rates()', pulseOn:true }},
  { t: 1700, evt: { type:'message', agent:'log',
      from:'✈ LOGISTICS', to:'→ ORCH',
      text:'Option A: Air via LAX — $450K / 24h / Low risk.<br>Recalled March 2024 LA strike — hybrid saved $180K then.',
      tools:['📦 check_freight_rates()','📚 memory_recall("LA_2024")'] }},
  { t: 1800, evt: { type:'map_update', status:'EVALUATING', statusColor:'#ffb340', route:'✈ LAX route evaluated' }},

  // ── Procurement queries ───────────────────────────────────────────── t=3s
  { t: 3000, evt: { type:'agent_state', agent:'pro', status:'QUERYING', statusClass:'working', confidence:0, tool:'🏭 query_suppliers("dallas")', pulseOn:true }},
  { t: 3100, evt: { type:'message', agent:'pro',
      from:'📦 PROCUREMENT', to:'→ ORCH',
      text:'Option B: Spot buy Dallas — $380K / 12h / Med risk. Only 80% quantity available. Cert: 4h.',
      tools:['🏭 query_suppliers("dallas")'] }},

  // ── Finance challenges ────────────────────────────────────────────── t=5s
  { t: 5000, evt: { type:'agent_state', agent:'fin', status:'CALCULATING', statusClass:'working', confidence:0, tool:'📊 run_monte_carlo(100)', pulseOn:true }},
  { t: 5100, evt: { type:'message', agent:'fin',
      from:'💰 FINANCE', to:'→ LOGISTICS',
      text:'Your $450K — does that include expedited customs at LAX during strike conditions? Challenging that assumption.',
      tools:['📊 run_monte_carlo(100)','💰 query_customs_rates()'] }},
  { t: 5200, evt: { type:'tool', agent:'fin', tool:'run_monte_carlo',
      result:{ mean:280000, p10:241000, p90:318000, ci:0.94,
               distribution:[3,6,10,16,26,36,50,65,77,87,92,87,80,70,58,45,33,24,16,10,6,3] }}},

  // ── Logistics revises ─────────────────────────────────────────────── t=7s
  { t: 7000, evt: { type:'agent_state', agent:'log', status:'REVISING', statusClass:'working', confidence:58, tool:'📦 recalculate_route()', pulseOn:true }},
  { t: 7100, evt: { type:'message', agent:'log',
      from:'✈ LOGISTICS', to:'→ FINANCE',
      text:'Confirmed. Customs +$50K. Total air: $500K — at budget limit. Recommend Hybrid 60/40: $280K / 36h instead.',
      tools:[] }},

  // ── Consensus ─────────────────────────────────────────────────────── t=9s
  { t: 9000, evt: { type:'agent_state', agent:'fin', status:'CONSENSUS', statusClass:'done', confidence:94, tool:'✅ propose_consensus()', pulseOn:false }},
  { t: 9100, evt: { type:'agent_state', agent:'log', status:'CONSENSUS', statusClass:'done', confidence:88, tool:'✅ hybrid_confirmed()', pulseOn:false }},

  // ── Sales negotiates ──────────────────────────────────────────────── t=10s
  { t: 10000, evt: { type:'agent_state', agent:'sal', status:'NEGOTIATING', statusClass:'working', confidence:0, tool:'📋 query_contract_terms()', pulseOn:true }},
  { t: 10100, evt: { type:'message', agent:'sal',
      from:'📧 SALES', to:'→ ALL',
      text:'Apple accepts 36h delay + Q3 priority allocation. Zero financial penalty confirmed. Hybrid timeline fits perfectly.',
      tools:['📋 query_contract_terms()','📝 draft_sla_amendment()'] }},
  { t: 10500, evt: { type:'agent_state', agent:'sal', status:'CONFIRMED', statusClass:'done', confidence:97, tool:'✅ sla_confirmed()', pulseOn:false }},

  // ── ⭐ Risk Agent fires — THE KEY MOMENT ──────────────────────────── t=12.5s
  { t: 12500, evt: { type:'risk_activated',
      message:'LAX ground crew unconfirmed during active strike. Single point of failure in Hybrid plan. Recommend Hour-20 backup trigger to Tucson air route.' }},
  { t: 12600, evt: { type:'message', agent:'risk',
      from:'⚠ RISK AGENT', to:'→ ALL ⚠',
      text:'⚠ Consensus challenge: LAX ground crew unconfirmed. Single point of failure. Recommend Hour-20 backup trigger to Tucson route.',
      tools:[] }},
  { t: 12700, evt: { type:'map_update', status:'RISK FLAGGED', statusColor:'#ff3b5c', route:'⚠ Risk identified' }},

  // ── Finance absorbs + proposes final ─────────────────────────────── t=14.5s
  { t: 14500, evt: { type:'agent_state', agent:'fin', status:'FINALISING', statusClass:'working', confidence:94, tool:'✅ propose_consensus()', pulseOn:true }},
  { t: 14600, evt: { type:'message', agent:'fin',
      from:'💰 FINANCE', to:'→ ALL',
      text:'Risk acknowledged. Adding +$20K contingency for Tucson backup. Final: Hybrid $280K + $20K reserve. 94% CI.',
      tools:['✅ propose_consensus()'] }},
  { t: 14700, evt: { type:'agent_state', agent:'pro', status:'ACKNOWLEDGED', statusClass:'done', confidence:71, tool:'✅ acknowledged()', pulseOn:false }},

  // ── Approval ──────────────────────────────────────────────────────── t=16s
  { t: 16000, evt: { type:'phase', phase:3 }},
  { t: 16100, evt: { type:'approval_required', option:'hybrid', cost:280000, confidence:0.94 }},
  { t: 16200, evt: { type:'map_update', status:'AWAITING APPROVAL', statusColor:'#ffb340', route:'✈ Hybrid route ready' }},
  { t: 16300, evt: { type:'metrics', resolutionTime:'4m 32s', costSaved:'$220K' }},
]

// ─── Post-approval execution cascade ─────────────────────────────────────────
const EXECUTION_EVENTS = [
  { t: 0,    evt: { type:'phase', phase:4 }},
  { t: 100,  evt: { type:'map_update', status:'EXECUTING', statusColor:'#00e676', route:'✈ Freight booked → Austin' }},
  { t: 200,  evt: { type:'truck_phase', truckPhase:'flying' }},
  { t: 500,  evt: { type:'execution', agent:'log', from:'✈ LOGISTICS',    text:'Freight booked: LAX → Austin TX · FX-2024-8891 · ETA 36h',                     tools:[] }},
  { t: 1200, evt: { type:'execution', agent:'sal', from:'📧 SALES',        text:'Apple notified — 36h extension confirmed · Q3 priority allocation logged',      tools:[] }},
  { t: 1900, evt: { type:'execution', agent:'fin', from:'💰 FINANCE',      text:'Budget released: $280K · Contingency $20K · PO #F-7741 issued',                 tools:[] }},
  { t: 2600, evt: { type:'execution', agent:'pro', from:'📦 PROCUREMENT',  text:'Dallas spot order cancelled · Tucson backup scheduled for Hour 20',             tools:[] }},
  { t: 3200, evt: { type:'complete', resolutionTime:'4m 32s', saved:220000 }},
  { t: 3300, evt: { type:'agent_state', agent:'log', status:'COMPLETE', statusClass:'done', confidence:88, tool:'✅ done', pulseOn:false }},
  { t: 3400, evt: { type:'agent_state', agent:'fin', status:'COMPLETE', statusClass:'done', confidence:94, tool:'✅ done', pulseOn:false }},
  { t: 3500, evt: { type:'agent_state', agent:'pro', status:'COMPLETE', statusClass:'done', confidence:71, tool:'✅ done', pulseOn:false }},
  { t: 3600, evt: { type:'agent_state', agent:'sal', status:'COMPLETE', statusClass:'done', confidence:97, tool:'✅ done', pulseOn:false }},
  { t: 3700, evt: { type:'map_update', status:'RESOLVED ✓', statusColor:'#00e676', route:'✅ Austin — Delivered' }},
  { t: 4000, evt: { type:'phase', phase:5 }},
]

// ─── Exports ──────────────────────────────────────────────────────────────────

export function runManualMode(onEvent) {
  const timers = []
  MANUAL_EVENTS.forEach(({ t, evt }) => {
    timers.push(setTimeout(() => onEvent(evt), t))
  })
  return timers
}

export function runExecutionCascade(onEvent) {
  const timers = []
  EXECUTION_EVENTS.forEach(({ t, evt }) => {
    timers.push(setTimeout(() => onEvent(evt), t))
  })
  return timers
}

// Re-export for handleSSEEvent to use in App.jsx
export { AGENT_CLASS, AGENT_COLOR, AGENT_LABEL }
