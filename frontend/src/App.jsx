import { useState, useRef, useCallback, useEffect } from 'react'
import Nav          from './components/Nav'
import CrisisBanner from './components/CrisisBanner'
import LeftPanel    from './components/left/LeftPanel'
import RightPanel   from './components/right/RightPanel'
import BottomBar    from './components/BottomBar'
import { useTicker }                          from './hooks/useTicker'
import { useSSE }                             from './hooks/useSSE'
import { runManualMode, runExecutionCascade } from './utils/manualMode'

const AGENT_CLASS = { log:'al', fin:'af', pro:'ap', sal:'as_', risk:'ar', orc:'orc' }
const AGENT_COLOR = { log:'#00d4ff', fin:'#39d98a', pro:'#ffb340', sal:'#9b5de5', risk:'#ff3b5c', orc:'#00d4ff' }
const AGENT_LABEL = { log:'✈ LOGISTICS', fin:'💰 FINANCE', pro:'📦 PROCUREMENT', sal:'📧 SALES', risk:'⚠ RISK', orc:'🎯 ORCHESTRATOR' }

// Backend sends full names — map to short keys used internally
const AGENT_KEY_MAP = {
  logistics:   'log',
  finance:     'fin',
  procurement: 'pro',
  sales:       'sal',
  risk:        'risk',
  orchestrator:'orc',
  // pass-through for already-short keys
  log:'log', fin:'fin', pro:'pro', sal:'sal',
}

const INITIAL_AGENTS = {
  log: { status:'STANDBY', statusClass:'idle', confidence:0, tool:'idle', pulseOn:false },
  fin: { status:'STANDBY', statusClass:'idle', confidence:0, tool:'idle', pulseOn:false },
  pro: { status:'STANDBY', statusClass:'idle', confidence:0, tool:'idle', pulseOn:false },
  sal: { status:'STANDBY', statusClass:'idle', confidence:0, tool:'idle', pulseOn:false },
}
const INITIAL_RISK  = { visible:false, text:'' }
const INITIAL_STATE = {
  runId:null, scenario:'port_strike', isRunning:false, isApproved:false,
  phase:0, tickerStart:null, messages:[],
  mapRoute:'— Awaiting agents', mapStatus:'STANDBY', mapStatusColor:'#ffb340',
  truckPhase:'blocked', mcDistribution:null,
  mcStats:{ mean:280000, p10:241000, p90:318000, ci:0.94 },
  approvalVisible:false, approvalData:null, auditItems:[],
  resolutionTime:null, costSaved:null, roiShipments:200,
}

export default function App() {
  const [agents,    setAgents]    = useState(INITIAL_AGENTS)
  const [riskAgent, setRiskAgent] = useState(INITIAL_RISK)
  const [state,     setState]     = useState(INITIAL_STATE)
  const [activeTab, setActiveTab] = useState('map')
  const timerRefs = useRef([])
  const tickerValue = useTicker(state.tickerStart)

  const handleSSEEvent = useCallback((rawEvt) => {
    // Normalize full agent names → short keys for ALL event types
    const evt = rawEvt.agent ? { ...rawEvt, agent: AGENT_KEY_MAP[rawEvt.agent] || rawEvt.agent } : rawEvt
    // ── AGENT STATE → isolated setter, never touches main state ──────────
    if (evt.type === 'agent_state') {
      const k = AGENT_KEY_MAP[evt.agent] || evt.agent
      if (!INITIAL_AGENTS.hasOwnProperty(k)) {
        console.warn('[agent_state] unknown agent key:', evt.agent, '→', k)
        return
      }
      // Backend uses 'pulsing' not 'pulseOn'; statusClass derived from status
      const statusClass = evt.statusClass
        ?? (evt.status === 'COMPLETE' || evt.status === 'CONSENSUS' || evt.status === 'CONFIRMED' || evt.status === 'ACKNOWLEDGED' ? 'done'
          : evt.status === 'STANDBY' ? 'idle' : 'working')
      setAgents(prev => ({
        ...prev,
        [k]: {
          status:      evt.status ?? 'STANDBY',
          statusClass,
          confidence:  typeof evt.confidence === 'number' ? evt.confidence : prev[k].confidence,
          tool:        evt.tool ?? 'idle',
          pulseOn:     evt.pulseOn ?? evt.pulsing ?? false,
        },
      }))
      return
    }

    // ── RISK ACTIVATED → own setter ───────────────────────────────────────
    if (evt.type === 'risk_activated') {
      setRiskAgent({ visible:true, text:evt.message })
      return
    }

    // ── EVERYTHING ELSE → main state ─────────────────────────────────────
    setState(prev => {
      switch (evt.type) {
        case 'phase':
          return { ...prev, phase: evt.phase }

        case 'message':
        case 'execution': {
          const s    = Math.floor((Date.now() - (prev.tickerStart || Date.now())) / 1000)
          const time = String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0')
          const last = prev.messages[prev.messages.length - 1]
          if (last && last.agent === evt.agent && last.text === (evt.text||'')) return prev
          return {
            ...prev,
            messages: [...prev.messages, {
              id:         `${evt.agent}-${Date.now()}`,
              agent:      evt.agent,
              agentClass: AGENT_CLASS[evt.agent] || 'orc',
              agentColor: AGENT_COLOR[evt.agent] || '#00d4ff',
              from:       evt.from || AGENT_LABEL[evt.agent] || evt.agent?.toUpperCase() || '?',
              to:         evt.to   || '→ ORCHESTRATOR',
              time, text: evt.text||'', tools: evt.tools||[], isStreaming:false,
            }],
          }
        }

        case 'token': {
          const s    = Math.floor((Date.now() - (prev.tickerStart || Date.now())) / 1000)
          const time = String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0')
          const msgs = [...prev.messages]
          const last = msgs[msgs.length-1]
          if (last?.agent === evt.agent && last?.isStreaming) {
            msgs[msgs.length-1] = { ...last, text: last.text + evt.content }
          } else {
            msgs.push({
              id:`${evt.agent}-stream-${Date.now()}`, agent:evt.agent,
              agentClass:AGENT_CLASS[evt.agent]||'orc', agentColor:AGENT_COLOR[evt.agent]||'#00d4ff',
              from:AGENT_LABEL[evt.agent]||evt.agent?.toUpperCase()||'?', to:'→ ORCHESTRATOR',
              time, text:evt.content||'', tools:[], isStreaming:true,
            })
          }
          return { ...prev, messages:msgs }
        }

        case 'tool': {
          const msgs = [...prev.messages]
          const idx  = msgs.findLastIndex(m => m.agent === evt.agent)
          if (idx >= 0) {
            const existing = msgs[idx].tools || []
            const toolStr  = `${evt.tool}()`
            if (!existing.includes(toolStr))
              msgs[idx] = { ...msgs[idx], tools:[...existing, toolStr], isStreaming:false }
          }
          if (evt.tool === 'run_monte_carlo' && evt.result?.distribution) {
            return { ...prev, messages:msgs,
              mcDistribution: evt.result.distribution,
              mcStats:{ mean:evt.result.mean, p10:evt.result.p10, p90:evt.result.p90, ci:evt.result.ci },
            }
          }
          return { ...prev, messages:msgs }
        }

        case 'approval_required':
          return { ...prev, approvalVisible:true, approvalData:evt }

        case 'map_update':
          return { ...prev,
            mapStatus:      evt.status      ?? prev.mapStatus,
            mapStatusColor: evt.statusColor ?? prev.mapStatusColor,
            mapRoute:       evt.route       ?? prev.mapRoute,
          }

        case 'truck_phase':
          return { ...prev, truckPhase: evt.truckPhase }

        case 'audit':
          return { ...prev, auditItems:[...prev.auditItems, evt] }

        case 'metrics':
          return { ...prev,
            resolutionTime: evt.resolutionTime ?? prev.resolutionTime,
            costSaved:      evt.costSaved      ?? prev.costSaved,
          }

        case 'complete':
          return { ...prev, isRunning:false,
            resolutionTime: evt.resolutionTime || evt.resolution_time || prev.resolutionTime,
            costSaved: evt.costSaved || (evt.saved ? '$'+Number(evt.saved).toLocaleString() : prev.costSaved),
          }

        default:
          return prev
      }
    })
  }, [])

  const { connect, disconnect } = useSSE(handleSSEEvent)

  useEffect(() => () => { disconnect(); timerRefs.current.forEach(clearTimeout) }, [disconnect])
  useEffect(() => {
    const p = setInterval(() => fetch(`${import.meta.env.VITE_API_URL}/health`).catch(()=>{}), 600000)
    return () => clearInterval(p)
  }, [])

  async function startScenario() {
    timerRefs.current.forEach(clearTimeout)
    timerRefs.current = []
    disconnect()
    const scenario = state.scenario
    setAgents(INITIAL_AGENTS)
    setRiskAgent(INITIAL_RISK)
    setState({ ...INITIAL_STATE, scenario, tickerStart:Date.now(), isRunning:true })

    console.log('[startScenario] API_URL:', import.meta.env.VITE_API_URL)

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/runs`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({ scenario }), signal:AbortSignal.timeout(5000),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const { run_id } = await res.json()
      console.log('[startScenario] ✅ LIVE mode — run_id:', run_id)
      setState(prev => ({ ...prev, runId:run_id }))
      connect(run_id)
    } catch (err) {
      console.warn('[startScenario] ⚠ MANUAL mode — reason:', err.message)
      setTimeout(() => {
        console.log('[startScenario] firing runManualMode with handleSSEEvent')
        timerRefs.current = runManualMode(handleSSEEvent)
        console.log('[startScenario] timers set:', timerRefs.current.length)
      }, 50)
    }
  }

  async function approveDecision() {
    const runId = state.runId
    setState(prev => ({ ...prev, approvalVisible:false, isApproved:true }))
    if (runId) {
      try { await fetch(`${import.meta.env.VITE_API_URL}/api/runs/${runId}/approve`, { method:'POST' }) }
      catch (err) { timerRefs.current.push(...runExecutionCascade(handleSSEEvent)) }
    } else {
      timerRefs.current.push(...runExecutionCascade(handleSSEEvent))
    }
  }

  function rejectDecision()  { setState(prev => ({ ...prev, approvalVisible:false })) }
  function resetScenario()   {
    timerRefs.current.forEach(clearTimeout); timerRefs.current = []
    disconnect(); setAgents(INITIAL_AGENTS); setRiskAgent(INITIAL_RISK)
    setState(INITIAL_STATE); setActiveTab('map')
  }
  function handleScenarioChange(s) { setState(prev => ({ ...prev, scenario:s })) }
  const handleTruckPhaseChange = useCallback((p) => setState(prev => ({ ...prev, truckPhase:p })), [])

  return (
    <>
      <Nav scenario={state.scenario} onScenarioChange={handleScenarioChange}
        onStartScenario={startScenario} onReset={resetScenario} />
      <CrisisBanner scenario={state.scenario} tickerValue={tickerValue} />
      <div className="main">
        <LeftPanel
          activeTab={activeTab} onTabChange={setActiveTab}
          scenario={state.scenario} mapRoute={state.mapRoute}
          mapStatus={state.mapStatus} mapStatusColor={state.mapStatusColor}
          truckPhase={state.truckPhase} onTruckPhaseChange={handleTruckPhaseChange}
          phase={state.phase} mcDistribution={state.mcDistribution}
          mcStats={state.mcStats} auditItems={state.auditItems}
          isActive={activeTab === 'decision'}
        />
        <RightPanel
          agents={agents} riskAgent={riskAgent}
          messages={state.messages}
          approvalVisible={state.approvalVisible} approvalData={state.approvalData}
          onApprove={approveDecision} onReject={rejectDecision}
        />
      </div>
      <BottomBar
        scenario={state.scenario} onScenarioChange={handleScenarioChange}
        resolutionTime={state.resolutionTime} costSaved={state.costSaved}
        msgCount={state.messages.length} roiShipments={state.roiShipments}
        onRoiChange={(v) => setState(prev => ({ ...prev, roiShipments:v }))}
      />
    </>
  )
}
