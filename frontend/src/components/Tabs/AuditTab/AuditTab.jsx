const AuditTab = () => {
  return (
    <div className="p-4 overflow-y-auto flex-1">
      <div className="flex items-center justify-between mb-3">
        <div className="text-[10px] font-bold text-[#7aa0be] uppercase tracking-wide">Decision Audit Trail</div>
        <button className="px-[10px] py-1 bg-[#111820] border border-[#223040] rounded text-[#7aa0be] text-[10px] cursor-pointer hover:text-[#ddeeff] hover:border-[#00d4ff] transition-all duration-200">
          ⬇ Export PDF
        </button>
      </div>
      
      <div className="relative pl-5">
        {/* Timeline line */}
        <div className="absolute left-[5px] top-0 bottom-0 w-px bg-[#1d2d40]"></div>
        
        <div className="relative mb-3">
          <div className="absolute left-[-17px] top-1 w-[7px] h-[7px] rounded-full border-2" style={{ borderColor: '#ff3b5c', backgroundColor: '#ff3b5c' }}></div>
          <div className="font-mono text-[10px] text-[#3d5a72] mb-[3px]">00:00 — Crisis Detected</div>
          <div className="bg-[#111820] border border-[#1d2d40] rounded p-2">
            <div className="text-[11px] font-bold mb-[2px] text-[#ff3b5c]">🔴 System Monitor</div>
            <div className="text-[10px] text-[#5a7a94] leading-[1.45] mb-1">Strike detected. SC-2024-8891 BLOCKED at Long Beach. P0 broadcast to all agents.</div>
            <div className="font-mono text-[9px] text-[#00d4ff] bg-[rgba(0,212,255,0.05)] px-[6px] py-[3px] rounded">penalty_risk: $2M · deadline: 48h · contract: Apple</div>
          </div>
        </div>
        
        <div className="relative mb-3">
          <div className="absolute left-[-17px] top-1 w-[7px] h-[7px] rounded-full border-2" style={{ borderColor: '#00d4ff', backgroundColor: '#00d4ff' }}></div>
          <div className="font-mono text-[10px] text-[#3d5a72] mb-[3px]">00:12 — Route Options</div>
          <div className="bg-[#111820] border border-[#1d2d40] rounded p-2">
            <div className="text-[11px] font-bold mb-[2px] text-[#00d4ff]">🔵 Logistics Agent</div>
            <div className="text-[10px] text-[#5a7a94] leading-[1.45] mb-1">3 options generated. Memory recalled March 2024 LA port strike — hybrid saved $180K.</div>
            <div className="font-mono text-[9px] text-[#00d4ff] bg-[rgba(0,212,255,0.05)] px-[6px] py-[3px] rounded">check_freight_rates() · memory_recall("LA_strike_2024")</div>
            <div className="inline-flex items-center bg-[rgba(155,93,229,0.1)] border border-[rgba(155,93,229,0.3)] rounded px-[7px] py-[2px] text-[9px] text-[#9b5de5] font-mono mt-1">
              📚 Historical: LA Strike Mar 2024 — hybrid saved $180K
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuditTab;
