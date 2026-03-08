/**
 * LeftPanel.jsx  (UPDATED — passes runId + isRunning + scenario to dynamic tabs)
 *
 * CHANGES FROM ORIGINAL
 * ─────────────────────
 * 1. New props: runId, isRunning, approvalData
 *    These are forwarded to DecisionTab and AuditTab so those components
 *    can fetch data from the API.
 * 2. DecisionTab: receives runId, isRunning, approvalData (new)
 *    plus the existing mcDistribution, mcStats, isActive.
 * 3. AuditTab: receives runId, isRunning, scenario (new)
 *    plus the existing auditItems.
 * 4. No other changes — all other tabs are untouched.
 *
 * Updated usage in App.jsx
 * ────────────────────────
 * Locate the <LeftPanel ... /> render in App.jsx and add these props:
 *
 *   <LeftPanel
 *     ...existing props...
 *     runId={state.runId}
 *     isRunning={state.isRunning}
 *     approvalData={state.approvalData}
 *   />
 */

import MapTab      from './MapTab'
import SplitTab    from './SplitTab'
import DecisionTab from './DecisionTab'
import AuditTab    from './AuditTab'

const TABS = [
  { id: 'map',      label: '🗺 Live Map' },
  { id: 'split',    label: '⚡ Traditional vs AI' },
  { id: 'decision', label: '📊 Decision Matrix' },
  { id: 'audit',    label: '📋 Audit Trail' },
]

export default function LeftPanel({
  activeTab, onTabChange,
  scenario, mapRoute, mapStatus, mapStatusColor,
  truckPhase, onTruckPhaseChange, phase,
  mcDistribution, mcStats, auditItems,
  messages, resolutionTime, costSaved,
  // ── NEW PROPS ──────────────────────────────────────────────────────────
  runId,          // string | null  — current run UUID
  isRunning,      // bool           — scenario in progress
  approvalData,   // object | null  — from SSE approval_required event
}) {
  return (
    <div className="left">
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
        />
      </div>

      {/* DecisionTab now fetches its own data via useDecisionMatrix() */}
      <div className={`tpane${activeTab === 'decision' ? ' on' : ''}`}>
        <DecisionTab
          runId={runId}
          scenario={scenario}
          mcDistribution={mcDistribution}
          mcStats={mcStats}
          isActive={activeTab === 'decision'}
          approvalData={approvalData}
          isRunning={isRunning}
        />
      </div>

      {/* AuditTab now fetches its own data via useAuditTrail() */}
      <div className={`tpane${activeTab === 'audit' ? ' on' : ''}`}>
        <AuditTab
          runId={runId}
          auditItems={auditItems}
          scenario={scenario}
          isRunning={isRunning}
        />
      </div>
    </div>
  )
}
