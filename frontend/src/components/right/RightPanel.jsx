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
  return (
    <div className="right">
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
