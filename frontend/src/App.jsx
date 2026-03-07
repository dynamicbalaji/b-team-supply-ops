import { useState, useEffect } from 'react';
import { useAppStore } from './store/useAppStore';
import Navigation from './components/Navigation/Navigation';
import CrisisBanner from './components/CrisisBanner/CrisisBanner';
import MainContent from './components/MainContent/MainContent';
import BottomBar from './components/BottomBar/BottomBar';
import { scenarios } from './data/mockData';

function App() {
  const { 
    currentScenario, 
    costAccumulated, 
    updateCostAccumulator, 
    costStart 
  } = useAppStore();

  // Cost accumulator effect
  useEffect(() => {
    if (!costStart) return;
    
    const interval = setInterval(() => {
      updateCostAccumulator();
    }, 120); // Update every 120ms like the original

    return () => clearInterval(interval);
  }, [costStart, updateCostAccumulator]);

  const currentScenarioData = scenarios[currentScenario];

  return (
    <div className="min-h-screen bg-[#06090f] text-[#ddeeff] flex flex-col font-['Syne'] overflow-hidden">
      <Navigation />
      <CrisisBanner 
        scenario={currentScenarioData} 
        costAccumulated={costAccumulated}
      />
      <MainContent />
      <BottomBar />
    </div>
  );
}

export default App;
