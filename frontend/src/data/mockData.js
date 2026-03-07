// Mock data extracted from the HTML file
export const scenarios = {
  port_strike: {
    id: 'port_strike',
    title: '$12M semiconductor shipment',
    crisis: 'blocked · Port of Long Beach · Risk: $2M penalty + $50M Apple contract',
    severity: 'CRITICAL',
    costAccumulation: 1388, // per minute
    traditionalTime: '72:00:00',
    aiTime: '00:04:32'
  },
  customs_delay: {
    id: 'customs_delay',
    title: '$8M component shipment',
    crisis: 'held · Customs — Shanghai → LAX · Risk: $1.5M penalty + production halt',
    severity: 'HIGH',
    costAccumulation: 1200,
    traditionalTime: '48:00:00',
    aiTime: '00:03:15'
  },
  supplier_breach: {
    id: 'supplier_breach',
    title: '$20M Taiwan fab order',
    crisis: 'cancelled · Supplier bankruptcy · Risk: $5M replacement cost + 90-day delay',
    severity: 'CRITICAL',
    costAccumulation: 2100,
    traditionalTime: '168:00:00',
    aiTime: '00:06:45'
  }
};

export const agents = [
  {
    id: 'log',
    name: 'LOGISTICS',
    color: 'blue',
    colorClass: 'al',
    status: 'STANDBY',
    confidence: 0,
    tool: 'idle',
    pulsing: false
  },
  {
    id: 'fin',
    name: 'FINANCE',
    color: 'green',
    colorClass: 'af',
    status: 'STANDBY',
    confidence: 0,
    tool: 'idle',
    pulsing: false
  },
  {
    id: 'pro',
    name: 'PROCUREMENT',
    color: 'orange',
    colorClass: 'ap',
    status: 'STANDBY',
    confidence: 0,
    tool: 'idle',
    pulsing: false
  },
  {
    id: 'sal',
    name: 'SALES',
    color: 'purple',
    colorClass: 'as_',
    status: 'STANDBY',
    confidence: 0,
    tool: 'idle',
    pulsing: false
  }
];

export const mapNodes = {
  shanghai: { x: 0.78, y: 0.27, label: 'Shanghai', icon: '📦', color: '#7aa0be' },
  longbeach: { x: 0.20, y: 0.46, label: 'Long Beach', icon: '🔴', color: '#ff3b5c' },
  lax: { x: 0.19, y: 0.49, label: 'LAX', icon: '✈', color: '#00d4ff' },
  dallas: { x: 0.29, y: 0.50, label: 'Dallas', icon: '🏢', color: '#ffb340' },
  austin: { x: 0.31, y: 0.53, label: 'Austin TX', icon: '🏭', color: '#00e676' }
};

export const mapRoutes = [
  { a: 'shanghai', b: 'longbeach', state: 'blocked', dash: [6, 4] },
  { a: 'longbeach', b: 'lax', state: 'active', dash: [6, 4] },
  { a: 'lax', b: 'austin', state: 'active', dash: [6, 4] },
  { a: 'longbeach', b: 'dallas', state: 'proposed', dash: [4, 7] },
  { a: 'dallas', b: 'austin', state: 'proposed', dash: [4, 7] }
];

export const landMasses = [
  // North America
  [[0.06, 0.12], [0.22, 0.10], [0.32, 0.15], [0.34, 0.22], [0.28, 0.30], [0.21, 0.38], [0.18, 0.45], [0.14, 0.56], [0.10, 0.62], [0.06, 0.60], [0.03, 0.50], [0.03, 0.34], [0.06, 0.22]],
  // Central/South America
  [[0.18, 0.55], [0.24, 0.52], [0.26, 0.60], [0.24, 0.72], [0.20, 0.78], [0.16, 0.76], [0.15, 0.67], [0.17, 0.58]],
  // Europe
  [[0.46, 0.12], [0.54, 0.10], [0.57, 0.16], [0.56, 0.21], [0.51, 0.23], [0.47, 0.21], [0.45, 0.15]],
  // Africa
  [[0.46, 0.22], [0.55, 0.20], [0.58, 0.28], [0.57, 0.42], [0.53, 0.52], [0.49, 0.53], [0.46, 0.48], [0.45, 0.34]],
  // Asia
  [[0.54, 0.09], [0.74, 0.08], [0.84, 0.14], [0.86, 0.22], [0.82, 0.29], [0.74, 0.31], [0.65, 0.30], [0.58, 0.26], [0.54, 0.19]],
  // Australia
  [[0.74, 0.51], [0.83, 0.50], [0.86, 0.58], [0.84, 0.65], [0.78, 0.66], [0.73, 0.60], [0.72, 0.54]]
];

export const phases = [
  { id: 0, label: 'Crisis Detected', status: 'active' },
  { id: 1, label: 'Agents Active', status: 'pending' },
  { id: 2, label: 'Negotiating', status: 'pending' },
  { id: 3, label: 'Approved', status: 'pending' },
  { id: 4, label: 'Executing', status: 'pending' }
];

export const decisionMatrix = [
  {
    option: 'Air Freight',
    cost: '$500K',
    time: '24h',
    risk: { level: 2, max: 10 },
    esg: '🔴',
    customer: 'None',
    recommended: false,
    costColor: 'text-red-500'
  },
  {
    option: 'Spot Buy',
    cost: '$380K',
    time: '12h',
    risk: { level: 7, max: 10 },
    esg: '🟡',
    customer: '20% short',
    recommended: false,
    costColor: 'text-orange-500'
  },
  {
    option: 'Hybrid',
    cost: '$280K',
    time: '36h',
    risk: { level: 4, max: 10 },
    esg: '🟡',
    customer: 'Minor',
    recommended: true,
    costColor: 'text-green-500'
  }
];

export const monteCarloData = [
  { x: 240, y: 3 }, { x: 245, y: 6 }, { x: 250, y: 10 }, { x: 255, y: 16 },
  { x: 260, y: 26 }, { x: 265, y: 36 }, { x: 270, y: 50 }, { x: 275, y: 65 },
  { x: 280, y: 77 }, { x: 285, y: 87 }, { x: 290, y: 92 }, { x: 295, y: 87 },
  { x: 300, y: 80 }, { x: 305, y: 70 }, { x: 310, y: 58 }, { x: 315, y: 45 },
  { x: 320, y: 33 }, { x: 325, y: 24 }, { x: 330, y: 16 }, { x: 335, y: 10 },
  { x: 340, y: 6 }, { x: 345, y: 3 }
];

export const traditionalEmails = [
  {
    from: 'logistics@company.com',
    time: 'Day 1, 09:14',
    subject: 'RE: Port Strike — Long Beach',
    body: 'ILWU striking at LB. SC-8891 stuck at port. Need Finance and Procurement on a call ASAP.',
    delay: 0.3
  },
  {
    from: 'finance@company.com',
    time: 'Day 1, 11:42',
    subject: 'RE: Port Strike',
    body: 'In back-to-back until 3pm. Bridge call tomorrow? I\'ll need full cost breakdown before approving anything over $200K.',
    delay: 1.8
  },
  {
    from: 'procurement@company.com',
    time: 'Day 1, 16:05',
    subject: 'RE: Vendor alternatives?',
    body: 'Dallas distributor — 80% quantity only. Cert takes 4-6h. Checking Tucson. Will update in the morning.',
    delay: 3.5
  },
  {
    from: 'sales@company.com',
    time: 'Day 2, 09:30',
    subject: 'URGENT: Apple deadline',
    body: 'Apple offering 36h extension if we guarantee Q3 priority. Need Legal review before I can commit.',
    delay: 5.2
  },
  {
    from: 'vp-ops@company.com',
    time: 'Day 2, 14:00',
    subject: 'RE: Bridge call — no decision',
    body: '45min call, Finance needs more data. Tucson quote still pending. Deferred again.',
    delay: 7
  }
];

export const aiMessages = [
  {
    from: '🔵 Logistics Agent',
    time: '00:12',
    subject: '3 route options generated',
    body: 'Air LAX $450K/24h · Hybrid 60/40 $253K/36h. Recalled Mar 2024 LA strike playbook — hybrid saved $180K.',
    className: 'al',
    tools: ['📦 check_freight_rates()', '📚 memory_recall("LA_2024")'],
    delay: 0.3
  },
  {
    from: '🟢 Finance Agent',
    time: '01:04',
    subject: 'Monte Carlo: Hybrid optimal (94% CI, 100 iterations)',
    body: 'Challenged customs assumption. Air revised $450K→$500K. Hybrid saves $220K.',
    className: 'af',
    tools: ['📊 run_monte_carlo(100)', '💰 query_customs_rates()'],
    delay: 1.8
  },
  {
    from: '🟣 Sales Agent',
    time: '02:18',
    subject: 'Apple: 36h extension confirmed, zero penalty',
    body: 'Contract reviewed. Q3 priority allocation accepted. Hybrid timeline fits.',
    className: 'as_',
    tools: ['📋 query_contract_terms()', '📝 draft_sla_amendment()'],
    delay: 3.5
  },
  {
    from: '🔴 Risk Agent',
    time: '03:45',
    subject: '⚠ Single point of failure flagged',
    body: 'LAX ground crew unconfirmed during strike. Hour-20 backup trigger added. +$20K contingency.',
    className: 'ar',
    tools: ['⚠ risk_analysis()', '🔧 backup_planning()'],
    delay: 5.2
  }
];

export const auditTrail = [
  {
    id: 1,
    time: '00:00 — Crisis Detected',
    agent: '🔴 System Monitor',
    agentColor: 'text-red-500',
    dotColor: '#ff3b5c',
    description: 'Strike detected. SC-2024-8891 BLOCKED at Long Beach. P0 broadcast to all agents.',
    data: 'penalty_risk: $2M · deadline: 48h · contract: Apple',
    delay: 0.1
  },
  {
    id: 2,
    time: '00:12 — Route Options',
    agent: '🔵 Logistics Agent',
    agentColor: 'text-blue-500',
    dotColor: '#00d4ff',
    description: '3 options generated. Memory recalled March 2024 LA port strike — hybrid saved $180K.',
    data: 'check_freight_rates() · memory_recall("LA_strike_2024")',
    memory: '📚 Historical: LA Strike Mar 2024 — hybrid saved $180K',
    delay: 0.3
  },
  {
    id: 3,
    time: '01:04 — Monte Carlo',
    agent: '🟢 Finance Agent',
    agentColor: 'text-green-500',
    dotColor: '#00e676',
    description: '100-iteration simulation run. Challenged customs assumption — Air revised $450K → $500K.',
    data: 'run_monte_carlo(100) · query_customs_rates()',
    delay: 0.5
  },
  {
    id: 4,
    time: '02:18 — SLA Confirmed',
    agent: '🟣 Sales Agent',
    agentColor: 'text-purple-500',
    dotColor: '#9b5de5',
    description: 'Apple 36h extension negotiated. Reputational risk only — zero financial penalty.',
    data: 'query_contract_terms() · draft_sla_amendment()',
    delay: 0.7
  },
  {
    id: 5,
    time: '03:45 — Risk Flagged',
    agent: '🔴 Risk Agent (Devil\'s Advocate)',
    agentColor: 'text-red-500',
    dotColor: '#ff3b5c',
    description: 'LAX ground crew unconfirmed during strike. Single point of failure. Hour-20 backup trigger added. Finance +$20K reserve.',
    data: 'risk: operational · severity: medium · mitigation: tucson_backup_H20',
    delay: 0.9
  },
  {
    id: 6,
    time: '04:32 — Approved & Executed',
    agent: '✅ VP Operations',
    agentColor: 'text-green-500',
    dotColor: '#00e676',
    description: 'Hybrid route approved. Cascade: freight booked, Apple notified, budget released, spot order cancelled.',
    data: 'option: hybrid · cost: $280K · savings: $220K · CI: 94%',
    delay: 1.1
  }
];
