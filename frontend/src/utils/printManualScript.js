export const MANUAL_SCRIPT = `
RESOLVEIQ — MANUAL MODE SCRIPT (Print this for demo day)
=========================================================
If live backend fails, click "📜 Manual Mode Script" → reads aloud this script.

STEP 1 (0:00) — Click "▶ Start Scenario"
  → 4 agent cards light up with ACTIVATING status
  → Orchestrator message: "Crisis P0: SC-2024-8891 blocked..."

STEP 2 (0:12) — Logistics speaks
  → Memory badge 📚 appears on message
  → Say: "The agent remembered a similar crisis from 14 months ago"
  → Map updates: LAX route evaluated

STEP 3 (0:31) — Procurement queries Dallas
  → Agent card shows query_suppliers tool

STEP 4 (1:04) — Finance CHALLENGES logistics
  → This is A2A negotiation — agents talking to each other
  → Monte Carlo runs: 100 iterations in seconds

STEP 5 (1:18) — Logistics REVISES its estimate
  → Air $450K → $500K after customs correction
  → Recommends Hybrid route $280K

STEP 6 (2:18) — Sales confirms Apple extension
  → Zero financial penalty

STEP 7 (3:45) — ⚠ RISK AGENT FIRES (key moment, pause here)
  → "Consensus challenge: LAX ground crew unconfirmed"
  → Say: "This is impossible with traditional software — genuine AI reasoning"
  → Finance adds $20K contingency

STEP 8 (4:32) — APPROVE panel appears
  → $280K + $20K reserve, 94% confidence
  → HAND LAPTOP TO JUDGE: "Would you like to approve?"

STEP 9 — Post-approval
  → Execution cascade: 4 confirmations in 3 seconds
  → Truck moves on map
  → Resolution: 4m 32s vs 72 hours traditional

STEP 10 — Decision Matrix tab
  → Show Monte Carlo chart
  → "What if your penalty was $4M?" — drag slider
  → ROI slider: "At your volume of shipments — here's annual savings"
=========================================================
`.trim()

export function showManualScript() {
  const w = window.open('', '_blank', 'width=640,height=720,scrollbars=yes')
  if (!w) {
    // Fallback if popups blocked
    alert(MANUAL_SCRIPT)
    return
  }
  w.document.write(`<!DOCTYPE html>
<html>
<head>
  <title>ResolveIQ — Manual Mode Script</title>
  <style>
    body {
      margin: 0;
      background: #06090f;
      color: #ddeeff;
      font-family: 'Courier New', monospace;
      font-size: 13px;
      line-height: 1.7;
      padding: 28px 32px;
    }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
    }
    h2 {
      color: #00d4ff;
      font-family: sans-serif;
      font-size: 14px;
      margin: 0 0 16px;
      letter-spacing: 1px;
    }
    .step { color: #ffb340; font-weight: bold; }
    .key  { color: #39d98a; }
    .warn { color: #ff3b5c; }
    @media print {
      body { background: white; color: black; }
      h2   { color: #0066cc; }
    }
  </style>
</head>
<body>
  <h2>⬡ RESOLVEIQ — MANUAL MODE SCRIPT</h2>
  <pre>${MANUAL_SCRIPT}</pre>
  <br/>
  <button onclick="window.print()" style="
    background:#00d4ff;border:none;border-radius:5px;
    color:#06090f;font-weight:700;padding:8px 18px;
    font-size:13px;cursor:pointer;margin-top:8px;">
    🖨 Print This
  </button>
</body>
</html>`)
  w.document.close()
}
