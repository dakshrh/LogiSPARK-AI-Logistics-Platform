import io
import json
import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from predictor import ShipmentPredictor
from report_generator import generate_pdf_report

app = FastAPI(title="LogiSPARK Enterprise Decision Support")
predictor = ShipmentPredictor()

# ──────────────────────────────────────────────────────────────────────────────
# API ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check(): return {"status": "running"}

@app.get("/api/shipments")
def get_shipments(): return predictor.get_all_shipments()

@app.get("/api/stats")
def get_global_stats(): return predictor.get_summary_stats()

@app.get("/predict/{shipment_id}")
def predict_shipment(shipment_id: str):
    try: return predictor.predict(shipment_id)
    except KeyError as e: raise HTTPException(status_code=404, detail=str(e))
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/predict/{shipment_id}/json")
def export_json(shipment_id: str): return predictor.predict(shipment_id)

@app.get("/predict/{shipment_id}/excel")
def export_excel(shipment_id: str):
    res = predictor.predict(shipment_id)
    flat = {
        "Shipment ID": res["shipment_id"], "Origin": res["origin"],
        "Destination": res["destination"], "Mode": res["mode"],
        "Customer Tier": res["customer_tier"],
        "Delay Probability (%)": res["delay_probability"],
        "Urgency": res["urgency"], "Root Cause": res["root_cause"],
        "Predicted Delay (hrs)": res["predicted_delay_hours"],
        "Total Loss (INR)": res["financial_breakdown"]["total_loss"],
        "Recommended Action": res["recommendation_v2"]["recommended_action"],
        "Potential Savings (INR)": res["recommendation_v2"]["potential_savings"],
        "Net Benefit (INR)": res["recommendation_v2"]["net_benefit"],
        "ROI (%)": res["recommendation_v2"]["roi"],
        "Priority": res["priority_matrix"]["priority"],
        "Action Deadline": res["priority_matrix"]["action_deadline"],
    }
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([flat]).to_excel(writer, index=False)
    output.seek(0)
    headers = {"Content-Disposition": f'attachment; filename="Delay_Report_{shipment_id}.xlsx"'}
    return StreamingResponse(output, headers=headers,
                             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.get("/predict/{shipment_id}/pdf")
def export_pdf(shipment_id: str):
    res = predictor.predict(shipment_id)
    out_path = f"Delay_Report_{shipment_id}.pdf"
    generate_pdf_report(res, out_path)
    return FileResponse(out_path, filename=out_path, media_type="application/pdf")


# ──────────────────────────────────────────────────────────────────────────────
# DASHBOARD HTML
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    return r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LogiSPARK – Enterprise Decision Support</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root{
  --navy:#0f172a;--blue:#1e3a8a;--accent:#3b82f6;--sky:#eff6ff;
  --bg:#f1f5f9;--card:#fff;--border:#e2e8f0;
  --muted:#64748b;--dark:#0f172a;
  --green:#10b981;--amber:#f59e0b;--red:#ef4444;--purple:#8b5cf6;
  --sh:0 1px 3px rgba(0,0,0,.08),0 1px 2px rgba(0,0,0,.04);
  --sh-lg:0 10px 25px rgba(0,0,0,.08);
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--dark);min-height:100vh}

/* NAV */
nav{background:var(--navy);color:#fff;display:flex;align-items:center;justify-content:space-between;
    padding:0 24px;height:54px;position:sticky;top:0;z-index:200;box-shadow:0 2px 12px rgba(0,0,0,.25)}
.nav-logo{display:flex;align-items:center;gap:10px}
.nav-logo .chip{background:var(--accent);padding:4px 10px;border-radius:6px;font-size:.75rem;font-weight:800;letter-spacing:1px}
.nav-logo span{font-size:1.1rem;font-weight:700}
.nav-right{display:flex;align-items:center;gap:12px;font-size:.8rem}
.pulse-dot{width:8px;height:8px;border-radius:50%;background:var(--green);animation:pulse 1.4s infinite}
@keyframes pulse{0%,100%{opacity:.5;transform:scale(.9)}50%{opacity:1;transform:scale(1.2)}}

/* LAYOUT */
.layout{display:grid;grid-template-columns:260px 1fr;gap:0;height:calc(100vh - 54px);overflow:hidden}
.sidebar{background:var(--navy);color:#fff;display:flex;flex-direction:column;overflow-y:auto;padding:16px;gap:12px}
.main{overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:16px}

/* SIDEBAR */
.s-label{font-size:.65rem;font-weight:700;letter-spacing:1px;color:#94a3b8;text-transform:uppercase;padding:4px 0}
.s-select{width:100%;padding:9px 10px;border-radius:6px;border:none;font-size:.8rem;font-weight:600;cursor:pointer;background:#fff;color:var(--navy)}
.kpi-card{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:8px;padding:12px}
.kpi-label{font-size:.65rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px}
.kpi-val{font-size:1.25rem;font-weight:800;margin-top:4px}

/* CARDS */
.card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px;box-shadow:var(--sh)}
.card-title{font-size:.7rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.7px;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--border)}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.grid-4{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.span-2{grid-column:span 2}
.span-3{grid-column:span 3}

/* EXEC SUMMARY */
.exec-banner{background:linear-gradient(135deg,#1e3a8a 0%,#1d4ed8 100%);color:#fff;border-radius:10px;padding:18px 22px;
             display:flex;align-items:flex-start;gap:14px;box-shadow:var(--sh-lg)}
.exec-icon{font-size:1.8rem;flex-shrink:0;margin-top:2px}
.exec-text{font-size:.95rem;line-height:1.65;font-weight:500}
.exec-text strong{font-weight:800}

/* BADGE */
.badge{display:inline-block;padding:3px 9px;border-radius:5px;font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px}
.b-red{background:#fee2e2;color:#dc2626}
.b-amber{background:#fef3c7;color:#b45309}
.b-green{background:#d1fae5;color:#059669}
.b-blue{background:#dbeafe;color:#1d4ed8}
.b-purple{background:#ede9fe;color:#6d28d9}

/* METRIC ROW */
.mrow{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px dashed #f1f5f9;font-size:.82rem}
.mrow:last-child{border:none}
.mkey{color:var(--muted);font-weight:500}
.mval{font-weight:700}

/* PROGRESS BARS */
.pbar-wrap{margin-bottom:10px}
.pbar-head{display:flex;justify-content:space-between;font-size:.75rem;font-weight:600;margin-bottom:3px}
.pbar-track{height:8px;background:#f1f5f9;border-radius:99px;overflow:hidden}
.pbar-fill{height:100%;border-radius:99px;transition:width .6s cubic-bezier(.4,0,.2,1)}

/* WHAT-IF OPTIONS */
.wi-opt{border:1.5px solid var(--border);border-radius:8px;padding:12px;margin-bottom:8px;transition:.2s}
.wi-opt.best{border-color:var(--green);background:#f0fdf4}
.wi-head{display:flex;justify-content:space-between;align-items:center;font-size:.82rem;font-weight:700}
.wi-stats{display:flex;gap:16px;margin-top:6px;font-size:.75rem;color:var(--muted)}

/* ROUTE ROWS */
.route-row{display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px dashed #f1f5f9;font-size:.8rem}
.route-row:last-child{border:none}
.route-name{flex:1;font-weight:700}
.route-tag{background:var(--sky);color:var(--blue);border-radius:4px;padding:2px 7px;font-size:.68rem;font-weight:700}
.route-tag.rec{background:#d1fae5;color:#059669}

/* ACTION CENTER */
.action-grid{display:flex;flex-wrap:wrap;gap:10px}
.btn{display:inline-flex;align-items:center;gap:7px;padding:9px 15px;border-radius:7px;
     font-size:.78rem;font-weight:600;cursor:pointer;border:1.5px solid var(--border);
     background:var(--card);color:var(--dark);text-decoration:none;transition:.15s}
.btn:hover{background:var(--accent);color:#fff;border-color:var(--accent)}
.btn-primary{background:var(--blue);color:#fff;border-color:var(--blue)}
.btn-primary:hover{background:var(--navy)}

/* CHART CONTAINERS */
.chart-box{position:relative;height:200px}
.chart-box-sm{position:relative;height:160px}
</style>
</head>
<body>

<!-- NAVBAR -->
<nav>
  <div class="nav-logo">
    <div class="chip">LS</div>
    <span>LogiSPARK Enterprise Decision Support</span>
  </div>
  <div class="nav-right">
    <div class="pulse-dot"></div>
    <span style="color:#10b981;font-weight:600">API LIVE</span>
    <span style="color:#94a3b8">|</span>
    <span style="color:#94a3b8">Powered by RandomForest AI</span>
  </div>
</nav>

<div class="layout">

  <!-- ── SIDEBAR ─────────────────────────────────────────────────── -->
  <div class="sidebar">
    <div class="s-label">Active Shipment</div>
    <select class="s-select" id="sel" onchange="load(this.value)">
      <option>Loading…</option>
    </select>

    <div class="s-label" style="margin-top:8px">Business Impact KPIs</div>
    <div class="kpi-card">
      <div class="kpi-label">Potential Loss Prevented</div>
      <div class="kpi-val" style="color:#10b981" id="g-loss">—</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Total Savings Generated</div>
      <div class="kpi-val" style="color:#3b82f6" id="g-sav">—</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Avg Delay Reduction</div>
      <div class="kpi-val" id="g-del">—</div>
    </div>
    <div class="kpi-card" style="border-color:rgba(239,68,68,.4)">
      <div class="kpi-label">Critical P1 Alerts</div>
      <div class="kpi-val" style="color:#ef4444" id="g-crit">—</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">High Risk Shipments</div>
      <div class="kpi-val" style="color:#f59e0b" id="g-high">—</div>
    </div>

    <!-- Cause distribution mini chart -->
    <div class="s-label" style="margin-top:8px">Global Delay Causes</div>
    <div style="background:rgba(255,255,255,.06);border-radius:8px;padding:10px">
      <div class="chart-box-sm"><canvas id="sidebarPie"></canvas></div>
    </div>
  </div>

  <!-- ── MAIN DASHBOARD ─────────────────────────────────────────── -->
  <div class="main">

    <!-- 1. Executive Summary Banner -->
    <div class="exec-banner" id="exec-banner">
      <div class="exec-icon">🤖</div>
      <div class="exec-text" id="exec-text">Loading AI narrative…</div>
    </div>

    <!-- 2. Top KPI Row: 4 metric cards -->
    <div class="grid-4">
      <div class="card" style="border-top:3px solid #ef4444">
        <div class="card-title">Delay Probability</div>
        <div style="font-size:2rem;font-weight:800;color:#ef4444" id="kpi-prob">—</div>
        <div id="kpi-risk" class="badge b-red" style="margin-top:6px">—</div>
      </div>
      <div class="card" style="border-top:3px solid #f59e0b">
        <div class="card-title">Predicted Delay</div>
        <div style="font-size:2rem;font-weight:800;color:#f59e0b" id="kpi-hrs">—</div>
        <div style="font-size:.75rem;color:var(--muted);margin-top:6px" id="kpi-type">—</div>
      </div>
      <div class="card" style="border-top:3px solid #3b82f6">
        <div class="card-title">Estimated Financial Loss</div>
        <div style="font-size:1.7rem;font-weight:800;color:#3b82f6" id="kpi-loss">—</div>
        <div style="font-size:.75rem;color:var(--muted);margin-top:6px" id="kpi-root">—</div>
      </div>
      <div class="card" style="border-top:3px solid #10b981">
        <div class="card-title">Potential Savings</div>
        <div style="font-size:1.7rem;font-weight:800;color:#10b981" id="kpi-sav">—</div>
        <div style="font-size:.75rem;color:var(--muted);margin-top:6px" id="kpi-action">—</div>
      </div>
    </div>

    <!-- 3. Priority Matrix + Delay Classification + Factor Contributions -->
    <div class="grid-3">

      <!-- Priority Matrix -->
      <div class="card">
        <div class="card-title">⚠️ Alert Priority Matrix</div>
        <div style="text-align:center;margin:10px 0">
          <div style="font-size:3rem;font-weight:900" id="mat-pri-big">—</div>
          <div class="badge b-red" id="mat-impact">—</div>
        </div>
        <div class="mrow"><span class="mkey">Customer Tier</span><span class="mval" id="mat-tier">—</span></div>
        <div class="mrow"><span class="mkey">Cargo Value</span><span class="mval" id="mat-val">—</span></div>
        <div class="mrow"><span class="mkey">Action Deadline</span><span class="mval" style="color:#ef4444" id="mat-dead">—</span></div>
      </div>

      <!-- Delay Classification -->
      <div class="card">
        <div class="card-title">🔍 Delay Classification</div>
        <div class="mrow"><span class="mkey">Type</span><span class="mval" id="clf-type">—</span></div>
        <div class="mrow"><span class="mkey">Severity</span><span id="clf-sev" class="badge">—</span></div>
        <div class="mrow"><span class="mkey">Predicted Delay</span><span class="mval" id="clf-hrs">—</span></div>
        <div class="mrow"><span class="mkey">AI Confidence</span><span class="mval" style="color:var(--green)" id="clf-conf">—</span></div>
        <div class="mrow"><span class="mkey">Root Cause</span><span class="mval" id="clf-root">—</span></div>
        <div class="mrow"><span class="mkey">Urgency</span><span id="clf-urg" class="badge">—</span></div>
      </div>

      <!-- Factor Contributions -->
      <div class="card">
        <div class="card-title">📊 AI Delay Explanation (Factor Contributions)</div>
        <div id="factor-bars"></div>
      </div>
    </div>

    <!-- 4. Charts Row: Gauge + Pie + Bar -->
    <div class="grid-3">
      <div class="card">
        <div class="card-title">🎯 Delay Risk Gauge</div>
        <div class="chart-box"><canvas id="gaugeChart"></canvas></div>
      </div>
      <div class="card">
        <div class="card-title">🥧 Cost Breakdown Distribution</div>
        <div class="chart-box"><canvas id="costPie"></canvas></div>
      </div>
      <div class="card">
        <div class="card-title">📉 What-If Delay Comparison</div>
        <div class="chart-box"><canvas id="whatifBar"></canvas></div>
      </div>
    </div>

    <!-- 5. Financial Breakdown + Advanced Root Cause -->
    <div class="grid-2">
      <div class="card">
        <div class="card-title">💰 Financial Impact Breakdown</div>
        <div id="fin-rows"></div>
        <div style="border-top:2px solid var(--border);padding-top:10px;margin-top:8px;display:flex;justify-content:space-between;font-weight:800;font-size:.9rem">
          <span>TOTAL ESTIMATED LOSS</span><span id="fin-total" style="color:#ef4444">—</span>
        </div>
      </div>
      <div class="card">
        <div class="card-title">🔬 Advanced Root Cause Metrics</div>
        <div class="mrow"><span class="mkey">Weather Score</span><span class="mval" id="arc-ws">—</span></div>
        <div class="mrow"><span class="mkey">Storm Risk</span><span class="mval" id="arc-sr">—</span></div>
        <div class="mrow"><span class="mkey">Visibility</span><span class="mval" id="arc-vis">—</span></div>
        <div class="mrow"><span class="mkey">Rainfall</span><span class="mval" id="arc-rain">—</span></div>
        <div class="mrow"><span class="mkey">Port Congestion</span><span class="mval" id="arc-pc">—</span></div>
        <div class="mrow"><span class="mkey">Berth Wait Hours</span><span class="mval" id="arc-bw">—</span></div>
        <div class="mrow"><span class="mkey">Vessel Queue</span><span class="mval" id="arc-vq">—</span></div>
        <div class="mrow"><span class="mkey">Customs Clearance Time</span><span class="mval" id="arc-ct">—</span></div>
        <div class="mrow"><span class="mkey">Documentation Errors</span><span class="mval" id="arc-de">—</span></div>
      </div>
    </div>

    <!-- 6. What-If Simulator + Savings Optimizer + Route Optimization -->
    <div class="grid-3">
      <div class="card">
        <div class="card-title">⚡ What-If Simulator</div>
        <div id="wi-box">—</div>
      </div>
      <div class="card">
        <div class="card-title">💡 AI Savings Optimizer</div>
        <div class="mrow"><span class="mkey">Recommendation</span><span class="mval" id="opt-rec" style="color:var(--blue);text-align:right;max-width:55%">—</span></div>
        <div class="mrow"><span class="mkey">Implementation Cost</span><span class="mval" style="color:#ef4444" id="opt-cost">—</span></div>
        <div class="mrow"><span class="mkey">Expected Savings</span><span class="mval" style="color:var(--green)" id="opt-sav">—</span></div>
        <div class="mrow"><span class="mkey">Net Benefit</span><span class="mval" style="font-size:1rem;color:var(--green)" id="opt-net">—</span></div>
        <div class="mrow"><span class="mkey">ROI</span><span id="opt-roi" class="badge b-green">—</span></div>
        <div class="mrow"><span class="mkey">Risk Reduction</span><span class="mval" id="opt-rr">—</span></div>
        <div class="mrow"><span class="mkey">AI Confidence</span><span class="mval" style="color:var(--green)" id="opt-conf">—</span></div>
      </div>
      <div class="card">
        <div class="card-title">🗺️ Route Optimization Panel</div>
        <div id="route-box">—</div>
      </div>
    </div>

    <!-- 7. Health Scores + Radar Chart -->
    <div class="grid-2">
      <div class="card">
        <div class="card-title">🩺 Shipment Health Scores</div>
        <div id="health-bars"></div>
      </div>
      <div class="card">
        <div class="card-title">📡 Multi-Dimensional Risk Radar</div>
        <div class="chart-box"><canvas id="radarChart"></canvas></div>
      </div>
    </div>

    <!-- 8. Savings vs Loss Bar + Shipment Info -->
    <div class="grid-2">
      <div class="card">
        <div class="card-title">📊 Loss vs. Savings – What-If Analysis</div>
        <div class="chart-box"><canvas id="savingsBar"></canvas></div>
      </div>
      <div class="card">
        <div class="card-title">📦 Shipment Details</div>
        <div class="mrow"><span class="mkey">Shipment ID</span><span class="mval" id="info-id">—</span></div>
        <div class="mrow"><span class="mkey">Origin</span><span class="mval" id="info-org">—</span></div>
        <div class="mrow"><span class="mkey">Destination</span><span class="mval" id="info-dst">—</span></div>
        <div class="mrow"><span class="mkey">Carrier</span><span class="mval" id="info-car">—</span></div>
        <div class="mrow"><span class="mkey">Mode</span><span class="mval" id="info-mode">—</span></div>
        <div class="mrow"><span class="mkey">Container Type</span><span class="mval" id="info-cont">—</span></div>
        <div class="mrow"><span class="mkey">Distance</span><span class="mval" id="info-dist">—</span></div>
        <div class="mrow"><span class="mkey">Departure</span><span class="mval" id="info-dep">—</span></div>
        <div class="mrow"><span class="mkey">Arrival</span><span class="mval" id="info-arr">—</span></div>
      </div>
    </div>

    <!-- 9. Action Center -->
    <div class="card">
      <div class="card-title">🚀 Enterprise Action Center</div>
      <div class="action-grid" id="action-btns">
        <a id="btn-pdf"   class="btn btn-primary" href="#" target="_blank">📥 Download PDF Report</a>
        <a id="btn-xlsx"  class="btn btn-primary" href="#" target="_blank">📊 Export to Excel</a>
        <a id="btn-json"  class="btn"             href="#" target="_blank">{ } Export JSON</a>
        <button class="btn">🔔 Notify Operations</button>
        <button class="btn">✉️  Notify Customer</button>
        <button class="btn">🚢 Request Alternate Port</button>
        <button class="btn">✈️  Request Alternate Carrier</button>
        <button class="btn">🛡️  Generate Mitigation Plan</button>
        <button class="btn">📄 Generate Delay Report</button>
      </div>
    </div>

  </div><!-- /main -->
</div><!-- /layout -->

<!-- ── JAVASCRIPT ──────────────────────────────────────────────── -->
<script>
const INR = n => 'Rs.\u00a0' + Math.round(n).toLocaleString('en-IN');
const PCT = n => n + '%';
let gaugeInst, costPieInst, whatifBarInst, radarInst, savingsBarInst, sidebarPieInst;

function destroyChart(inst){ if(inst){ inst.destroy(); } }

/* ─ Boot ─────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  /* Global sidebar KPIs */
  fetch('/api/stats').then(r=>r.json()).then(d=>{
    document.getElementById('g-loss').textContent = INR(d.potential_loss_prevented);
    document.getElementById('g-sav').textContent  = INR(d.total_savings_generated);
    document.getElementById('g-del').textContent  = d.avg_delay_reduction_hrs + ' hrs';
    document.getElementById('g-crit').textContent = d.critical_alerts;
    document.getElementById('g-high').textContent = d.high_risk_shipments;
    drawSidebarPie(d.cause_distribution);
  });

  /* Shipment dropdown */
  fetch('/api/shipments').then(r=>r.json()).then(list=>{
    const sel = document.getElementById('sel');
    sel.innerHTML = '';
    list.sort((a,b)=> a.shipment_id==='SH110'?-1:(b.shipment_id==='SH110'?1:0));
    list.forEach(s=>{
      const o = document.createElement('option');
      o.value = s.shipment_id;
      o.textContent = `${s.shipment_id}  ${s.origin.split(' ').pop()} ➔ ${s.destination.split(' ').pop()} (${s.customer_tier})`;
      sel.appendChild(o);
    });
    load('SH110');
  });
});

/* ─ Main Load ─────────────────────────────────────────────────── */
function load(id){
  document.getElementById('sel').value = id;
  fetch('/predict/'+id).then(r=>r.json()).then(d=> render(d));
}

function render(d){
  const r = d.recommendation_v2;
  const fin = d.financial_breakdown;

  /* Exec banner */
  document.getElementById('exec-text').innerHTML = d.ai_summary.replace(
    /(Rs\.[^\\.]+|Route Diversion|Urgency HIGH|77%|22\.7|39,104|23,462)/g,
    '<strong>$1</strong>'
  );

  /* Top KPIs */
  const probColor = d.delay_probability>=70?'#ef4444':(d.delay_probability>=30?'#f59e0b':'#10b981');
  document.getElementById('kpi-prob').textContent = PCT(d.delay_probability);
  document.getElementById('kpi-prob').style.color = probColor;
  document.getElementById('kpi-risk').textContent = d.risk_level;
  document.getElementById('kpi-risk').className = 'badge '+(d.delay_probability>=70?'b-red':d.delay_probability>=30?'b-amber':'b-green');
  document.getElementById('kpi-hrs').textContent  = d.predicted_delay_hours + ' hrs';
  document.getElementById('kpi-type').textContent = d.delay_classification.type + ' Delay';
  document.getElementById('kpi-loss').textContent = INR(fin.total_loss);
  document.getElementById('kpi-root').textContent = '📍 ' + d.root_cause;
  document.getElementById('kpi-sav').textContent  = INR(r.potential_savings);
  document.getElementById('kpi-action').textContent = '✅ ' + r.recommended_action;

  /* Priority matrix */
  document.getElementById('mat-pri-big').textContent = d.priority_matrix.priority;
  document.getElementById('mat-pri-big').style.color = d.priority_matrix.priority==='P1'?'#ef4444':d.priority_matrix.priority==='P2'?'#f59e0b':'#10b981';
  document.getElementById('mat-impact').textContent = d.priority_matrix.business_impact + ' Impact';
  document.getElementById('mat-impact').className = 'badge '+(d.priority_matrix.business_impact==='Critical'?'b-red':d.priority_matrix.business_impact==='High'?'b-amber':'b-green');
  document.getElementById('mat-tier').textContent  = d.priority_matrix.customer_tier;
  document.getElementById('mat-val').textContent   = INR(d.priority_matrix.shipment_value);
  document.getElementById('mat-dead').textContent  = d.priority_matrix.action_deadline;

  /* Delay classification */
  const sev = d.delay_classification.severity;
  document.getElementById('clf-type').textContent = d.delay_classification.type;
  document.getElementById('clf-sev').textContent  = sev;
  document.getElementById('clf-sev').className = 'badge '+(sev==='Critical'||sev==='High'?'b-red':sev==='Medium'?'b-amber':'b-green');
  document.getElementById('clf-hrs').textContent  = d.delay_classification.predicted_delay_hours + ' hrs';
  document.getElementById('clf-conf').textContent = d.delay_classification.confidence + '%';
  document.getElementById('clf-root').textContent = d.root_cause;
  document.getElementById('clf-urg').textContent  = d.urgency;
  document.getElementById('clf-urg').className    = 'badge '+(d.urgency==='HIGH'?'b-red':d.urgency==='MEDIUM'?'b-amber':'b-green');

  /* Factor contribution bars */
  const fb = document.getElementById('factor-bars'); fb.innerHTML = '';
  const factColors = {'Weather':'#ef4444','Port Congestion':'#f59e0b','Customs':'#8b5cf6','Traffic':'#3b82f6','Documentation Error':'#10b981'};
  Object.entries(d.factor_contributions).sort((a,b)=>b[1]-a[1]).forEach(([k,v])=>{
    const c = factColors[k]||'#3b82f6';
    fb.innerHTML += `<div class="pbar-wrap">
      <div class="pbar-head"><span>${k}</span><span style="color:${c}">+${v}%</span></div>
      <div class="pbar-track"><div class="pbar-fill" style="width:${v}%;background:${c}"></div></div>
    </div>`;
  });

  /* Financial breakdown rows */
  const fr = document.getElementById('fin-rows'); fr.innerHTML='';
  const finLabels = {warehousing_cost:'Warehousing',demurrage_charges:'Demurrage',sla_penalty:'SLA Penalty',inventory_holding_cost:'Inventory Holding',fuel_impact:'Fuel Impact',customer_compensation:'Customer Compensation'};
  Object.entries(fin).forEach(([k,v])=>{
    if(k==='total_loss') return;
    fr.innerHTML += `<div class="mrow"><span class="mkey">${finLabels[k]||k}</span><span class="mval">${INR(v)}</span></div>`;
  });
  document.getElementById('fin-total').textContent = INR(fin.total_loss);

  /* Advanced metrics */
  const a = d.advanced_root_cause;
  document.getElementById('arc-ws').textContent   = a.weather_score + ' / 100';
  document.getElementById('arc-sr').textContent   = (a.storm_risk*100).toFixed(0) + '%';
  document.getElementById('arc-vis').textContent  = a.visibility + ' km';
  document.getElementById('arc-rain').textContent = a.rainfall + ' mm';
  document.getElementById('arc-pc').textContent   = a.port_congestion + ' / 100';
  document.getElementById('arc-bw').textContent   = a.berth_wait_hours + ' hrs';
  document.getElementById('arc-vq').textContent   = a.vessel_queue + ' vessels';
  document.getElementById('arc-ct').textContent   = a.customs_time + ' hrs';
  document.getElementById('arc-de').textContent   = a.doc_errors + (a.doc_errors===1?' error':' errors');

  /* What-If Simulator */
  const wb = document.getElementById('wi-box'); wb.innerHTML='';
  (r.what_if_options||[]).forEach(w=>{
    wb.innerHTML += `<div class="wi-opt ${w.is_best?'best':''}">
      <div class="wi-head"><span>${w.name}</span>${w.is_best?'<span class="badge b-green">BEST</span>':''}</div>
      <div class="wi-stats">
        <span>Delay: <strong>${w.delay}h</strong></span>
        <span>Loss: <strong>${INR(w.loss)}</strong></span>
        <span>Saves: <strong style="color:#10b981">${INR(w.savings)}</strong></span>
      </div>
    </div>`;
  });

  /* Savings optimizer */
  document.getElementById('opt-rec').textContent  = r.recommended_action;
  document.getElementById('opt-cost').textContent = INR(r.implementation_cost);
  document.getElementById('opt-sav').textContent  = INR(r.potential_savings);
  document.getElementById('opt-net').textContent  = INR(r.net_benefit);
  document.getElementById('opt-roi').textContent  = r.roi + '% ROI';
  document.getElementById('opt-rr').textContent   = r.risk_reduction;
  document.getElementById('opt-conf').textContent = r.confidence + '%';

  /* Route optimization */
  const rb = document.getElementById('route-box'); rb.innerHTML='';
  (r.route_options||[]).forEach(ro=>{
    rb.innerHTML += `<div class="route-row">
      <div class="route-name">${ro.name}</div>
      <span class="route-tag ${ro.is_recommended?'rec':''}">Risk ${ro.risk}%</span>
      <span style="font-size:.75rem;color:var(--muted)">${ro.eta}</span>
      <span style="font-weight:700;font-size:.8rem">${INR(ro.cost)}</span>
    </div>`;
  });

  /* Health Scores */
  const hb = document.getElementById('health-bars'); hb.innerHTML='';
  Object.entries(d.health_scores).forEach(([k,v])=>{
    const c = v>=75?'#10b981':v>=40?'#f59e0b':'#ef4444';
    hb.innerHTML += `<div class="pbar-wrap">
      <div class="pbar-head"><span>${k}</span><span style="color:${c};font-weight:700">${v}/100</span></div>
      <div class="pbar-track"><div class="pbar-fill" style="width:${v}%;background:${c}"></div></div>
    </div>`;
  });

  /* Shipment info */
  document.getElementById('info-id').textContent   = d.shipment_id;
  document.getElementById('info-org').textContent  = d.origin;
  document.getElementById('info-dst').textContent  = d.destination;
  document.getElementById('info-car').textContent  = d.carrier;
  document.getElementById('info-mode').textContent = d.mode;
  document.getElementById('info-cont').textContent = d.container_type;
  document.getElementById('info-dist').textContent = (d.distance_km||'—') + ' km';
  document.getElementById('info-dep').textContent  = (d.scheduled_departure||'—').replace('T',' ');
  document.getElementById('info-arr').textContent  = (d.scheduled_arrival||'—').replace('T',' ');

  /* Export links */
  document.getElementById('btn-pdf').href  = `/predict/${d.shipment_id}/pdf`;
  document.getElementById('btn-xlsx').href = `/predict/${d.shipment_id}/excel`;
  document.getElementById('btn-json').href = `/predict/${d.shipment_id}/json`;

  /* ── Draw Charts ── */
  drawGauge(d.delay_probability);
  drawCostPie(fin);
  drawWhatifBar(r.what_if_options||[]);
  drawRadar(d);
  drawSavingsBar(r.what_if_options||[], fin.total_loss);
}

/* ─ Gauge (doughnut) ─────────────────────────────────────────── */
function drawGauge(pct){
  destroyChart(gaugeInst);
  const c = pct>=70?'#ef4444':pct>=30?'#f59e0b':'#10b981';
  const ctx = document.getElementById('gaugeChart').getContext('2d');
  gaugeInst = new Chart(ctx,{
    type:'doughnut',
    data:{labels:['Risk','Safe'],datasets:[{data:[pct,100-pct],backgroundColor:[c,'#f1f5f9'],borderWidth:0,circumference:270,rotation:225}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'75%',plugins:{
      tooltip:{callbacks:{label:i=>i.dataIndex===0?`Delay Risk: ${pct}%`:''}},
      legend:{display:false}
    }}
  });
}

/* ─ Cost Breakdown Pie ────────────────────────────────────────── */
function drawCostPie(fin){
  destroyChart(costPieInst);
  const labels=[], data=[], colors=['#1e3a8a','#3b82f6','#f59e0b','#ef4444','#10b981','#8b5cf6'];
  const lmap={warehousing_cost:'Warehousing',demurrage_charges:'Demurrage',sla_penalty:'SLA Penalty',
              inventory_holding_cost:'Inventory',fuel_impact:'Fuel',customer_compensation:'Compensation'};
  let i=0;
  Object.entries(fin).forEach(([k,v])=>{ if(k!=='total_loss'&&v>0){labels.push(lmap[k]||k);data.push(v);i++;} });
  const ctx = document.getElementById('costPie').getContext('2d');
  costPieInst = new Chart(ctx,{
    type:'pie',
    data:{labels,datasets:[{data,backgroundColor:colors.slice(0,data.length),borderWidth:1,borderColor:'#fff'}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'right',labels:{font:{size:9,family:'Inter'},boxWidth:10}}}}
  });
}

/* ─ What-If Delay Bar ─────────────────────────────────────────── */
function drawWhatifBar(opts){
  destroyChart(whatifBarInst);
  if(!opts.length) return;
  const labels = opts.map(o=>o.name.split(':')[0]);
  const delays = opts.map(o=>o.delay);
  const bgColors = opts.map(o=> o.is_best?'#10b981':'#3b82f6');
  const ctx = document.getElementById('whatifBar').getContext('2d');
  whatifBarInst = new Chart(ctx,{
    type:'bar',
    data:{labels,datasets:[{label:'Delay (hrs)',data:delays,backgroundColor:bgColors,borderRadius:5}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},
      scales:{y:{beginAtZero:true,title:{display:true,text:'Hours',font:{size:9}},ticks:{font:{size:9}}},
              x:{ticks:{font:{size:9}}}}}
  });
}

/* ─ Radar Chart ───────────────────────────────────────────────── */
function drawRadar(d){
  destroyChart(radarInst);
  const h = d.health_scores;
  const labels = Object.keys(h).filter(k=>k!=='Overall');
  const vals   = labels.map(k=>h[k]);
  const ctx = document.getElementById('radarChart').getContext('2d');
  radarInst = new Chart(ctx,{
    type:'radar',
    data:{labels,datasets:[{label:'Health Score',data:vals,backgroundColor:'rgba(59,130,246,.15)',borderColor:'#3b82f6',borderWidth:2,pointBackgroundColor:'#3b82f6'}]},
    options:{responsive:true,maintainAspectRatio:false,
      scales:{r:{min:0,max:100,ticks:{stepSize:25,font:{size:8}},pointLabels:{font:{size:9}}}},
      plugins:{legend:{display:false}}}
  });
}

/* ─ Savings vs Loss Grouped Bar ──────────────────────────────── */
function drawSavingsBar(opts, currentLoss){
  destroyChart(savingsBarInst);
  const labels  = ['Current', ...opts.map(o=>o.name.split(':')[0])];
  const losses  = [currentLoss, ...opts.map(o=>o.loss)];
  const savings = [0, ...opts.map(o=>o.savings)];
  const ctx = document.getElementById('savingsBar').getContext('2d');
  savingsBarInst = new Chart(ctx,{
    type:'bar',
    data:{labels,datasets:[
      {label:'Loss (Rs.)',data:losses,backgroundColor:'#ef4444',borderRadius:4},
      {label:'Savings (Rs.)',data:savings,backgroundColor:'#10b981',borderRadius:4}
    ]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'top',labels:{font:{size:9},boxWidth:10}}},
      scales:{y:{beginAtZero:true,ticks:{font:{size:9},callback:v=>'Rs. '+(v>=1000?(v/1000)+'k':v)}},
              x:{ticks:{font:{size:9}}}}}
  });
}

/* ─ Sidebar Pie ──────────────────────────────────────────────── */
function drawSidebarPie(causes){
  destroyChart(sidebarPieInst);
  const labels = Object.keys(causes);
  const data   = Object.values(causes);
  const ctx = document.getElementById('sidebarPie').getContext('2d');
  sidebarPieInst = new Chart(ctx,{
    type:'doughnut',
    data:{labels,datasets:[{data,backgroundColor:['#ef4444','#f59e0b','#8b5cf6','#3b82f6','#10b981'],borderWidth:1,borderColor:'rgba(255,255,255,.2)'}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'bottom',labels:{color:'#94a3b8',font:{size:8},boxWidth:8}}}}
  });
}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    print("Launching LogiSPARK Enterprise Decision Support Server...")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
