const DecisionTab = () => {
  return (
    <div className="p-4 overflow-y-auto flex-1">
      <div className="bg-[#111820] border border-[#1d2d40] rounded-lg p-[13px] mb-4">
        <div className="flex items-center justify-between mb-3">
          <div className="text-[10px] font-bold text-[#7aa0be] uppercase tracking-wide">⚡ What-If Editor</div>
          <span className="inline-block px-[7px] py-[2px] rounded bg-[rgba(255,179,64,0.12)] text-[#ffb340] border border-[rgba(255,179,64,0.3)] text-[9px] font-bold">LIVE RECALC</span>
        </div>
        
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-[#7aa0be]">Contract Penalty</span>
            <div className="flex items-center gap-2">
              <input type="range" min="500" max="5000" defaultValue="2000" className="w-[84px]" />
              <span className="font-mono text-[11px] text-[#00d4ff] min-w-[52px] text-right">$2.0M</span>
            </div>
          </div>
        </div>
        
        <div className="mt-2 p-[6px_9px] bg-[rgba(0,212,255,0.05)] border border-[rgba(0,212,255,0.15)] rounded text-[10px] text-[#00d4ff] font-mono">
          → Hybrid saves $220K · Optimal within all constraints
        </div>
      </div>
      
      <div className="flex items-center justify-between mb-3">
        <div className="text-[10px] font-bold text-[#7aa0be] uppercase tracking-wide">Decision Matrix</div>
        <span className="inline-block px-[7px] py-[2px] rounded bg-[rgba(0,230,118,0.18)] text-[#00e676] border border-[rgba(0,230,118,0.4)] text-[9px] font-bold">✦ HYBRID OPTIMAL</span>
      </div>
      
      <table className="w-full border-collapse text-[11px] mb-4">
        <thead>
          <tr>
            <th className="text-left p-[6px_9px] text-[9px] font-bold uppercase tracking-wide text-[#3d5a72] border-b border-[#1d2d40] bg-[#090e15] font-mono">Option</th>
            <th className="text-left p-[6px_9px] text-[9px] font-bold uppercase tracking-wide text-[#3d5a72] border-b border-[#1d2d40] bg-[#090e15] font-mono">Cost</th>
            <th className="text-left p-[6px_9px] text-[9px] font-bold uppercase tracking-wide text-[#3d5a72] border-b border-[#1d2d40] bg-[#090e15] font-mono">Time</th>
            <th className="text-left p-[6px_9px] text-[9px] font-bold uppercase tracking-wide text-[#3d5a72] border-b border-[#1d2d40] bg-[#090e15] font-mono">Risk</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td className="p-[8px_9px] border-b border-[#1d2d40] font-mono text-[#7aa0be]">
              <span className="font-bold text-[#ddeeff] font-['Syne'] text-[11px]">Air Freight</span>
            </td>
            <td className="p-[8px_9px] border-b border-[#1d2d40] font-mono text-[#ff3b5c]">$500K</td>
            <td className="p-[8px_9px] border-b border-[#1d2d40] font-mono text-[#7aa0be]">24h</td>
            <td className="p-[8px_9px] border-b border-[#1d2d40] font-mono text-[#7aa0be]">2/10</td>
          </tr>
          <tr className="bg-[rgba(0,230,118,0.04)]">
            <td className="p-[8px_9px] border-b border-[#1d2d40] font-mono text-[#ddeeff]">
              <span className="font-bold text-[#00e676] font-['Syne'] text-[11px]">✦ Hybrid</span>
            </td>
            <td className="p-[8px_9px] border-b border-[#1d2d40] font-mono text-[#00e676]">$280K</td>
            <td className="p-[8px_9px] border-b border-[#1d2d40] font-mono text-[#ddeeff]">36h</td>
            <td className="p-[8px_9px] border-b border-[#1d2d40] font-mono text-[#ddeeff]">4/10</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
};

export default DecisionTab;
