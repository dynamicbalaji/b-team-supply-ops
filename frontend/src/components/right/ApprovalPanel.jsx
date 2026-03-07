export default function ApprovalPanel({ visible, data, onApprove, onReject }) {
  if (!visible || !data) return null

  const cost       = data.cost       ?? 280000
  const confidence = data.confidence ?? 0.94
  const option     = data.option     ?? 'hybrid'

  return (
    <div className="approval">
      <div className="apcard">
        <div className="ap-title">⏸ AWAITING HUMAN APPROVAL</div>

        <div className="ap-opt">
          {option.toUpperCase()} Route — 60% Air / 40% Sea
        </div>

        <div className="ap-det">
          ${Math.round(cost / 1000)}K + $20K reserve · 36h delivery · Backup H20 · Apple: ✓ · Confidence: {Math.round(confidence * 100)}%
        </div>

        <div className="ap-acts">
          <button
            className="appbtn"
            onClick={onApprove}
            style={{ animation: 'approvalPulse 2s infinite' }}
          >
            ✓ APPROVE &amp; EXECUTE
          </button>
          <button className="rejbtn" onClick={onReject}>
            ✗ Reject
          </button>
        </div>
      </div>
    </div>
  )
}
