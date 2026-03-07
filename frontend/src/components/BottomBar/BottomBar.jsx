import { useAppStore } from '../../store/useAppStore';
import { scenarios } from '../../data/mockData';

const BottomBar = () => {
  const {
    resolutionTime,
    costSaved,
    messageCount,
    shipmentsPerYear,
    setShipmentsPerYear,
    currentScenario,
    setCurrentScenario
  } = useAppStore();

  const handleROIChange = (e) => {
    const count = parseInt(e.target.value);
    setShipmentsPerYear(count);
  };

  const calculateAnnualSavings = () => {
    const savingsPerShipment = 220000; // $220K saved per shipment
    const annualSavings = (shipmentsPerYear * savingsPerShipment) / 1000000; // Convert to millions
    return `$${annualSavings.toFixed(1)}M/yr`;
  };

  return (
    <div className="h-[46px] flex-shrink-0 bg-[#0c1119] border-t border-[#1d2d40] flex items-center justify-between px-[18px] gap-[10px] overflow-hidden">
      {/* Metrics */}
      <div className="flex gap-[18px]">
        <div className="flex flex-col">
          <span className="text-[8px] uppercase tracking-wide text-[#3d5a72] font-mono">Resolution</span>
          <span className="font-mono text-[14px] font-bold text-[#00d4ff]">{resolutionTime}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[8px] uppercase tracking-wide text-[#3d5a72] font-mono">Cost Saved</span>
          <span className="font-mono text-[14px] font-bold text-[#00e676]">{costSaved}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[8px] uppercase tracking-wide text-[#3d5a72] font-mono">Traditional</span>
          <span className="font-mono text-[14px] font-bold text-[#ff3b5c]">72 hrs</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[8px] uppercase tracking-wide text-[#3d5a72] font-mono">Messages</span>
          <span className="font-mono text-[14px] font-bold text-[#00d4ff]">{messageCount}</span>
        </div>
      </div>

      {/* ROI Calculator */}
      <div className="flex items-center gap-[7px]">
        <span className="text-[10px] text-[#7aa0be] whitespace-nowrap">Shipments/yr:</span>
        <input
          type="range"
          min="50"
          max="500"
          value={shipmentsPerYear}
          onChange={handleROIChange}
          className="w-20"
        />
        <span className="min-w-[28px] font-mono text-[11px] text-[#ddeeff]">{shipmentsPerYear}</span>
        <span className="text-[10px] text-[#7aa0be]">→ Annual savings:</span>
        <span className="font-mono text-[14px] font-bold text-[#00e676] min-w-[74px]">
          {calculateAnnualSavings()}
        </span>
      </div>

      {/* Scenario Selector */}
      <div className="flex items-center gap-[7px]">
        <span className="text-[9px] text-[#3d5a72] font-mono">SCENARIO</span>
        <select
          className="bg-[#111820] border border-[#223040] rounded px-[7px] py-1 text-[#ddeeff] text-[10px] font-['Syne'] outline-none cursor-pointer"
          value={currentScenario}
          onChange={(e) => setCurrentScenario(e.target.value)}
        >
          <option value="port_strike">🔴 Port Strike (Long Beach)</option>
          <option value="customs_delay">🟡 Customs Delay (China)</option>
          <option value="supplier_breach">🟠 Supplier Bankruptcy</option>
        </select>
      </div>
    </div>
  );
};

export default BottomBar;
