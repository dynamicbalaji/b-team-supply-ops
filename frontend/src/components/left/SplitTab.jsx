export default function SplitTab() {
  return (
    <div className="split">
      {/* Traditional process — left */}
      <div className="sp trad">
        <div className="sp-hd">
          <div className="sp-title" style={{ color: '#ff3b5c' }}>📧 Traditional Process</div>
          <div className="sp-time slow">72:00:00</div>
        </div>

        <div className="eml">
          <div className="er">
            <span className="efrom">ops.manager@company.com</span>
            <span className="etime">Day 1, 09:14</span>
          </div>
          <div className="esubj">RE: Port Strike — Long Beach</div>
          <div className="ebody">ILWU striking at LB. SC-8891 stuck at port. Need Finance and Procurement on a call ASAP.</div>
        </div>

        <div className="eml">
          <div className="er">
            <span className="efrom">finance.vp@company.com</span>
            <span className="etime">Day 1, 11:42</span>
          </div>
          <div className="esubj">RE: Port Strike</div>
          <div className="ebody">In back-to-back until 3pm. Bridge call tomorrow? I'll need full cost breakdown before approving anything over $200K.</div>
        </div>

        <div className="eml">
          <div className="er">
            <span className="efrom">procurement.lead@company.com</span>
            <span className="etime">Day 1, 16:05</span>
          </div>
          <div className="esubj">RE: Vendor alternatives?</div>
          <div className="ebody">Dallas distributor — 80% quantity only. Cert takes 4-6h. Checking Tucson. Will update in the morning.</div>
        </div>

        <div className="eml">
          <div className="er">
            <span className="efrom">sales.director@company.com</span>
            <span className="etime">Day 2, 09:30</span>
          </div>
          <div className="esubj">URGENT: Apple deadline</div>
          <div className="ebody">Apple offering 36h extension if we guarantee Q3 priority. Need Legal review before I can commit.</div>
        </div>

        <div className="eml">
          <div className="er">
            <span className="efrom">ops.manager@company.com</span>
            <span className="etime">Day 2, 14:00</span>
          </div>
          <div className="esubj">RE: Bridge call — no decision</div>
          <div className="ebody">45min call, Finance needs more data. Tucson quote still pending. Deferred again.</div>
        </div>

        <div className="ebar">⏱ 72 HOURS — $2M PENALTY TRIGGERED</div>
      </div>

      {/* ChainGuard AI — right */}
      <div className="sp ai">
        <div className="sp-hd">
          <div className="sp-title" style={{ color: '#00e676' }}>🤖 ChainGuard AI</div>
          <div className="sp-time fast">04:32</div>
        </div>

        <div className="ai-bar">✅ RESOLVED IN 4m 32s — Hybrid Route · $280K · saved $220K</div>

        <div className="eml" style={{ background: 'rgba(0,212,255,.04)', borderColor: 'rgba(0,212,255,.18)' }}>
          <div className="er">
            <span className="efrom" style={{ color: '#00d4ff' }}>🔵 Logistics Agent</span>
            <span className="etime">00:12</span>
          </div>
          <div className="esubj" style={{ color: '#ddeeff' }}>3 route options generated</div>
          <div className="ebody" style={{ color: '#7aa0be' }}>Air LAX $450K/24h · Hybrid 60/40 $253K/36h. Recalled Mar 2024 LA strike playbook — hybrid saved $180K.</div>
        </div>

        <div className="eml" style={{ background: 'rgba(0,230,118,.04)', borderColor: 'rgba(0,230,118,.18)' }}>
          <div className="er">
            <span className="efrom" style={{ color: '#00e676' }}>🟢 Finance Agent</span>
            <span className="etime">01:04</span>
          </div>
          <div className="esubj" style={{ color: '#ddeeff' }}>Monte Carlo: Hybrid optimal (94% CI, 100 iterations)</div>
          <div className="ebody" style={{ color: '#7aa0be' }}>Challenged customs assumption. Air revised $450K→$500K. Hybrid saves $220K.</div>
        </div>

        <div className="eml" style={{ background: 'rgba(155,93,229,.04)', borderColor: 'rgba(155,93,229,.18)' }}>
          <div className="er">
            <span className="efrom" style={{ color: '#9b5de5' }}>🟣 Sales Agent</span>
            <span className="etime">02:18</span>
          </div>
          <div className="esubj" style={{ color: '#ddeeff' }}>Apple: 36h extension confirmed, zero penalty</div>
          <div className="ebody" style={{ color: '#7aa0be' }}>Contract reviewed. Q3 priority allocation accepted. Hybrid timeline fits.</div>
        </div>

        <div className="eml" style={{ background: 'rgba(255,59,92,.04)', borderColor: 'rgba(255,59,92,.18)' }}>
          <div className="er">
            <span className="efrom" style={{ color: '#ff3b5c' }}>🔴 Risk Agent</span>
            <span className="etime">03:45</span>
          </div>
          <div className="esubj" style={{ color: '#ddeeff' }}>⚠ Single point of failure flagged</div>
          <div className="ebody" style={{ color: '#7aa0be' }}>LAX ground crew unconfirmed during strike. Hour-20 backup trigger added. +$20K contingency.</div>
        </div>
      </div>
    </div>
  )
}
