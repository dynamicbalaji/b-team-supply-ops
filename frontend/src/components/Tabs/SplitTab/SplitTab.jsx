import { useState, useEffect } from 'react';
import { traditionalEmails, aiMessages } from '../../../data/mockData';

const SplitTab = () => {
  const [visibleTraditionalEmails, setVisibleTraditionalEmails] = useState([]);
  const [visibleAiMessages, setVisibleAiMessages] = useState([]);
  const [aiTimer, setAiTimer] = useState('00:00');

  useEffect(() => {
    // Traditional email animation
    traditionalEmails.forEach((email, index) => {
      setTimeout(() => {
        setVisibleTraditionalEmails(prev => [...prev, email]);
      }, email.delay * 1000);
    });

    // AI message animation  
    aiMessages.forEach((message, index) => {
      setTimeout(() => {
        setVisibleAiMessages(prev => [...prev, message]);
      }, message.delay * 1000);
    });

    // AI Timer
    const timerInterval = setInterval(() => {
      const now = Date.now();
      const seconds = Math.floor(now / 1000) % 300; // Reset every 5 minutes for demo
      const minutes = Math.floor(seconds / 60);
      const secs = seconds % 60;
      setAiTimer(`${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`);
    }, 1000);

    return () => clearInterval(timerInterval);
  }, []);

  return (
    <div className="grid grid-cols-2 flex-1 overflow-hidden">
      {/* Traditional Process */}
      <div className="p-[14px] overflow-y-auto border-r border-[#1d2d40] scrollbar-thin scrollbar-thumb-[#1d2d40]">
        <div className="flex items-center justify-between mb-3 pb-[9px] border-b border-[#1d2d40]">
          <div className="text-xs font-bold text-[#ff3b5c]">📧 Traditional Process</div>
          <div className="font-mono text-lg font-bold text-[#ff3b5c]">72:00:00</div>
        </div>
        
        {visibleTraditionalEmails.map((email, index) => (
          <div 
            key={index}
            className="bg-[#111820] border border-[#1d2d40] rounded p-2 mb-2 opacity-0 animate-fadein"
            style={{ animationDelay: `${email.delay}s`, animationFillMode: 'forwards' }}
          >
            <div className="flex justify-between mb-1">
              <span className="text-[11px] font-semibold text-[#7aa0be]">{email.from}</span>
              <span className="text-[10px] text-[#3d5a72] font-mono">{email.time}</span>
            </div>
            <div className="text-[11px] font-semibold text-[#ddeeff] mb-[3px]">{email.subject}</div>
            <div className="text-[10px] text-[#5a7a94] leading-relaxed">{email.body}</div>
          </div>
        ))}
        
        {visibleTraditionalEmails.length >= traditionalEmails.length && (
          <div className="bg-[rgba(255,59,92,0.1)] border border-[rgba(255,59,92,0.25)] rounded p-2 mt-2 text-center animate-fadein">
            <span className="text-[10px] text-[#ff3b5c] font-mono">⏱ 72 HOURS — $2M PENALTY TRIGGERED</span>
          </div>
        )}
      </div>

      {/* AI Process */}
      <div className="p-[14px] overflow-y-auto scrollbar-thin scrollbar-thumb-[#1d2d40]">
        <div className="flex items-center justify-between mb-3 pb-[9px] border-b border-[#1d2d40]">
          <div className="text-xs font-bold text-[#00e676]">🤖 ChainGuard AI</div>
          <div className="font-mono text-lg font-bold text-[#00e676]">{aiTimer}</div>
        </div>
        
        <div className="bg-[rgba(0,230,118,0.08)] border border-[rgba(0,230,118,0.2)] rounded p-2 mb-[10px] text-center">
          <span className="text-[10px] text-[#00e676] font-mono">✅ RESOLVED IN 4m 32s — Hybrid Route · $280K · saved $220K</span>
        </div>
        
        {visibleAiMessages.map((message, index) => {
          const colors = {
            al: 'border-l-[#00d4ff] border-[rgba(0,212,255,0.18)] bg-[rgba(0,212,255,0.04)]',
            af: 'border-l-[#00e676] border-[rgba(0,230,118,0.18)] bg-[rgba(0,230,118,0.04)]',
            as_: 'border-l-[#9b5de5] border-[rgba(155,93,229,0.18)] bg-[rgba(155,93,229,0.04)]',
            ar: 'border-l-[#ff3b5c] border-[rgba(255,59,92,0.18)] bg-[rgba(255,59,92,0.04)]'
          };
          
          const textColors = {
            al: 'text-[#00d4ff]',
            af: 'text-[#00e676]', 
            as_: 'text-[#9b5de5]',
            ar: 'text-[#ff3b5c]'
          };
          
          return (
            <div 
              key={index}
              className={`border-l-2 border rounded p-2 mb-2 opacity-0 animate-fadein ${colors[message.className]}`}
              style={{ animationDelay: `${message.delay}s`, animationFillMode: 'forwards' }}
            >
              <div className="flex justify-between mb-1">
                <span className={`text-[11px] font-semibold ${textColors[message.className]}`}>{message.from}</span>
                <span className="text-[10px] text-[#3d5a72] font-mono">{message.time}</span>
              </div>
              <div className="text-[11px] font-semibold text-[#ddeeff] mb-[3px]">{message.subject}</div>
              <div className="text-[10px] text-[#7aa0be] leading-relaxed mb-2">{message.body}</div>
              {message.tools && (
                <div className="flex flex-wrap gap-1">
                  {message.tools.map((tool, toolIndex) => (
                    <span key={toolIndex} className="text-[8px] bg-[rgba(0,0,0,0.25)] border border-[#1d2d40] rounded-full px-2 py-1 font-mono text-[#3d5a72]">
                      {tool}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SplitTab;
