import { useState } from 'react'

export default function ApprovalPanel({ visible, data, onApprove, onReject }) {
  const [showRejectForm, setShowRejectForm] = useState(false)
  const [reason, setReason] = useState('')

  if (!visible || !data) return null

  const cost       = data.cost       ?? 280000
  const confidence = data.confidence ?? 0.94
  const option     = data.option     ?? 'hybrid'
  const label      = data.label      ?? `${option.toUpperCase()} Route`
  const detail     = data.detail     ?? ''
  const isAirOnly  = option === 'air_only'

  function handleReject() {
    onReject(reason)
    setShowRejectForm(false)
    setReason('')
  }

  return (
    <div className="approval">
      <div className="apcard">

        {/* Title — changes based on iteration */}
        <div className="ap-title" style={isAirOnly ? { color:'#ffb340' } : {}}>
          {isAirOnly ? '🔄 REVISED PROPOSAL — AGENT RE-NEGOTIATION' : '⏸ AWAITING HUMAN APPROVAL'}
        </div>

        {isAirOnly && (
          <div style={{
            fontSize:'9px', fontFamily:"'JetBrains Mono',monospace",
            color:'#ff3b5c', marginBottom:'6px', letterSpacing:'.05em',
          }}>
            ↩ Previous hybrid proposal was rejected — agents re-engaged
          </div>
        )}

        <div className="ap-opt" style={isAirOnly ? { color:'#ffb340' } : {}}>
          {label}
        </div>

        <div className="ap-det">
          {detail || `$${Math.round(cost/1000)}K + $20K reserve · ${isAirOnly ? '18h' : '36h'} delivery · Confidence: ${Math.round(confidence*100)}%`}
        </div>

        {/* Cost comparison pill */}
        <div style={{
          display:'flex', gap:'8px', margin:'8px 0',
          fontFamily:"'JetBrains Mono',monospace", fontSize:'9px',
        }}>
          <div style={{ padding:'3px 8px', background:'#0d2233', border:'1px solid #1a3a52', borderRadius:'4px', color:'#7aa0be' }}>
            Cost: <span style={{ color:'#c8dcea', fontWeight:'bold' }}>${Math.round(cost/1000)}K</span>
          </div>
          <div style={{ padding:'3px 8px', background:'#0d2233', border:'1px solid #1a3a52', borderRadius:'4px', color:'#7aa0be' }}>
            CI: <span style={{ color:'#39d98a', fontWeight:'bold' }}>{Math.round(confidence*100)}%</span>
          </div>
          <div style={{ padding:'3px 8px', background:'#0d2233', border:'1px solid #1a3a52', borderRadius:'4px', color:'#7aa0be' }}>
            ETA: <span style={{ color:'#00d4ff', fontWeight:'bold' }}>{isAirOnly ? '18h' : '36h'}</span>
          </div>
        </div>

        {!showRejectForm ? (
          <div className="ap-acts">
            <button
              className="appbtn"
              onClick={onApprove}
              style={{ animation: 'approvalPulse 2s infinite' }}
            >
              ✓ APPROVE &amp; EXECUTE
            </button>
            <button
              className="rejbtn"
              onClick={() => setShowRejectForm(true)}
            >
              ✗ Reject
            </button>
          </div>
        ) : (
          <div style={{ display:'flex', flexDirection:'column', gap:'8px', marginTop:'8px' }}>
            <div style={{
              fontSize:'9px', fontFamily:"'JetBrains Mono',monospace",
              color:'#ffb340', letterSpacing:'.05em',
            }}>
              REJECTION REASON — agents will re-negotiate
            </div>
            <textarea
              value={reason}
              onChange={e => setReason(e.target.value)}
              placeholder="e.g. Cost too high, need under $300K..."
              style={{
                width:'100%', padding:'7px', background:'#0d2233',
                border:'1px solid #ff3b5c55', borderRadius:'5px',
                color:'#c8dcea', fontSize:'10px', fontFamily:"'JetBrains Mono',monospace",
                resize:'none', height:'56px', boxSizing:'border-box',
                outline:'none',
              }}
            />
            <div style={{ display:'flex', gap:'6px' }}>
              <button
                className="rejbtn"
                onClick={handleReject}
                style={{ flex:1, background:'#ff3b5c22', borderColor:'#ff3b5c', color:'#ff3b5c', fontWeight:'bold' }}
              >
                ✗ Confirm Rejection — Re-engage Agents
              </button>
              <button
                className="rejbtn"
                onClick={() => { setShowRejectForm(false); setReason('') }}
                style={{ padding:'8px 10px' }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
