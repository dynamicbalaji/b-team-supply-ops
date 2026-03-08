export const SCENARIOS = {
  port_strike: {
    title: '$12M semiconductor shipment',
    crisis: 'blocked · Port of Long Beach · Risk: $2M penalty + $50M Apple contract',
    // Nav pills
    caseId:  'SC-2024-8891',
    window:  '48h WINDOW',
    // Map bar
    origin:     '📦 Shanghai Port',
    blockedAt:  '🔴 Long Beach (ILWU Strike)',
    destination: '🏭 Apple — Cupertino, CA',
    // Crisis banner sub-text
    traditional: '~$149K/72h',
    tradTime: '72h',
    // SplitTab — traditional side
    trad: {
      emails: [
        { from:'ops.manager@company.com',      time:'Day 1, 09:14', subj:'RE: Port Strike — Long Beach',   body:'ILWU striking at Long Beach. SC-8891 stuck at port — $12M semiconductor shipment cannot unload. Need Finance and Procurement on a call ASAP. Apple deadline is 48h away.' },
        { from:'finance.vp@company.com',        time:'Day 1, 11:42', subj:'RE: Port Strike',                body:"In back-to-back until 3pm. Bridge call tomorrow? I'll need full cost breakdown before approving anything over $200K. Air freight quote from FedEx was $450K — that's already near our cap." },
        { from:'procurement.lead@company.com',  time:'Day 1, 16:05', subj:'RE: Vendor alternatives?',      body:'No local stock near LA. Checking if we can pull from the Texas Semiconductor Warehouse in Dallas — 80% quantity only. Cert takes 4-6h. Will update tomorrow morning.' },
        { from:'sales.director@company.com',    time:'Day 2, 09:30', subj:'URGENT: Apple deadline',        body:'Apple is offering a 36h extension if we guarantee Q3 priority allocation. Need Legal sign-off before I can commit anything in writing. Clock is ticking.' },
        { from:'ops.manager@company.com',       time:'Day 2, 14:00', subj:'RE: Bridge call — no decision', body:'45min call and still no decision. Finance wants more data on Oakland vs LAX. Tucson backup quote still pending. Deferred to tomorrow.' },
      ],
      penalty: '⏱ 72 HOURS — $2M PENALTY TRIGGERED',
    },
    // SplitTab — AI side (static summary cards; live feed below)
    ai: {
      resolution: '4m 32s',
      summary: 'RESOLVED IN 4m 32s — Hybrid Route · $280K · saved $220K · Apple: ✓',
    },
  },

  customs_delay: {
    title: '$8M component shipment',
    crisis: 'held · Shenzhen Customs · Risk: $1.5M penalty + Samsung production halt',
    caseId:  'CD-2024-3341',
    window:  '36h WINDOW',
    origin:     '📦 Shenzhen, China',
    blockedAt:  '🟡 Shenzhen Customs Hold',
    destination: '🏭 Samsung — Dallas, TX',
    traditional: '~$120K/72h',
    tradTime: '72h',
    trad: {
      emails: [
        { from:'logistics.ops@company.com',    time:'Day 1, 07:30', subj:'RE: Customs Hold — Shenzhen', body:'GACC flagged shipment for additional inspection at Shenzhen. No ETA on release. HS code 8542.31 under dispute. Samsung production line in Dallas at risk in 36h.' },
        { from:'compliance.officer@company.com',time:'Day 1, 10:15', subj:'RE: HS Code dispute',        body:'Customs contesting HS code classification. Broker says 3-5 day appeal process minimum. Penalty clock started. We may need to reroute entirely.' },
        { from:'finance.vp@company.com',        time:'Day 1, 14:00', subj:'RE: Cost exposure?',         body:"I need numbers before EOD. What's the broker fee for expedited clearance? And what does rerouting via Busan add to cost vs time?" },
        { from:'ops.manager@company.com',       time:'Day 2, 08:45', subj:'RE: Alternative sourcing?',  body:'Checked Korean backup supplier — 8-day lead time. Not viable this week. Busan port reroute looks like the best option but we need a freight broker fast.' },
        { from:'sales.director@company.com',    time:'Day 2, 15:30', subj:'URGENT: Samsung escalating', body:'Samsung Dallas is calling every 2 hours. If we miss the delivery window they will source from a competitor and we lose the contract permanently.' },
      ],
      penalty: '⏱ 72 HOURS — $1.5M PENALTY + SAMSUNG CONTRACT LOST',
    },
    ai: {
      resolution: '3m 18s',
      summary: 'RESOLVED IN 3m 18s — Expedited Air via Busan · $180K · saved $140K · Samsung: ✓',
    },
  },

  supplier_breach: {
    title: '$20M Taiwan fab order',
    crisis: 'cancelled · Supplier bankruptcy · Risk: $5M replacement cost + 90-day delay',
    caseId:  'SB-2024-7712',
    window:  '72h WINDOW',
    origin:     '🏭 Hsinchu Fab, Taiwan',
    blockedAt:  '🔴 ChipTech — Bankrupt',
    destination: '🏭 NVIDIA — Santa Clara, CA',
    traditional: '~$280K/90d',
    tradTime: '90d',
    trad: {
      emails: [
        { from:'procurement.lead@company.com',  time:'Day 1, 06:00', subj:'URGENT: ChipTech filing Chapter 11', body:'Our primary fab in Hsinchu just filed for Chapter 11 bankruptcy. Our $20M order for NVIDIA is in limbo. Production halt in 8 days if we cannot find a replacement.' },
        { from:'legal.counsel@company.com',     time:'Day 1, 09:30', subj:'RE: Contract exposure',              body:'Force majeure clause applies but asset recovery through Taiwanese courts is 60-90 days minimum. No fast path. We need a substitute supplier immediately.' },
        { from:'finance.vp@company.com',        time:'Day 1, 13:00', subj:'RE: Replacement cost',               body:'SK Hynix in Korea can supply equivalent spec but at a $5M premium with 10-week lead time. Board approval needed for anything above $2M. Call Thursday.' },
        { from:'ops.manager@company.com',       time:'Day 2, 10:00', subj:'RE: Partial inventory?',             body:'Found 40% of required stock in Singapore warehouse — buys us about 3 weeks. Not enough to fulfill Q3 NVIDIA commitments on its own.' },
        { from:'sales.director@company.com',    time:'Day 2, 16:00', subj:'RE: NVIDIA contract at risk',        body:'NVIDIA wants a written commitment by Friday or they qualify an alternate vendor. We absolutely cannot lose this account. Need a decision NOW.' },
      ],
      penalty: '⏱ 90 DAYS — $5M COST + NVIDIA CONTRACT LOST',
    },
    ai: {
      resolution: '6m 14s',
      summary: 'RESOLVED IN 6m 14s — SK Hynix Alt-Source · $510K · NVIDIA spec certified · saved $4.49M',
    },
  },
}
