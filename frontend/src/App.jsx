import { useState } from 'react'
import Nav from './components/Nav'
import CrisisBanner from './components/CrisisBanner'
import LeftPanel from './components/left/LeftPanel'
import RightPanel from './components/right/RightPanel'
import BottomBar from './components/BottomBar'

export default function App() {
  const [activeTab, setActiveTab] = useState('map')
  const [scenario, setScenario] = useState('port_strike')

  function handleStartScenario() {
    // No-op in Phase 1 — wired in Phase 4
  }

  function handleReset() {
    window.location.reload()
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

  return (
    <>
      <Nav
        scenario={scenario}
        onScenarioChange={setScenario}
        onStartScenario={handleStartScenario}
        onReset={handleReset}
        onManualScript={handleManualScript}
      />
      <CrisisBanner scenario={scenario} tickerValue={0} />
      <div className="main">
        <LeftPanel activeTab={activeTab} onTabChange={setActiveTab} />
        <RightPanel />
      </div>
      <BottomBar scenario={scenario} onScenarioChange={setScenario} />
    </>
  )
}
