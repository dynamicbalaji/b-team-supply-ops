import MapTab      from './MapTab'
import SplitTab    from './SplitTab'
import DecisionTab from './DecisionTab'
import AuditTab    from './AuditTab'

const TABS = [
  { id:'map',      label:'🗺 Live Map' },
  { id:'split',    label:'⚡ Traditional vs AI' },
  { id:'decision', label:'📊 Decision Matrix' },
  { id:'audit',    label:'📋 Audit Trail' },
]

export default function LeftPanel({
  activeTab, onTabChange,
  scenario, mapRoute, mapStatus, mapStatusColor,
  truckPhase, onTruckPhaseChange, phase,
  mcDistribution, mcStats, auditItems,
  messages, resolutionTime, costSaved, isRunning,
  approvalData,
}) {
  return (
    <div className="left">
      <div className="tabs">
        {TABS.map(tab => (
          <div key={tab.id}
            className={`tab${activeTab === tab.id ? ' on' : ''}`}
            onClick={() => onTabChange(tab.id)}
          >
            {tab.label}
          </div>
        ))}
      </div>

      <div className={`tpane${activeTab === 'map' ? ' on' : ''}`}>
        <MapTab
          scenario={scenario} mapRoute={mapRoute}
          mapStatus={mapStatus} mapStatusColor={mapStatusColor}
          truckPhase={truckPhase} onTruckPhaseChange={onTruckPhaseChange}
          phase={phase} isActive={activeTab === 'map'}
        />
      </div>

      <div className={`tpane${activeTab === 'split' ? ' on' : ''}`}>
        <SplitTab
          scenario={scenario}
          messages={messages}
          resolutionTime={resolutionTime}
          costSaved={costSaved}
          isRunning={isRunning}
        />
      </div>

      <div className={`tpane${activeTab === 'decision' ? ' on' : ''}`}>
        <DecisionTab
          mcDistribution={mcDistribution} mcStats={mcStats}
          isActive={activeTab === 'decision'}
          approvalData={approvalData}
          isRunning={isRunning}
        />
      </div>

      <div className={`tpane${activeTab === 'audit' ? ' on' : ''}`}>
        <AuditTab auditItems={auditItems} />
      </div>
    </div>
  )
}
