import { useState, useCallback } from 'react'
import Nav from './components/Nav'
import CrisisBanner from './components/CrisisBanner'
import LeftPanel from './components/left/LeftPanel'
import RightPanel from './components/right/RightPanel'
import BottomBar from './components/BottomBar'
import { useTicker } from './hooks/useTicker'

// ─── Global initial state ────────────────────────────────────────────────────
const INITIAL_STATE = {
  // Run
  runId: null,
  scenario: 'port_strike',
  isRunning: false,
  isApproved: false,
  phase: 0,          // 0–4 maps to phase strip
  tickerStart: null,

  // Agents (keyed by id)
  agents: {
    log: { status: 'STANDBY', statusClass: 'idle', confidence: 0, tool: 'idle', pulseOn: false },
    fin: { status: 'STANDBY', statusClass: 'idle', confidence: 0, tool: 'idle', pulseOn: false },
    pro: { status: 'STANDBY', statusClass: 'idle', confidence: 0, tool: 'idle', pulseOn: false },
    sal: { status: 'STANDBY', statusClass: 'idle', confidence: 0, tool: 'idle', pulseOn: false },
  },
  riskAgent: { visible: false, text: '' },

  // Chat
  messages: [],

  // Map
  mapRoute: '— Awaiting agents',
  mapStatus: 'STANDBY',
  mapStatusColor: '#ffb340',
  truckPhase: 'blocked',   // 'blocked' | 'flying' | 'driving' | 'arrived'

  // Decision tab
  mcDistribution: null,
  mcStats: { mean: 280000, p10: 241000, p90: 318000, ci: 0.94 },

  // Approval
  approvalVisible: false,
  approvalData: null,

  // Audit
  auditItems: [],

  // Metrics
  resolutionTime: null,
  costSaved: null,
  roiShipments: 200,
}

// ─── App ─────────────────────────────────────────────────────────────────────
export default function App() {
  const [state, setState] = useState(INITIAL_STATE)
  const [activeTab, setActiveTab] = useState('map')

  // Live cost ticker — only runs when scenario is active
  const tickerValue = useTicker(state.tickerStart)

  // ── Handlers ──────────────────────────────────────────────────────────────

  function handleScenarioChange(scenario) {
    setState(prev => ({ ...prev, scenario }))
  }

  function handleStartScenario() {
    // No-op in Phase 2 — wired fully in Phase 4
  }

  function handleReset() {
    setState(INITIAL_STATE)
    setActiveTab('map')
  }

  function handleManualScript() {
    alert(
      'Manual Mode Script\n\n' +
      '1. ORCHESTRATOR → ALL: "Crisis P0 — evaluate options"\n' +
      '2. LOGISTICS: Air $450K + Hybrid $280K option. Recalls March 2024 LA strike.\n' +
      '3. PROCUREMENT: Dallas spot buy, 80% qty, $380K\n' +
      '4. FINANCE: Challenges $450K — customs +$50K → Monte Carlo → Hybrid wins 94% CI\n' +
      '5. SALES: Apple accepts 36h extension, zero penalty\n' +
      '6. RISK AGENT: LAX single point of failure — backup trigger H20\n' +
      '7. FINANCE: Final proposal $280K + $20K reserve\n' +
      '8. Click APPROVE → execution cascade fires'
    )
  }

  // Stable callback so useMapCanvas doesn't restart animation loop on every render
  const handleTruckPhaseChange = useCallback((newPhase) => {
    setState(prev => ({ ...prev, truckPhase: newPhase }))
  }, [])

  function handleApprove() {
    setState(prev => ({ ...prev, approvalVisible: false, isApproved: true }))
  }

  function handleReject() {
    setState(prev => ({ ...prev, approvalVisible: false }))
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <>
      <Nav
        scenario={state.scenario}
        onScenarioChange={handleScenarioChange}
        onStartScenario={handleStartScenario}
        onReset={handleReset}
        onManualScript={handleManualScript}
      />

      <CrisisBanner
        scenario={state.scenario}
        tickerValue={tickerValue}
      />

      <div className="main">
        <LeftPanel
          activeTab={activeTab}
          onTabChange={setActiveTab}
          // Map props
          scenario={state.scenario}
          mapRoute={state.mapRoute}
          mapStatus={state.mapStatus}
          mapStatusColor={state.mapStatusColor}
          truckPhase={state.truckPhase}
          onTruckPhaseChange={handleTruckPhaseChange}
          phase={state.phase}
        />

        <RightPanel
          agents={state.agents}
          riskAgent={state.riskAgent}
          messages={state.messages}
          approvalVisible={state.approvalVisible}
          approvalData={state.approvalData}
          onApprove={handleApprove}
          onReject={handleReject}
        />
      </div>

      <BottomBar
        scenario={state.scenario}
        onScenarioChange={handleScenarioChange}
        resolutionTime={state.resolutionTime}
        costSaved={state.costSaved}
        msgCount={state.messages.length}
        roiShipments={state.roiShipments}
        onRoiChange={(v) => setState(prev => ({ ...prev, roiShipments: v }))}
      />
    </>
  )
}
