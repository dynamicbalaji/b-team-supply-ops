import { useEffect, useRef, useState } from 'react'
import AgentNetwork  from './AgentNetwork'
import ChatPanel     from './ChatPanel'
import ApprovalPanel from './ApprovalPanel'

export default function RightPanel({
  agents,
  riskAgent,
  messages,
  approvalVisible,
  approvalData,
  onApprove,
  onReject,
}) {
  const [flashing, setFlashing]   = useState(false)
  const prevVisibleRef            = useRef(false)

  // Flash the panel red when the risk agent first fires
  useEffect(() => {
    const nowVisible = riskAgent?.visible
    if (nowVisible && !prevVisibleRef.current) {
      setFlashing(true)
      const t = setTimeout(() => setFlashing(false), 600)
      prevVisibleRef.current = true
      return () => clearTimeout(t)
    }
    if (!nowVisible) prevVisibleRef.current = false
  }, [riskAgent?.visible])

  return (
    <div className={`right${flashing ? ' risk-flash' : ''}`}>
      <AgentNetwork
        agents={agents}
        riskAgent={riskAgent}
      />

      <ChatPanel
        messages={messages}
      />

      <ApprovalPanel
        visible={approvalVisible}
        data={approvalData}
        onApprove={onApprove}
        onReject={onReject}
      />
    </div>
  )
}
