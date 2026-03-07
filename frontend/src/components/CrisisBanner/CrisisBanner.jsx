import { useEffect } from 'react';

const CrisisBanner = ({ scenario, costAccumulated }) => {
  const formatCost = (cost) => {
    return `$${cost.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
  };

  return (
    <div className="relative overflow-hidden">
      {/* Animated background gradient */}
      <div className="absolute inset-0 bg-gradient-to-r from-red-500/10 via-red-400/5 to-red-500/10 animate-pulse"></div>
      
      {/* Moving light effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-red-500/20 to-transparent animate-slide transform -skew-x-12"></div>
      
      <div className="relative h-[46px] flex-shrink-0 bg-[#140609] border-b-2 border-[rgba(255,59,92,0.55)] flex items-center justify-between px-[18px] shadow-lg shadow-red-500/20">
        {/* Crisis Info */}
        <div className="flex items-center min-w-0 overflow-hidden">
          <span className="bg-[#ff3b5c] text-white text-[9px] font-bold px-2 py-[2px] rounded-sm tracking-wide flex-shrink-0 shadow-lg shadow-red-500/40 animate-pulse">
            {scenario?.severity || 'CRITICAL'}
          </span>
          <span className="text-[12px] font-semibold text-[#ffd4dc] ml-[10px] whitespace-nowrap overflow-hidden text-ellipsis">
            <span className="font-bold text-white drop-shadow-sm">{scenario?.title}</span> {scenario?.crisis}
          </span>
        </div>

        {/* Cost Ticker */}
        <div className="text-right flex-shrink-0 ml-4">
          <div className="text-[9px] text-[#3d5a72] uppercase tracking-wide font-mono">
            Cost accumulating
          </div>
          <div className="text-[19px] font-bold text-[#ff3b5c] font-mono drop-shadow-sm animate-pulse-glow">
            {formatCost(costAccumulated)}
          </div>
          <div className="text-[9px] text-[#3d5a72] font-mono">
            Traditional: ~$149K/72h
          </div>
        </div>
      </div>
    </div>
  );
};

export default CrisisBanner;
