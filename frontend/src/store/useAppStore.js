import { create } from 'zustand';
import { agents as initialAgents, phases as initialPhases, scenarios } from '../data/mockData.js';

export const useAppStore = create((set, get) => ({
  // Current scenario
  currentScenario: 'port_strike',
  
  // Scenario running state
  scenarioRunning: false,
  scenarioTimers: [],
  
  // Agents state
  agents: initialAgents,
  agentCount: 0,
  riskAgent: {
    visible: false,
    message: 'Monitoring...'
  },
  
  // Messages & Chat
  messages: [],
  messageCount: 0,
  showApproval: false,
  
  // Phases
  phases: initialPhases,
  
  // Map state
  mapStatus: 'STANDBY',
  mapRoute: '— Awaiting agents',
  truckPhase: 'blocked', // blocked | flying | driving | arrived
  truckProgress: 0,
  
  // UI state
  activeTab: 'map',
  agentPanelCollapsed: false,
  demoDropdownOpen: false,
  
  // Metrics
  resolutionTime: '—',
  costSaved: '—',
  
  // What-if parameters
  whatIf: {
    penalty: 2000,
    deadline: 48,
    budget: 500
  },
  
  // ROI calculation
  shipmentsPerYear: 200,
  
  // Cost accumulator
  costAccumulated: 0,
  costStart: null,
  
  // Actions
  setCurrentScenario: (scenario) => set({ currentScenario: scenario }),
  
  setScenarioRunning: (running) => set({ scenarioRunning: running }),
  
  setActiveTab: (tab) => set({ activeTab: tab }),
  
  toggleAgentPanel: () => set((state) => ({ 
    agentPanelCollapsed: !state.agentPanelCollapsed 
  })),
  
  toggleDemoDropdown: () => set((state) => ({ 
    demoDropdownOpen: !state.demoDropdownOpen 
  })),
  
  closeDemoDropdown: () => set({ demoDropdownOpen: false }),
  
  setAgentCount: (count) => set({ agentCount: count }),
  
  updateAgent: (id, updates) => set((state) => ({
    agents: state.agents.map(agent => 
      agent.id === id ? { ...agent, ...updates } : agent
    )
  })),
  
  showRiskAgent: (message) => set({
    riskAgent: { visible: true, message }
  }),
  
  hideRiskAgent: () => set({
    riskAgent: { visible: false, message: 'Monitoring...' }
  }),
  
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, { ...message, id: Date.now() }],
    messageCount: state.messageCount + 1
  })),
  
  clearMessages: () => set({
    messages: [],
    messageCount: 0
  }),
  
  setPhase: (phaseId, status) => set((state) => ({
    phases: state.phases.map(phase =>
      phase.id === phaseId ? { ...phase, status } : phase
    )
  })),
  
  setMapStatus: (status) => set({ mapStatus: status }),
  
  setMapRoute: (route) => set({ mapRoute: route }),
  
  setTruckPhase: (phase, progress = 0) => set({ 
    truckPhase: phase, 
    truckProgress: progress 
  }),
  
  updateTruckProgress: (progress) => set({ truckProgress: progress }),
  
  showApproval: () => set({ showApproval: true }),
  
  hideApproval: () => set({ showApproval: false }),
  
  setResolutionTime: (time) => set({ resolutionTime: time }),
  
  setCostSaved: (cost) => set({ costSaved: cost }),
  
  updateWhatIf: (key, value) => set((state) => ({
    whatIf: { ...state.whatIf, [key]: value }
  })),
  
  setShipmentsPerYear: (count) => set({ shipmentsPerYear: count }),
  
  startCostAccumulator: () => {
    const scenario = scenarios[get().currentScenario];
    set({ 
      costStart: Date.now(),
      costAccumulated: 0
    });
  },
  
  updateCostAccumulator: () => {
    const state = get();
    if (!state.costStart) return;
    
    const scenario = scenarios[state.currentScenario];
    const minutes = (Date.now() - state.costStart) / 60000;
    const cost = Math.floor(minutes * scenario.costAccumulation);
    
    set({ costAccumulated: cost });
  },
  
  resetScenario: () => {
    // Clear any existing timers
    const state = get();
    state.scenarioTimers.forEach(timer => clearTimeout(timer));
    
    set({
      scenarioRunning: false,
      scenarioTimers: [],
      agents: initialAgents,
      agentCount: 0,
      riskAgent: { visible: false, message: 'Monitoring...' },
      messages: [],
      messageCount: 0,
      showApproval: false,
      phases: initialPhases.map((phase, index) => ({
        ...phase,
        status: index === 0 ? 'active' : 'pending'
      })),
      mapStatus: 'STANDBY',
      mapRoute: '— Awaiting agents',
      truckPhase: 'blocked',
      truckProgress: 0,
      resolutionTime: '—',
      costSaved: '—',
      costStart: null,
      costAccumulated: 0
    });
  }
}));
