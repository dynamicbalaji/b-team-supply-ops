import { useEffect, useRef, useState } from 'react';
import { useAppStore } from '../../store/useAppStore';

const Chat = () => {
  const messagesEndRef = useRef(null);
  const { 
    messages, 
    messageCount, 
    showApproval: showApprovalPanel,
    addMessage,
    setPhase,
    setMapStatus,
    setMapRoute,
    setTruckPhase,
    updateAgent,
    hideApproval
  } = useAppStore();
  
  const [approving, setApproving] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleApprove = () => {
    setApproving(true);
    
    // Start truck animation and update status
    setTruckPhase('flying', 0);
    setPhase(3, 'done');
    setPhase(4, 'active');
    setMapStatus('EXECUTING');
    setMapRoute('✈ Freight booked → Austin');
    
    // Cascade messages like in original
    const cascade = [
      { from: '✈ LOGISTICS', className: 'al', time: '04:32', body: 'Freight booked: LAX → Austin TX · FX-2024-8891 · ETA 36h' },
      { from: '📧 SALES', className: 'as_', time: '04:33', body: 'Apple notified — 36h extension confirmed · Q3 priority allocation logged' },
      { from: '💰 FINANCE', className: 'af', time: '04:34', body: 'Budget released: $280K · Contingency $20K · PO #F-7741 issued' },
      { from: '🚫 PROCUREMENT', className: 'ap', time: '04:35', body: 'Dallas spot order cancelled · Tucson backup scheduled for Hour 20' }
    ];
    
    cascade.forEach((msg, i) => {
      setTimeout(() => {
        addMessage({
          from: msg.from,
          to: '→ EXEC',
          time: msg.time,
          className: msg.className,
          body: msg.body,
          tools: null
        });
      }, i * 700);
    });
    
    setTimeout(() => {
      setApproving(false);
      hideApproval();
      setTruckPhase('driving', 0);
      setPhase(4, 'done');
      setMapStatus('DELIVERED ✅');
      
      // Update all agents to complete
      updateAgent('log', { status: 'COMPLETE', statusClass: 'done', tool: '✅ done', confidence: 88, pulsing: false });
      updateAgent('fin', { status: 'COMPLETE', statusClass: 'done', tool: '✅ done', confidence: 94, pulsing: false });
      updateAgent('pro', { status: 'COMPLETE', statusClass: 'done', tool: '✅ done', confidence: 71, pulsing: false });
      updateAgent('sal', { status: 'COMPLETE', statusClass: 'done', tool: '✅ done', confidence: 97, pulsing: false });
    }, 3200);
  };

  const getMessageColors = (className) => {
    switch (className) {
      case 'orc': return { bg: 'bg-[#081624]', border: 'border-[rgba(0,212,255,0.2)]', borderLeft: 'border-l-[#00d4ff]', text: 'text-[#c0dded]' };
      case 'al': return { bg: 'bg-[#071824]', border: 'border-[rgba(0,212,255,0.15)]', borderLeft: 'border-l-[#00d4ff]', text: 'text-[#c0dded]' };
      case 'af': return { bg: 'bg-[#061a10]', border: 'border-[rgba(0,230,118,0.15)]', borderLeft: 'border-l-[#00e676]', text: 'text-[#bce8cc]' };
      case 'ap': return { bg: 'bg-[#1a1408]', border: 'border-[rgba(255,179,64,0.15)]', borderLeft: 'border-l-[#ffb340]', text: 'text-[#e8d8b0]' };
      case 'as_': return { bg: 'bg-[#100d1e]', border: 'border-[rgba(155,93,229,0.15)]', borderLeft: 'border-l-[#9b5de5]', text: 'text-[#ccbce8]' };
      case 'ar': return { bg: 'bg-[#1a0610]', border: 'border-[rgba(255,59,92,0.2)]', borderLeft: 'border-l-[#ff3b5c]', text: 'text-[#f0b8c4]' };
      default: return { bg: 'bg-[#081624]', border: 'border-[rgba(0,212,255,0.2)]', borderLeft: 'border-l-[#00d4ff]', text: 'text-[#c0dded]' };
    }
  };

  const getFromColor = (className) => {
    switch (className) {
      case 'orc':
      case 'al': return 'text-[#00d4ff]';
      case 'af': return 'text-[#00e676]';
      case 'ap': return 'text-[#ffb340]';
      case 'as_': return 'text-[#9b5de5]';
      case 'ar': return 'text-[#ff3b5c]';
      default: return 'text-[#00d4ff]';
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
      {/* Header - Fixed at top */}
      <div className="p-[9px_13px] border-b border-[#1d2d40] flex items-center justify-between flex-shrink-0 bg-[#0c1119] sticky top-0 z-10">
        <span className="text-[10px] font-bold uppercase tracking-wide text-[#7aa0be]">⬡ A2A Negotiation Log</span>
        <span className="font-mono text-[9px] text-[#3d5a72] bg-[#111820] px-2 py-[2px] rounded-full border border-[#1d2d40]">
          {messageCount} messages
        </span>
      </div>

      {/* Messages - Scroll behind header */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden bg-[#07090f] min-h-0 custom-scrollbar relative">
        <div className="p-[10px_11px] flex flex-col gap-[7px] h-[400px]">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center min-h-[200px] gap-[9px] opacity-35">
              <div className="text-[28px]">⬡</div>
              <div className="font-mono text-[11px] text-[#3d5a72]">Awaiting scenario start</div>
              <div className="text-[10px] text-[#3d5a72]">Click ⚙ DEMO CTRL → Start Scenario</div>
            </div>
          ) : (
            <>
              {messages.map((message) => {
                const colors = getMessageColors(message.className);
                const fromColor = getFromColor(message.className);
                
                return (
                  <div key={message.id} className="flex flex-col gap-[3px] flex-shrink-0">
                    <div className="flex items-center gap-[5px]">
                      <span className={`text-[10px] font-bold ${fromColor}`}>
                        {message.from}
                      </span>
                      <span className="text-[9px] text-[#3d5a72] font-mono">
                        {message.to}
                      </span>
                      <span className="text-[9px] text-[#3d5a72] font-mono ml-auto">
                        {message.time}
                      </span>
                    </div>
                    <div className={`rounded-[0_7px_7px_7px] p-[7px_10px] text-[11px] leading-relaxed border border-l-2 ${colors.bg} ${colors.border} ${colors.borderLeft} ${colors.text} break-words`}>
                      <div dangerouslySetInnerHTML={{ __html: message.body }} />
                      {message.tools && (
                        <div className="flex flex-wrap gap-[3px] mt-[5px]">
                          {message.tools.map((tool, index) => (
                            <span key={index} className="inline-flex items-center bg-[rgba(0,0,0,0.25)] border border-[#1d2d40] rounded-full px-[7px] py-[2px] font-mono text-[8px] text-[#3d5a72]">
                              {tool}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </div>

      {/* Approval Panel */}
      {showApprovalPanel && (
        <div className="p-[10px] border-t border-[#1d2d40] flex-shrink-0">
          <div className="bg-[rgba(0,230,118,0.07)] border border-[rgba(0,230,118,0.25)] rounded-lg p-[10px]">
            <div className="text-[10px] font-bold text-[#00e676] mb-[5px]">⏸ AWAITING HUMAN APPROVAL</div>
            <div className="text-[13px] font-extrabold text-[#ddeeff] mb-[3px]">Hybrid Route — 60% Air / 40% Sea</div>
            <div className="text-[10px] text-[#7aa0be] leading-relaxed mb-2">
              $280K + $20K reserve · 36h delivery · Backup trigger H20 · Apple: ✓ · Confidence: 94%
            </div>
            <div className="flex gap-[7px]">
              <button 
                className={`flex-1 p-2 border-none rounded font-['Syne'] text-[11px] font-extrabold cursor-pointer transition-all duration-200 ${
                  approving 
                    ? 'bg-[#00a8cc] text-white' 
                    : 'bg-[#00e676] text-[#021a09] hover:bg-[#33eb91]'
                }`}
                onClick={handleApprove}
                disabled={approving}
              >
                {approving ? '⟳ Executing...' : '✓ APPROVE & EXECUTE'}
              </button>
              <button className="px-[13px] py-2 bg-transparent border border-[#223040] rounded text-[#7aa0be] font-['Syne'] text-[11px] cursor-pointer hover:border-[#ff3b5c] hover:text-[#ff3b5c] transition-all duration-200">
                ✗ Reject
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Chat;
