export const SCENARIOS = {
  port_strike: {
    title: '$12M semiconductor shipment',
    crisis: 'blocked · Port of Long Beach · Risk: $2M penalty + $50M Apple contract',
    // Nav pills
    caseId:  'SC-2024-8891',
    window:  '48h WINDOW',
    // Map bar
    origin:  '📦 Shanghai Port',
    blockedAt: '🔴 Long Beach',
    // Crisis banner sub-text
    traditional: '~$149K/72h',
    tradTime: '~72 hrs',
    // SplitTab — traditional side
    trad: {
      emails: [
        { from:'ops.manager@company.com',      time:'Day 1, 09:14', subj:'RE: Port Strike — Long Beach',   body:'ILWU striking at LB. SC-8891 stuck at port. Need Finance and Procurement on a call ASAP.' },
        { from:'finance.vp@company.com',        time:'Day 1, 11:42', subj:'RE: Port Strike',                body:"In back-to-back until 3pm. Bridge call tomorrow? I'll need full cost breakdown before approving anything over $200K." },
        { from:'procurement.lead@company.com',  time:'Day 1, 16:05', subj:'RE: Vendor alternatives?',      body:'Dallas distributor — 80% quantity only. Cert takes 4-6h. Checking Tucson. Will update in the morning.' },
        { from:'sales.director@company.com',    time:'Day 2, 09:30', subj:'URGENT: Apple deadline',        body:'Apple offering 36h extension if we guarantee Q3 priority. Need Legal review before I can commit.' },
        { from:'ops.manager@company.com',       time:'Day 2, 14:00', subj:'RE: Bridge call — no decision', body:'45min call, Finance needs more data. Tucson quote still pending. Deferred again.' },
      ],
      penalty: '⏱ 72 HOURS — $2M PENALTY TRIGGERED',
    },
    // SplitTab — AI side (static summary cards; live feed below)
    ai: {
      resolution: '4m 32s',
      summary: 'RESOLVED IN 4m 32s — Hybrid Route · $280K · saved $220K',
    },
  },

  customs_delay: {
    title: '$8M component shipment',
    crisis: 'held · Customs — Shanghai → LAX · Risk: $1.5M penalty + production halt',
    caseId:  'CD-2024-3341',
    window:  '36h WINDOW',
    origin:  '📦 Shanghai Port',
    blockedAt: '🟡 Shanghai Customs Hold',
    traditional: '~$120K/72h',
    tradTime: '~72 hrs',
    trad: {
      emails: [
        { from:'logistics.ops@company.com',    time:'Day 1, 07:30', subj:'RE: Customs Hold — Shanghai LAX', body:'CBP flagged shipment for additional inspection. No ETA on release. Production line at risk.' },
        { from:'compliance.officer@company.com',time:'Day 1, 10:15', subj:'RE: HS Code dispute',           body:'Customs contesting HS code 8542.31. Broker says 3-5 day appeal process. Penalty clock started.' },
        { from:'finance.vp@company.com',        time:'Day 1, 14:00', subj:'RE: Cost exposure?',            body:"I need numbers before EOD. What's the broker saying about expedited clearance fees?" },
        { from:'ops.manager@company.com',       time:'Day 2, 08:45', subj:'RE: Alternative sourcing?',     body:'Checked Mexico plant — 60% capacity only. Taiwan fab 10-day lead time. Neither solves this week.' },
        { from:'sales.director@company.com',    time:'Day 2, 15:30', subj:'URGENT: Client escalating',     body:'Samsung calling every 2 hours. If we miss delivery they source from competitor permanently.' },
      ],
      penalty: '⏱ 72 HOURS — $1.5M PENALTY + CLIENT LOST',
    },
    ai: {
      resolution: '3m 18s',
      summary: 'RESOLVED IN 3m 18s — Expedited Clearance · $180K · saved $140K',
    },
  },

  supplier_breach: {
    title: '$20M Taiwan fab order',
    crisis: 'cancelled · Supplier bankruptcy · Risk: $5M replacement cost + 90-day delay',
    caseId:  'SB-2024-7712',
    window:  '72h WINDOW',
    origin:  '🏭 ChipTech Taiwan',
    blockedAt: '🔴 ChipTech Bankrupt',
    traditional: '~$280K/90d',
    tradTime: '~90 days',
    trad: {
      emails: [
        { from:'procurement.lead@company.com',  time:'Day 1, 06:00', subj:'URGENT: ChipTech filing Chapter 11', body:'Our primary fab just filed for bankruptcy. $20M order in limbo. Production halt in 8 days.' },
        { from:'legal.counsel@company.com',     time:'Day 1, 09:30', subj:'RE: Contract exposure',              body:'Force majeure clause applies but recovery timeline is 60-90 days through courts. No fast path.' },
        { from:'finance.vp@company.com',        time:'Day 1, 13:00', subj:'RE: Replacement cost',               body:'TSMC alternative is $5M premium + 10-week lead time. Board approval needed above $2M. Call Thursday.' },
        { from:'ops.manager@company.com',       time:'Day 2, 10:00', subj:'RE: Partial inventory?',             body:'Found 40% stock in Singapore warehouse — buys us 3 weeks. Not enough for Q3 commitments.' },
        { from:'sales.director@company.com',    time:'Day 2, 16:00', subj:'RE: NVIDIA contract at risk',        body:'NVIDIA wants written commitment by Friday or they qualify alternate vendor. We cannot lose this.' },
      ],
      penalty: '⏱ 90 DAYS — $5M COST + NVIDIA CONTRACT LOST',
    },
    ai: {
      resolution: '6m 14s',
      summary: 'RESOLVED IN 6m 14s — Multi-Source Strategy · $2.8M · saved $2.2M',
    },
  },
}
