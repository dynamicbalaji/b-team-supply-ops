import { useEffect, useRef } from 'react';
import { useAppStore } from '../store/useAppStore';

export const useScenarioEngine = () => {
  const {
    scenarioRunning,
    setScenarioRunning,
    agents,
    updateAgent,
    setAgentCount,
    showRiskAgent,
    addMessage,
    clearMessages,
    setPhase,
    setMapStatus,
    setMapRoute,
    setTruckPhase,
    showApproval,
    setResolutionTime,
    setCostSaved,
    resetScenario
  } = useAppStore();

  const timersRef = useRef([]);

  // Scenario steps matching the original HTML
  const scenarioSteps = [
    // t=0 — Orchestrator broadcasts
    {
      t: 0,
      fn: () => {
        setPhase(0, 'done');
        setPhase(1, 'active');
        setAgentCount(4);
        
        updateAgent('log', { status: 'ACTIVATING', statusClass: 'working', tool: '📡 broadcast_received()', confidence: 0, pulsing: true });
        updateAgent('fin', { status: 'ACTIVATING', statusClass: 'working', tool: '📡 broadcast_received()', confidence: 0, pulsing: true });
        updateAgent('pro', { status: 'ACTIVATING', statusClass: 'working', tool: '📡 broadcast_received()', confidence: 0, pulsing: true });
        updateAgent('sal', { status: 'ACTIVATING', statusClass: 'working', tool: '📡 broadcast_received()', confidence: 0, pulsing: true });
        
        addMessage({
          from: 'ORCHESTRATOR',
          to: '→ ALL',
          time: '00:00',
          className: 'orc',
          body: 'Crisis P0: SC-2024-8891 blocked at Long Beach. Budget cap $500K. Deadline 48h. Begin parallel evaluation.',
          tools: null
        });
        
        setMapStatus('AGENTS ACTIVE');
        setMapRoute('📡 Agents activated');
      }
    },
    
    // t=1.5s — Logistics proposes
    {
      t: 1500,
      fn: () => {
        setPhase(1, 'done');
        setPhase(2, 'active');
        
        updateAgent('log', { status: 'PROPOSING', statusClass: 'working', tool: '📦 check_freight_rates()', pulsing: true });
        
        addMessage({
          from: 'LOGISTICS',
          to: '→ ORCH',
          time: '00:12',
          className: 'al',
          body: 'Option A: Air via LAX — $450K / 24h / Low risk.<br>Recalled March 2024 LA strike — hybrid saved $180K then.',
          tools: ['📦 check_freight_rates()', '📚 memory_recall("LA_2024")']
        });
        
        setMapRoute('✈ LAX route evaluated');
      }
    },
    
    // t=3s — Procurement
    {
      t: 3000,
      fn: () => {
        updateAgent('pro', { status: 'QUERYING', statusClass: 'working', tool: '🏭 query_suppliers("dallas")', pulsing: true });
        
        addMessage({
          from: 'PROCUREMENT',
          to: '→ ORCH',
          time: '00:31',
          className: 'ap',
          body: 'Option B: Spot buy Dallas — $380K / 12h / Med risk. Only 80% quantity available. Cert: 4h.',
          tools: ['🏭 query_suppliers("dallas")']
        });
      }
    },
    
    // t=5s — Finance challenges
    {
      t: 5000,
      fn: () => {
        updateAgent('fin', { status: 'CALCULATING', statusClass: 'working', tool: '📊 run_monte_carlo(100)', pulsing: true });
        
        addMessage({
          from: 'FINANCE',
          to: '→ LOGISTICS',
          time: '01:04',
          className: 'af',
          body: 'Your $450K — does that include expedited customs at LAX during strike conditions? Challenging that assumption.',
          tools: ['📊 run_monte_carlo(100)', '💰 query_customs_rates()']
        });
      }
    },
    
    // t=7s — Logistics revises
    {
      t: 7000,
      fn: () => {
        updateAgent('log', { status: 'REVISING', statusClass: 'working', tool: '📦 recalculate_route()', confidence: 58, pulsing: true });
        
        addMessage({
          from: 'LOGISTICS',
          to: '→ FINANCE',
          time: '01:18',
          className: 'al',
          body: 'Confirmed. Customs +$50K. Total air: $500K — at budget limit. Recommend Hybrid 60/40: $280K / 36h instead.',
          tools: null
        });
      }
    },
    
    // t=9s — Finance confidence rises
    {
      t: 9000,
      fn: () => {
        updateAgent('fin', { status: 'CONSENSUS', statusClass: 'done', tool: '✅ propose_consensus()', confidence: 94, pulsing: false });
        updateAgent('log', { status: 'CONSENSUS', statusClass: 'done', tool: '✅ hybrid_confirmed()', confidence: 88, pulsing: false });
      }
    },
    
    // t=10s — Sales negotiates
    {
      t: 10000,
      fn: () => {
        updateAgent('sal', { status: 'NEGOTIATING', statusClass: 'working', tool: '📋 query_contract_terms()', pulsing: true });
        
        addMessage({
          from: 'SALES',
          to: '→ ALL',
          time: '02:18',
          className: 'as_',
          body: 'Apple accepts 36h delay + Q3 priority allocation. Zero financial penalty confirmed. Hybrid timeline fits perfectly.',
          tools: ['📋 query_contract_terms()', '📝 draft_sla_amendment()']
        });
        
        updateAgent('sal', { status: 'CONFIRMED', statusClass: 'done', tool: '✅ sla_confirmed()', confidence: 97, pulsing: false });
      }
    },
    
    // t=12.5s — Risk Agent fires challenge
    {
      t: 12500,
      fn: () => {
        showRiskAgent('LAX ground crew unconfirmed during active strike. Single point of failure in Hybrid plan. Recommend Hour-20 backup trigger to Tucson air route.');
        
        addMessage({
          from: 'RISK AGENT',
          to: '→ ALL ⚠',
          time: '03:45',
          className: 'ar',
          body: '⚠ Consensus challenge: LAX ground crew unconfirmed. Single point of failure. Recommend Hour-20 backup trigger to Tucson route.',
          tools: null
        });
        
        setMapStatus('RISK FLAGGED');
      }
    },
    
    // t=14.5s — Finance absorbs risk, proposes final
    {
      t: 14500,
      fn: () => {
        updateAgent('fin', { status: 'FINALISING', statusClass: 'working', tool: '✅ propose_consensus()', pulsing: true });
        
        addMessage({
          from: 'FINANCE',
          to: '→ ALL',
          time: '04:01',
          className: 'af',
          body: 'Risk acknowledged. Adding +$20K contingency for Tucson backup. Final recommendation: Hybrid $280K + $20K reserve. 94% CI. Proposing approval.',
          tools: ['✅ propose_consensus()']
        });
        
        updateAgent('pro', { status: 'DONE', statusClass: 'done', tool: '✅ acknowledged()', confidence: 71, pulsing: false });
      }
    },
    
    // t=16s — Show approval panel
    {
      t: 16000,
      fn: () => {
        setPhase(2, 'done');
        setPhase(3, 'active');
        showApproval();
        setMapStatus('AWAITING APPROVAL');
        setResolutionTime('4m 32s');
        setCostSaved('$220K');
      }
    }
  ];

  const startScenario = () => {
    if (scenarioRunning) return;
    
    setScenarioRunning(true);
    resetScenario();
    clearMessages();
    
    // Start cost accumulator
    const { startCostAccumulator } = useAppStore.getState();
    startCostAccumulator();
    
    // Clear existing timers
    timersRef.current.forEach(timer => clearTimeout(timer));
    timersRef.current = [];
    
    // Set up new timers
    scenarioSteps.forEach(step => {
      const timer = setTimeout(step.fn, step.t);
      timersRef.current.push(timer);
    });
  };

  const stopScenario = () => {
    timersRef.current.forEach(timer => clearTimeout(timer));
    timersRef.current = [];
    setScenarioRunning(false);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      timersRef.current.forEach(timer => clearTimeout(timer));
    };
  }, []);

  return {
    startScenario,
    stopScenario,
    scenarioRunning
  };
};
