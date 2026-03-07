import { useAppStore } from '../../store/useAppStore';

const AgentNetwork = () => {
  const { 
    agents, 
    agentCount, 
    riskAgent, 
    agentPanelCollapsed, 
    toggleAgentPanel 
  } = useAppStore();

  const getStatusClass = (status) => {
    switch(status) {
      case 'PROCESSING':
        return 'text-[#ffb340]';
      case 'ONLINE':
        return 'text-[#00e676]';
      case 'ANALYZING':
        return 'text-[#00d4ff]';
      case 'INTERFACING':
        return 'text-[#9b5de5]';
      default:
        return 'text-[#3d5a72]';
    }
  };

  return (
    <div className="flex-shrink-0 border-b border-[#1d2d40] max-h-[60vh] flex flex-col overflow-hidden">
      {/* Header */}
      <div 
        className="flex items-center justify-between p-[9px_13px] cursor-pointer bg-[#0c1119] hover:bg-[#101820] select-none flex-shrink-0"
        onClick={toggleAgentPanel}
      >
        <div className="text-[10px] font-bold uppercase tracking-wide text-[#7aa0be] flex items-center gap-[7px]">
          ⬡ Agent Network
          <div className="inline-flex items-center gap-1 text-[9px] font-mono text-[#00e676] bg-[rgba(0,230,118,0.08)] border border-[rgba(0,230,118,0.2)] rounded-full px-[7px] py-[1px]">
            <div className="w-[5px] h-[5px] rounded-full bg-[#00e676] animate-pulse"></div>
            <span>{agentCount} active</span>
          </div>
        </div>
        <div className={`text-[10px] text-[#3d5a72] transition-transform duration-250 font-mono ${agentPanelCollapsed ? '' : 'rotate-180'}`}>
          {agentPanelCollapsed ? '▸ show agents' : '▾'}
        </div>
      </div>

      {/* Body */}
      {!agentPanelCollapsed && (
        <div className="flex-1 overflow-y-auto overflow-x-hidden p-[10px_12px_11px] min-h-0 custom-scrollbar">
          <div className="grid grid-cols-2 gap-[6px] mb-[7px]">
            {agents.map(agent => {
              const colorStyles = {
                blue: { 
                  color: '#00d4ff', 
                  borderTop: 'border-t-[#00d4ff]',
                  bg: 'bg-[#111820]'
                },
                green: { 
                  color: '#00e676', 
                  borderTop: 'border-t-[#00e676]',
                  bg: 'bg-[#111820]' 
                },
                orange: { 
                  color: '#ffb340', 
                  borderTop: 'border-t-[#ffb340]',
                  bg: 'bg-[#111820]'
                },
                purple: { 
                  color: '#9b5de5', 
                  borderTop: 'border-t-[#9b5de5]',
                  bg: 'bg-[#111820]'
                }
              };
              
              const style = colorStyles[agent.color] || colorStyles.blue;
              
              return (
                <div 
                  key={agent.id}
                  className={`${style.bg} border border-[#1d2d40] rounded-md p-2 relative overflow-hidden border-t-2 ${style.borderTop} shadow-sm hover:shadow-lg transition-all duration-300 hover:scale-[1.02]`}
                  style={{ color: style.color }}
                >
                  <div className="flex items-center justify-between mb-[3px]">
                    <span className="text-[9px] font-bold text-current drop-shadow-sm">{agent.name}</span>
                    <span 
                      className={`w-[5px] h-[5px] rounded-full bg-current shadow-sm ${agent.pulsing ? 'animate-ping' : ''}`}
                    ></span>
                  </div>
                  
                  <div className={`font-mono text-[8px] mb-1 ${getStatusClass(agent.status)}`}>
                    {agent.status}
                  </div>
                  
                  <div className="flex items-center gap-1 mb-2">
                    <div className="flex-1 h-[3px] bg-[#1d2d40] rounded-sm overflow-hidden shadow-inner">
                      <div 
                        className="h-full rounded-sm transition-all duration-1200 ease-out bg-current shadow-sm animate-glow"
                        style={{ width: `${agent.confidence}%` }}
                      ></div>
                    </div>
                    <span className="font-mono text-[8px] min-w-[24px] text-current drop-shadow-sm">
                      {agent.confidence > 0 ? `${agent.confidence}%` : '—'}
                    </span>
                  </div>
                  
                  <div className="inline-flex items-center bg-[rgba(0,0,0,0.25)] border border-[#1d2d40] rounded-full px-[7px] py-[2px] font-mono text-[8px] text-[#3d5a72] mt-[5px] shadow-sm">
                    {agent.tool}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Risk Agent */}
          {riskAgent.visible && (
            <div className="rounded-md p-2 border border-[rgba(255,59,92,0.25)] bg-[rgba(255,59,92,0.06)] flex-shrink-0">
              <div className="flex items-center gap-[6px] mb-[5px]">
                <span className="text-[10px] font-bold text-[#ff3b5c]">⚠ RISK AGENT</span>
                <span className="text-[8px] bg-[#ff3b5c] text-white px-[5px] py-[1px] rounded-sm font-mono">DEVIL'S ADVOCATE</span>
                <span className="w-[6px] h-[6px] rounded-full bg-[#ff3b5c] animate-pulse ml-auto"></span>
              </div>
              <div className="text-[10px] text-[#ffccd4] leading-relaxed">
                {riskAgent.message}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AgentNetwork;
