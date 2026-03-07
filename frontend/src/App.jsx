import { useState, useRef, useCallback } from 'react'
import Nav          from './components/Nav'
import CrisisBanner from './components/CrisisBanner'
import LeftPanel    from './components/left/LeftPanel'
import RightPanel   from './components/right/RightPanel'
import BottomBar    from './components/BottomBar'
import { useTicker }                              from './hooks/useTicker'
import { runManualMode, runExecutionCascade }     from './utils/manualMode'

// ─── Agent lookup maps ────────────────────────────────────────────────────────
const AGENT_CLASS = { log:'al', fin:'af', pro:'ap', sal:'as_', risk:'ar', orc:'orc' }
const AGENT_COLOR = { log:'#00d4ff', fin:'#00e676', pro:'#ffb340', sal:'#9b5de5', risk:'#ff3b5c', orc:'#00d4ff' }
const AGENT_LABEL = { log:'✈ LOGISTICS', fin:'💰 FINANCE', pro:'📦 PROCUREMENT', sal:'📧 SALES', risk:'⚠ RISK', orc:'🎯 ORCHESTRATOR' }

// ─── Initial state ────────────────────────────────────────────────────────────
const INITIAL_STATE = {
  runId:      null,
  scenario:   'port_strike',
  isRunning:  false,
  isApproved: false,
  phase:      0,
  tickerStart: null,

  agents: {
    log: { status:'STANDBY', statusClass:'idle', confidence:0, tool:'idle', pulseOn:false },
    fin: { status:'STANDBY', statusClass:'idle', confidence:0, tool:'idle', pulseOn:false },
    pro: { status:'STANDBY', statusClass:'idle', confidence:0, tool:'idle', pulseOn:false },
    sal: { status:'STANDBY', statusClass:'idle', confidence:0, tool:'idle', pulseOn:false },
  },
  riskAgent: { visible:false, text:'' },

  messages: [],

  mapRoute:       '— Awaiting agents',
  mapStatus:      'STANDBY',
  mapStatusColor: '#ffb340',
  truckPhase:     'blocked',

  mcDistribution: null,
  mcStats: { mean:280000, p10:241000, p90:318000, ci:0.94 },

  approvalVisible: false,
  approvalData:    null,

  auditItems: [],

  resolutionTime: null,
  costSaved:      null,
  roiShipments:   200,
}

// ─── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  const [state, setState]         = useState(INITIAL_STATE)
  const [activeTab, setActiveTab] = useState('map')
  const timerRefs                 = useRef([])

  // Live cost ticker
  const tickerValue = useTicker(state.tickerStart)

  // ── Universal SSE event handler ───────────────────────────────────────────
  function handleSSEEvent(evt) {
    setState(prev => {
      switch (evt.type) {

        case 'phase':
          return { ...prev, phase: evt.phase }

        case 'agent_state':
          return {
            ...prev,
            agents: {
              ...prev.agents,
              [evt.agent]: {
                status:      evt.status,
                statusClass: evt.statusClass ?? 'working',
                confidence:  evt.confidence  ?? prev.agents[evt.agent]?.confidence ?? 0,
                tool:        evt.tool        ?? 'idle',
                pulseOn:     evt.pulseOn     ?? false,
              },
            },
          }

        case 'message':
        case 'execution': {
          const s = Math.floor((Date.now() - (prev.tickerStart || Date.now())) / 1000)
          const time = String(Math.floor(s / 60)).padStart(2,'0') + ':' + String(s % 60).padStart(2,'0')
          return {
            ...prev,
            messages: [
              ...prev.messages,
              {
                id:          Date.now() + Math.random(),
                agent:       evt.agent,
                agentClass:  AGENT_CLASS[evt.agent] || 'orc',
                agentColor:  AGENT_COLOR[evt.agent] || '#00d4ff',
                from:        evt.from  || AGENT_LABEL[evt.agent] || '?',
                to:          evt.to    || '→ ORCHESTRATOR',
                time,
                text:        evt.text  || '',
                tools:       evt.tools || [],
                isStreaming: false,
              },
            ],
          }
        }

        case 'token': {
          const s = Math.floor((Date.now() - (prev.tickerStart || Date.now())) / 1000)
          const time = String(Math.floor(s / 60)).padStart(2,'0') + ':' + String(s % 60).padStart(2,'0')
          const msgs = [...prev.messages]
          const last = msgs[msgs.length - 1]
          if (last?.agent === evt.agent && last?.isStreaming) {
            msgs[msgs.length - 1] = { ...last, text: last.text + evt.content }
          } else {
            msgs.push({
              id: Date.now() + Math.random(),
              agent: evt.agent,
              agentClass: AGENT_CLASS[evt.agent] || 'orc',
              agentColor: AGENT_COLOR[evt.agent] || '#00d4ff',
              from: AGENT_LABEL[evt.agent] || '?',
              to: '→ ORCHESTRATOR',
              time,
              text: evt.content || '',
              tools: [],
              isStreaming: true,
            })
          }
          return { ...prev, messages: msgs }
        }

        case 'tool': {
          const msgs = [...prev.messages]
          const idx  = msgs.findLastIndex(m => m.agent === evt.agent)
          if (idx >= 0) {
            msgs[idx] = { ...msgs[idx], tools: [...msgs[idx].tools, `${evt.tool}()`], isStreaming: false }
          }
          if (evt.tool === 'run_monte_carlo' && evt.result?.distribution) {
            return {
              ...prev, messages: msgs,
              mcDistribution: evt.result.distribution,
              mcStats: { mean:evt.result.mean, p10:evt.result.p10, p90:evt.result.p90, ci:evt.result.ci },
            }
          }
          return { ...prev, messages: msgs }
        }

        case 'risk_activated':
          return { ...prev, riskAgent: { visible:true, text:evt.message } }

        case 'approval_required':
          return { ...prev, approvalVisible:true, approvalData:evt }

        case 'map_update':
          return {
            ...prev,
            mapStatus:      evt.status      ?? prev.mapStatus,
            mapStatusColor: evt.statusColor ?? prev.mapStatusColor,
            mapRoute:       evt.route       ?? prev.mapRoute,
          }

        case 'truck_phase':
          return { ...prev, truckPhase: evt.truckPhase }

        case 'audit':
          return { ...prev, auditItems: [...prev.auditItems, evt] }

        case 'metrics':
          return {
            ...prev,
            resolutionTime: evt.resolutionTime ?? prev.resolutionTime,
            costSaved:      evt.costSaved      ?? prev.costSaved,
          }

        case 'complete':
          return {
            ...prev,
            isRunning:      false,
            resolutionTime: evt.resolutionTime || evt.resolution_time || prev.resolutionTime,
            costSaved:      evt.costSaved || (evt.saved ? '$' + Number(evt.saved).toLocaleString() : prev.costSaved),
          }

        default:
          return prev
      }
    })
  }

  // ── startScenario ─────────────────────────────────────────────────────────
  function startScenario() {
    timerRefs.current.forEach(clearTimeout)
    timerRefs.current = []
    setState(prev => ({
      ...INITIAL_STATE,
      scenario:    prev.scenario,
      tickerStart: Date.now(),
      isRunning:   true,
    }))
    // Small delay so React flushes state before first event fires
    setTimeout(() => {
      timerRefs.current = runManualMode(handleSSEEvent)
    }, 50)
  }

  // ── approveDecision — triggers execution cascade ──────────────────────────
  function approveDecision() {
    setState(prev => ({ ...prev, approvalVisible:false, isApproved:true }))
    timerRefs.current.push(...runExecutionCascade(handleSSEEvent))
  }

  // ── rejectDecision ────────────────────────────────────────────────────────
  function rejectDecision() {
    setState(prev => ({ ...prev, approvalVisible:false }))
  }

  // ── resetScenario ─────────────────────────────────────────────────────────
  function resetScenario() {
    timerRefs.current.forEach(clearTimeout)
    timerRefs.current = []
    setState(INITIAL_STATE)
    setActiveTab('map')
  }

  // ── handleScenarioChange ──────────────────────────────────────────────────
  function handleScenarioChange(scenario) {
    setState(prev => ({ ...prev, scenario }))
  }

  // ── Stable truck phase callback — prevents Leaflet hook re-init ───────────
  const handleTruckPhaseChange = useCallback((newPhase) => {
    setState(prev => ({ ...prev, truckPhase: newPhase }))
  }, [])

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <>
      <Nav
        scenario={state.scenario}
        onScenarioChange={handleScenarioChange}
        onStartScenario={startScenario}
        onReset={resetScenario}
      />

      <CrisisBanner
        scenario={state.scenario}
        tickerValue={tickerValue}
      />

      <div className="main">
        <LeftPanel
          activeTab={activeTab}
          onTabChange={setActiveTab}
          scenario={state.scenario}
          mapRoute={state.mapRoute}
          mapStatus={state.mapStatus}
          mapStatusColor={state.mapStatusColor}
          truckPhase={state.truckPhase}
          onTruckPhaseChange={handleTruckPhaseChange}
          phase={state.phase}
          mcDistribution={state.mcDistribution}
          mcStats={state.mcStats}
        />

        <RightPanel
          agents={state.agents}
          riskAgent={state.riskAgent}
          messages={state.messages}
          approvalVisible={state.approvalVisible}
          approvalData={state.approvalData}
          onApprove={approveDecision}
          onReject={rejectDecision}
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
