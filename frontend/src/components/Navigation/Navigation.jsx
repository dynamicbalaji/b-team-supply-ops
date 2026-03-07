import { useAppStore } from '../../store/useAppStore';
import { useScenarioEngine } from '../../hooks/useScenarioEngine';
import { scenarios } from '../../data/mockData';

const Navigation = () => {
  const { 
    currentScenario,
    demoDropdownOpen,
    toggleDemoDropdown,
    closeDemoDropdown,
    setCurrentScenario,
    resetScenario
  } = useAppStore();

  const { startScenario } = useScenarioEngine();

  const handleScenarioChange = (scenarioId) => {
    setCurrentScenario(scenarioId);
    closeDemoDropdown();
  };

  const handleStartScenario = () => {
    startScenario();
    closeDemoDropdown();
  };

  const handleReset = () => {
    resetScenario();
    window.location.reload();
  };

  const handleManualMode = () => {
    alert('Manual Mode Script\n\n' +
      '1. ORCHESTRATOR → ALL: "Crisis P0 — evaluate options"\n' +
      '2. LOGISTICS: Air $450K + Hybrid $280K option. Recalls March 2024 LA strike.\n' +
      '3. PROCUREMENT: Dallas spot buy, 80% qty, $380K\n' +
      '4. FINANCE: Challenges $450K — customs +$50K → Monte Carlo → Hybrid wins 94% CI\n' +
      '5. SALES: Apple accepts 36h extension, zero penalty\n' +
      '6. RISK AGENT: LAX single point of failure — backup trigger H20\n' +
      '7. FINANCE: Final proposal $280K + $20K reserve\n' +
      '8. Click APPROVE → execution cascade fires');
  };

  return (
    <nav className="h-[50px] flex-shrink-0 bg-[#0c1119] border-b border-[#1d2d40] flex items-center justify-between px-[18px] relative z-[300]">
      {/* Logo */}
      <div className="flex items-center gap-2 text-base font-extrabold">
        <div className="w-[26px] h-[26px] bg-gradient-to-br from-cyan-400 to-violet-500 rounded-md flex items-center justify-center text-[13px] shadow-lg shadow-cyan-400/20 animate-pulse-glow">
          ⬡
        </div>
        <span className="bg-gradient-to-r from-white to-cyan-200 bg-clip-text text-transparent drop-shadow-sm">
          ChainGuard
        </span>
        <span className="text-[#00d4ff] drop-shadow-sm">AI</span>
      </div>

      {/* Alert */}
      <div className="flex items-center gap-[7px] font-mono text-[10px] text-[#ff3b5c] tracking-wide animate-pulse">
        <div className="w-[7px] h-[7px] rounded-full bg-[#ff3b5c] shadow-[0_0_8px_#ff3b5c]"></div>
        THREAT LEVEL: CRITICAL — P0 INCIDENT ACTIVE
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2">
        <div className="px-[10px] py-[3px] rounded-full text-[10px] font-mono border border-[#223040] text-[#7aa0be] bg-[#111820]">
          SC-2024-8891
        </div>
        <div className="px-[10px] py-[3px] rounded-full text-[10px] font-mono border border-[#2a3820] text-[#ffb340] bg-[#111820]">
          48h WINDOW
        </div>
        
        {/* Demo Control Button */}
        <button 
          className="px-[13px] py-[5px] rounded text-[11px] font-bold cursor-pointer border border-[#223040] bg-[#111820] text-[#7aa0be] hover:text-[#ddeeff] hover:border-[#00d4ff] transition-all duration-200"
          onClick={toggleDemoDropdown}
        >
          ⚙ DEMO CTRL
        </button>
        
        <button 
          className="px-[13px] py-[5px] rounded text-[11px] font-bold cursor-pointer border border-[#ff3b5c] bg-[#ff3b5c] text-white hover:bg-[#ff5a75] transition-all duration-200"
          onClick={handleReset}
        >
          ↺ RESET
        </button>

        {/* Demo Dropdown */}
        {demoDropdownOpen && (
          <div className="absolute top-[52px] right-[14px] w-[215px] bg-[#111820] border border-[#223040] rounded-lg p-[14px] z-[500] shadow-[0_10px_40px_rgba(0,0,0,0.8)]">
            <div className="text-[9px] font-bold uppercase tracking-[1.5px] text-[#3d5a72] mb-[10px]">
              Demo Controller
            </div>
            
            <select 
              className="w-full bg-[#0c1119] border border-[#223040] rounded text-[#ddeeff] text-[11px] font-['Syne'] px-[9px] py-[6px] outline-none mb-2"
              value={currentScenario}
              onChange={(e) => handleScenarioChange(e.target.value)}
            >
              <option value="port_strike">🔴 Port Strike — Long Beach</option>
              <option value="customs_delay">🟡 Customs Delay — Shanghai</option>
              <option value="supplier_breach">🟠 Supplier Bankruptcy — Taiwan</option>
            </select>
            
            <button 
              className="w-full p-2 bg-gradient-to-br from-[#00d4ff] to-[#9b5de5] border-none rounded text-white font-['Syne'] text-xs font-bold cursor-pointer hover:opacity-90 transition-opacity duration-200"
              onClick={handleStartScenario}
            >
              ▶ Start Scenario
            </button>
            
            <button 
              className="w-full mt-[6px] p-[5px] bg-transparent border border-[#1d2d40] rounded text-[#3d5a72] font-['Syne'] text-[10px] cursor-pointer hover:text-[#7aa0be] transition-colors duration-200"
              onClick={handleManualMode}
            >
              📜 Manual Mode Script
            </button>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navigation;
