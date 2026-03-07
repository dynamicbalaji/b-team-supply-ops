import MapTab from './MapTab'
import SplitTab from './SplitTab'
import DecisionTab from './DecisionTab'
import AuditTab from './AuditTab'

const TABS = [
  { id: 'map',      label: '🗺 Live Map' },
  { id: 'split',    label: '⚡ Traditional vs AI' },
  { id: 'decision', label: '📊 Decision Matrix' },
  { id: 'audit',    label: '📋 Audit Trail' },
]

export default function LeftPanel({ activeTab, onTabChange }) {
  return (
    <div className="left">
      {/* Tab bar */}
      <div className="tabs">
        {TABS.map(tab => (
          <div
            key={tab.id}
            className={`tab${activeTab === tab.id ? ' on' : ''}`}
            onClick={() => onTabChange(tab.id)}
          >
            {tab.label}
          </div>
        ))}
      </div>

      {/* Tab panes */}
      <div className={`tpane${activeTab === 'map' ? ' on' : ''}`}>
        <MapTab isActive={activeTab === 'map'} />
      </div>

      <div className={`tpane${activeTab === 'split' ? ' on' : ''}`}>
        <SplitTab />
      </div>

      <div className={`tpane${activeTab === 'decision' ? ' on' : ''}`}>
        <DecisionTab />
      </div>

      <div className={`tpane${activeTab === 'audit' ? ' on' : ''}`}>
        <AuditTab />
      </div>
    </div>
  )
}
