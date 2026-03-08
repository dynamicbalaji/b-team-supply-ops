import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble'

export default function ChatPanel({ messages = [] }) {
  const bottomRef = useRef(null)

  // Auto-scroll to bottom whenever messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="chat">
      {/* Header */}
      <div className="chat-hdr">
        <span className="chat-title">⬡ A2A Negotiation Log</span>
        <span className="chat-cnt">{messages.length} messages</span>
      </div>

      {/* Message feed */}
      <div className="msgs">
        {messages.length === 0 ? (
          <div className="msg-empty">
            <div className="msg-empty-icon">🤝</div>
            <div className="msg-empty-txt">Awaiting agents</div>
            <div className="msg-empty-sub">Start a scenario to begin</div>
          </div>
        ) : (
          <>
            {messages.map(msg => (
              <MessageBubble key={msg.id} msg={msg} />
            ))}
            {/* Invisible scroll target */}
            <div ref={bottomRef} />
          </>
        )}
      </div>
    </div>
  )
}
