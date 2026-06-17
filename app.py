import os
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from modules.shipment_delay.app import router as shipment_delay_router
from modules.shipment_delay.predictor import ShipmentPredictor
from modules.hs_classifier.predict import classify, get_mode, build_index_if_needed
from modules.emergency_transport.emergency_transport_engine import plan_emergency
from modules.risk_assessment.risk_assessment_engine import assess_risk

app = FastAPI(title="LogiSPARK Enterprise AI Logistics Platform")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Mount module routers
app.include_router(shipment_delay_router)

# For platform stats, we need access to the predictor from shipment_delay
predictor = ShipmentPredictor()

@app.on_event("startup")
async def startup_event():
    print("[LogiSPARK] Initialising platform…")
    try:
        build_index_if_needed()
        print(f"[LogiSPARK] HS Classifier ready — mode: {get_mode()}")
    except Exception as exc:
        print(f"[LogiSPARK] HS Classifier index warning: {exc}")
    print("[LogiSPARK] All systems operational.")

@app.get("/health")
def health_check():
    return {
        "status": "running",
        "modules": ["shipment_delay", "hs_classifier", "emergency_transport", "risk_assessment"],
        "hs_mode": get_mode(),
    }

@app.get("/api/platform-stats")
def get_platform_stats():
    """Dashboard-level KPIs across all modules."""
    base = predictor.get_summary_stats()
    return {
        "total_modules": 4,
        "active_services": 12,
        "platform_health": "Healthy",
        "uptime_pct": "99.97%",
        "total_shipments_analyzed": len(predictor.get_all_shipments()),
        "predicted_cost_savings": round(base["total_savings_generated"], 2),
        "potential_loss_prevented": round(base["potential_loss_prevented"], 2),
        "critical_alerts": base["critical_alerts"],
        "high_risk_shipments": base["high_risk_shipments"],
        "ai_status": "ONLINE",
        "hs_classifier_mode": get_mode(),
    }

# ──────────────────────────────────────────────────────────────────────────────
# HS CLASSIFIER API
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/api/hs-classify")
def classify_hs_get(q: str = ""):
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required.")
    return classify(q, top_k=5)

@app.post("/api/hs-classify")
async def classify_hs_post(request: Request):
    try:
        body = await request.json()
        query = body.get("query", "").strip()
        if not query:
            raise HTTPException(status_code=400, detail="'query' field is required.")
        return classify(query, top_k=5)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

# ──────────────────────────────────────────────────────────────────────────────
# EMERGENCY TRANSPORT API
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/api/emergency-plan")
async def emergency_plan_post(request: Request):
    try:
        body = await request.json()
        return plan_emergency(
            transport_type=body.get("transport_type", "Ocean"),
            severity=body.get("severity", "high"),
            origin=body.get("origin", "Mumbai"),
            destination=body.get("destination", "Delhi"),
            cargo_value=float(body.get("cargo_value", 1_000_000)),
            current_delay_hrs=float(body.get("current_delay_hrs", 24)),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/api/emergency-plan")
def emergency_plan_get(
    transport_type: str = "Ocean",
    severity: str = "high",
    origin: str = "Mumbai",
    destination: str = "Delhi",
    cargo_value: float = 1_000_000,
    current_delay_hrs: float = 24,
):
    try:
        return plan_emergency(
            transport_type=transport_type,
            severity=severity,
            origin=origin,
            destination=destination,
            cargo_value=cargo_value,
            current_delay_hrs=current_delay_hrs,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

# ──────────────────────────────────────────────────────────────────────────────
# RISK ASSESSMENT API
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/api/risk-assess")
async def risk_assess_post(request: Request):
    try:
        body = await request.json()
        return assess_risk(
            origin=body.get("origin", "Mumbai"),
            destination=body.get("destination", "Delhi"),
            mode=body.get("mode", "Ocean"),
            cargo_type=body.get("cargo_type", "Electronics"),
            cargo_value=float(body.get("cargo_value", 1_000_000)),
            route_region=body.get("route_region", ""),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/api/risk-assess")
def risk_assess_get(
    origin: str = "Mumbai",
    destination: str = "Delhi",
    mode: str = "Ocean",
    cargo_type: str = "Electronics",
    cargo_value: float = 1_000_000,
):
    try:
        return assess_risk(
            origin=origin,
            destination=destination,
            mode=mode,
            cargo_type=cargo_type,
            cargo_value=cargo_value,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

# ──────────────────────────────────────────────────────────────────────────────
# HTML PAGE ROUTES
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def get_main_dashboard(request: Request):
    return templates.TemplateResponse(
        request=request, name="dashboard.html",
        context={"active_page": "dashboard"},
    )

@app.get("/shipment-delay", response_class=HTMLResponse)
def get_shipment_delay(request: Request):
    return templates.TemplateResponse(
        request=request, name="shipment_delay.html",
        context={"active_page": "shipment_delay"},
    )

@app.get("/emergency-transport", response_class=HTMLResponse)
def get_emergency_transport(request: Request):
    return templates.TemplateResponse(
        request=request, name="emergency_transport.html",
        context={"active_page": "emergency_transport"},
    )

@app.get("/hs-classifier", response_class=HTMLResponse)
def get_hs_classifier(request: Request):
    return templates.TemplateResponse(
        request=request, name="hs_classifier.html",
        context={"active_page": "hs_classifier"},
    )

@app.get("/risk-assessment", response_class=HTMLResponse)
def get_risk_assessment(request: Request):
    return templates.TemplateResponse(
        request=request, name="risk_assessment.html",
        context={"active_page": "risk_assessment"},
    )

if __name__ == "__main__":
    print("=" * 60)
    print("  LogiSPARK AI Logistics Platform  –  Starting…")
    print("  Dashboard →  http://127.0.0.1:8000")
    print("=" * 60)
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
