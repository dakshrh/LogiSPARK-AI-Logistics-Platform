import os
import uvicorn
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request, Query, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.database import engine, Base, get_db
from database import crud
from database.seed import seed_db

from modules.shipment_delay.app import router as shipment_delay_router
from modules.shipment_delay.predictor import ShipmentPredictor
from modules.hs_classifier.predict import classify, get_mode, build_index_if_needed
from modules.emergency_transport.emergency_transport_engine import plan_emergency
from modules.risk_assessment.risk_assessment_engine import assess_risk
from modules.shipment_tracking.app import router as shipment_tracking_router
from modules.copilot.app import router as copilot_router
from modules.emergency_transport.pdf_generator import generate_emergency_pdf

tags_metadata = [
    {
        "name": "Platform",
        "description": "Core platform operations, health checks, and AI copilot interactions.",
    },
    {
        "name": "HS Classification",
        "description": "AI-powered HS Code classification for global trade compliance.",
    },
    {
        "name": "Emergency Planning",
        "description": "Generate emergency recovery and alternative transport plans.",
    },
    {
        "name": "Analytics",
        "description": "Risk assessment and global analytics.",
    },
    {
        "name": "Delay Prediction",
        "description": "Predictive modeling for shipment delays.",
    },
    {
        "name": "Shipment Tracking",
        "description": "Track shipment statuses with AI insights.",
    },
]

app = FastAPI(
    title="LogiSPARK Enterprise AI Logistics Platform",
    description="An enterprise-grade AI-powered platform for predicting shipment delays, classifying HS codes, planning emergency transport, and assessing route risks.",
    version="1.0.0",
    contact={
        "name": "LogiSPARK Support",
        "email": "support@logispark.com",
    },
    openapi_tags=tags_metadata,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Mount module routers
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(shipment_delay_router)
app.include_router(shipment_tracking_router)
app.include_router(copilot_router)

# For platform stats, we need access to the predictor from shipment_delay
predictor = ShipmentPredictor()

# ──────────────────────────────────────────────────────────────────────────────
# PYDANTIC MODELS
# ──────────────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = Field(..., description="Current status of the API", examples=["running"])
    modules: List[str] = Field(..., description="List of active modules", examples=[["shipment_delay", "hs_classifier"]])
    hs_mode: str = Field(..., description="Current mode of the HS classifier", examples=["hybrid"])

class PlatformStatsResponse(BaseModel):
    total_modules: int = Field(..., examples=[4])
    active_services: int = Field(..., examples=[12])
    platform_health: str = Field(..., examples=["Healthy"])
    uptime_pct: str = Field(..., examples=["99.97%"])
    total_shipments_analyzed: int = Field(..., examples=[5000])
    predicted_cost_savings: float = Field(..., examples=[125000.50])
    potential_loss_prevented: float = Field(..., examples=[500000.00])
    critical_alerts: int = Field(..., examples=[15])
    high_risk_shipments: int = Field(..., examples=[42])
    ai_status: str = Field(..., examples=["ONLINE"])
    hs_classifier_mode: str = Field(..., examples=["hybrid"])

class HSClassifyRequest(BaseModel):
    query: str = Field(..., description="Product description to classify", examples=["Wireless noise-canceling headphones"])

class HSClassifyResult(BaseModel):
    rank: int = Field(..., description="Rank of the result")
    hscode: str = Field(..., description="Predicted HS Code")
    description: str = Field(..., description="Description of the HS Code")
    confidence: float = Field(..., description="Confidence score percentage")

class HSTopMatch(BaseModel):
    hscode: str = Field(..., description="HS Code")
    description: str = Field(..., description="Description")
    confidence: float = Field(..., description="Confidence percentage")
    sem_similarity: float = Field(..., description="Semantic similarity")
    keyword_score: float = Field(..., description="Keyword score")
    domain_boost_applied: bool = Field(..., description="Domain boost applied")

class ExplainableAI(BaseModel):
    detected_category: Optional[str] = Field(None, description="Detected category")
    expanded_query: str = Field(..., description="Expanded query")
    matched_keywords: List[str] = Field(..., description="Matched keywords")
    rules_applied: List[str] = Field(..., description="Rules applied")
    domain_boost_applied: bool = Field(..., description="Domain boost applied")

class HSClassifyResponse(BaseModel):
    query: str = Field(..., description="Original query")
    mode: str = Field(..., description="Classification mode used")
    top_match: HSTopMatch = Field(..., description="Top match details")
    classification_path: str = Field(..., description="Classification path")
    explainable_ai: ExplainableAI = Field(..., description="Explainable AI details")
    results: List[HSClassifyResult] = Field(..., description="Top classification results")

class EmergencyPlanRequest(BaseModel):
    transport_type: str = Field("Ocean", description="Mode of transport", examples=["Ocean"])
    severity: str = Field("high", description="Severity of delay", examples=["high"])
    origin: str = Field("Mumbai", description="Origin port/city", examples=["Mumbai"])
    destination: str = Field("Delhi", description="Destination port/city", examples=["Delhi"])
    cargo_value: float = Field(1000000.0, description="Value of the cargo in INR", examples=[1000000.0])
    current_delay_hrs: float = Field(24.0, description="Current delay in hours", examples=[24.0])

class ETAImpact(BaseModel):
    original_eta: str = Field(..., description="Original estimated time of arrival")
    revised_eta: str = Field(..., description="Revised estimated time of arrival after emergency action")
    delay_reduction_pct: float = Field(..., description="Percentage of delay reduction")
    delay_reduction_hrs: float = Field(..., description="Hours of delay reduction")

class CarrierSuggestion(BaseModel):
    rank: int = Field(..., description="Rank of carrier")
    name: str = Field(..., description="Name of carrier")
    reliability: float = Field(..., description="Reliability score")
    estimated_cost: float = Field(..., description="Estimated cost")
    eta_hours: float = Field(..., description="ETA in hours")
    delay_reduction_hrs: float = Field(..., description="Delay reduction in hours")
    recommended: bool = Field(..., description="Is recommended")
    historical_performance: str = Field(..., description="Historical performance")
    disruption_risk: str = Field(..., description="Disruption risk")
    weather_risk: str = Field(..., description="Weather risk")
    port_congestion: str = Field(..., description="Port congestion")
    customs_delays: str = Field(..., description="Customs delays")

class EmergencyRoute(BaseModel):
    type: str = Field(..., description="Type of route")
    path: str = Field(..., description="Path taken")
    distance_km: float = Field(..., description="Distance in km")
    risk_pct: float = Field(..., description="Risk percentage")
    congestion_score: float = Field(..., description="Congestion score")
    cost_impact: float = Field(..., description="Cost impact")
    eta_impact_hrs: float = Field(..., description="ETA impact in hours")
    is_recommended: bool = Field(..., description="Is recommended")

class EmergencyPlanResponse(BaseModel):
    transport_type: str = Field(..., description="Transport type")
    severity: str = Field(..., description="Severity of emergency")
    severity_label: str = Field(..., description="Severity label")
    severity_color: str = Field(..., description="Severity color code")
    origin: str = Field(..., description="Origin location")
    destination: str = Field(..., description="Destination location")
    cargo_value: float = Field(..., description="Value of cargo")
    current_delay_hrs: float = Field(..., description="Current delay in hours")
    recommended_action: str = Field(..., description="Recommended emergency action")
    action_description: str = Field(..., description="Description of action")
    risk_level_after: str = Field(..., description="Risk level after action")
    estimated_loss: float = Field(..., description="Estimated loss without action")
    estimated_savings: float = Field(..., description="Estimated savings with action")
    implementation_cost: float = Field(..., description="Cost to implement action")
    net_benefit: float = Field(..., description="Net financial benefit")
    carrier_suggestions: List[CarrierSuggestion] = Field(..., description="List of carrier suggestions")
    emergency_routes: List[EmergencyRoute] = Field(..., description="List of emergency routes")
    eta_impact: ETAImpact = Field(..., description="Impact on ETA")
    ai_narrative: str = Field(..., description="AI generated summary narrative")

class RiskAssessRequest(BaseModel):
    origin: str = Field("Mumbai", description="Origin city/port", examples=["Mumbai"])
    destination: str = Field("Delhi", description="Destination city/port", examples=["Delhi"])
    mode: str = Field("Ocean", description="Transport mode", examples=["Ocean"])
    cargo_type: str = Field("Electronics", description="Type of cargo", examples=["Electronics"])
    cargo_value: float = Field(1000000.0, description="Value of the cargo", examples=[1000000.0])
    route_region: str = Field("", description="Specific route region if any", examples=["Suez Canal"])

class HeatmapItem(BaseModel):
    factor: str = Field(..., description="Risk factor name")
    score: float = Field(..., description="Risk score")
    color: str = Field(..., description="Color code")

class TopRisk(BaseModel):
    factor: str = Field(..., description="Top risk factor")
    score: float = Field(..., description="Risk score")

class RiskAssessResponse(BaseModel):
    origin: str = Field(..., description="Origin location")
    destination: str = Field(..., description="Destination location")
    mode: str = Field(..., description="Transport mode")
    cargo_type: str = Field(..., description="Cargo type")
    cargo_value: float = Field(..., description="Value of cargo")
    risk_scores: Dict[str, float] = Field(..., description="Individual risk scores")
    overall_score: float = Field(..., description="Overall risk score")
    category: str = Field(..., description="Risk category")
    category_color: str = Field(..., description="Category color code")
    category_badge: str = Field(..., description="Category badge CSS class")
    heatmap: List[HeatmapItem] = Field(..., description="Heatmap data")
    recommendations: List[str] = Field(..., description="List of recommendations")
    mitigations: List[str] = Field(..., description="List of mitigations")
    financial_exposure: float = Field(..., description="Financial exposure")
    mitigation_potential: float = Field(..., description="Mitigation potential savings")
    ai_narrative: str = Field(..., description="AI generated narrative")
    top_risk: TopRisk = Field(..., description="Top risk factor detail")

@app.on_event("startup")
async def startup_event():
    print("[LogiSPARK] Initialising platform database…")
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    seed_db(db)
    print("[LogiSPARK] Database initialized.")
    try:
        build_index_if_needed()
        print(f"[LogiSPARK] HS Classifier ready — mode: {get_mode()}")
    except Exception as exc:
        print(f"[LogiSPARK] HS Classifier index warning: {exc}")
    print("[LogiSPARK] All systems operational.")

@app.get("/health", response_model=HealthResponse, tags=["Platform"], summary="Check Platform Health", description="Returns the current operational status of the platform and its active modules.")
def health_check():
    return {
        "status": "running",
        "modules": ["shipment_delay", "hs_classifier", "emergency_transport", "risk_assessment"],
        "hs_mode": get_mode(),
    }

@app.get("/api/platform-stats", response_model=PlatformStatsResponse, tags=["Platform"], summary="Get Platform Stats", description="Dashboard-level KPIs across all modules including financial savings and alerts.")
def get_platform_stats(db: Session = Depends(get_db)):
    base = predictor.get_summary_stats()
    active_shipments = crud.get_active_shipments_count(db)
    return {
        "total_modules": 4,
        "active_services": 12,
        "platform_health": "Healthy",
        "uptime_pct": "99.97%",
        "total_shipments_analyzed": active_shipments + len(predictor.get_all_shipments()),
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
@app.get("/api/hs-classify", response_model=HSClassifyResponse, tags=["HS Classification"], summary="Classify HS Code via GET", description="Classify a product description to find the most probable HS codes.")
def classify_hs_get(q: str = Query(..., description="Product description to classify", examples=["Leather boots"]), db: Session = Depends(get_db)):
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required.")
    res = classify(q, top_k=5)
    
    top_code = res["top_match"]["hscode"] if res.get("top_match") else "Unknown"
    conf = res["top_match"]["confidence"] if res.get("top_match") else 0.0
    crud.save_hs_classification(db, q, top_code, conf)
    return res

@app.post("/api/hs-classify", response_model=HSClassifyResponse, tags=["HS Classification"], summary="Classify HS Code via POST", description="Classify a product description to find the most probable HS codes using a JSON payload.")
async def classify_hs_post(request: HSClassifyRequest, db: Session = Depends(get_db)):
    try:
        query = request.query.strip()
        if not query:
            raise HTTPException(status_code=400, detail="'query' field cannot be empty.")
        res = classify(query, top_k=5)
        
        top_code = res["top_match"]["hscode"] if res.get("top_match") else "Unknown"
        conf = res["top_match"]["confidence"] if res.get("top_match") else 0.0
        crud.save_hs_classification(db, query, top_code, conf)
        return res
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

# ──────────────────────────────────────────────────────────────────────────────
# EMERGENCY TRANSPORT API
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/api/emergency-plan", response_model=EmergencyPlanResponse, tags=["Emergency Planning"], summary="Generate Emergency Transport Plan", description="Generates a robust emergency transport plan considering alternatives and cost impacts.")
async def emergency_plan_post(request: EmergencyPlanRequest, db: Session = Depends(get_db)):
    try:
        plan = plan_emergency(
            transport_type=request.transport_type,
            severity=request.severity,
            origin=request.origin,
            destination=request.destination,
            cargo_value=request.cargo_value,
            current_delay_hrs=request.current_delay_hrs,
        )
        crud.save_emergency_plan(db, {
            "shipment_id": None,
            "recommended_carrier": plan.get("recommended_action", ""),
            "recommended_route": "Alternative",
            "alternative_route": "Fallback",
            "estimated_recovery_days": 2.5,
            "full_plan": plan
        })
        return plan
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/api/emergency-plan", response_model=EmergencyPlanResponse, tags=["Emergency Planning"], summary="Generate Emergency Transport Plan via GET", description="Generates an emergency transport plan using query parameters.")
def emergency_plan_get(
    transport_type: str = Query("Ocean", description="Mode of transport", examples=["Ocean"]),
    severity: str = Query("high", description="Severity of delay", examples=["high"]),
    origin: str = Query("Mumbai", description="Origin port/city", examples=["Mumbai"]),
    destination: str = Query("Delhi", description="Destination port/city", examples=["Delhi"]),
    cargo_value: float = Query(1000000.0, description="Value of the cargo in INR", examples=[1000000.0]),
    current_delay_hrs: float = Query(24.0, description="Current delay in hours", examples=[24.0]),
    db: Session = Depends(get_db)
):
    try:
        plan = plan_emergency(
            transport_type=transport_type,
            severity=severity,
            origin=origin,
            destination=destination,
            cargo_value=cargo_value,
            current_delay_hrs=current_delay_hrs,
        )
        crud.save_emergency_plan(db, {
            "shipment_id": None,
            "recommended_carrier": plan.get("recommended_action", ""),
            "recommended_route": "Alternative",
            "alternative_route": "Fallback",
            "estimated_recovery_days": 2.5,
            "full_plan": plan
        })
        return plan
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/api/emergency-plan/pdf", tags=["Emergency Planning"], summary="Download Emergency Plan PDF", description="Generates and returns an emergency transport plan as a downloadable PDF document.")
async def emergency_plan_pdf(request: EmergencyPlanRequest, db: Session = Depends(get_db)):
    try:
        plan = plan_emergency(
            transport_type=request.transport_type,
            severity=request.severity,
            origin=request.origin,
            destination=request.destination,
            cargo_value=request.cargo_value,
            current_delay_hrs=request.current_delay_hrs,
        )
        crud.save_emergency_plan(db, {
            "shipment_id": None,
            "recommended_carrier": plan.get("recommended_action", ""),
            "recommended_route": "Alternative",
            "alternative_route": "Fallback",
            "estimated_recovery_days": 2.5,
            "full_plan": plan
        })
        pdf_buffer = generate_emergency_pdf(plan)
        return StreamingResponse(
            pdf_buffer, 
            media_type="application/pdf", 
            headers={"Content-Disposition": "attachment; filename=Emergency_Recovery_Plan.pdf"}
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

# ──────────────────────────────────────────────────────────────────────────────
# RISK ASSESSMENT API
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/api/risk-assess", response_model=RiskAssessResponse, tags=["Analytics"], summary="Assess Shipment Risk", description="Evaluates risk factors based on origin, destination, mode, and cargo type.")
async def risk_assess_post(request: RiskAssessRequest):
    try:
        return assess_risk(
            origin=request.origin,
            destination=request.destination,
            mode=request.mode,
            cargo_type=request.cargo_type,
            cargo_value=request.cargo_value,
            route_region=request.route_region,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/api/risk-assess", response_model=RiskAssessResponse, tags=["Analytics"], summary="Assess Shipment Risk via GET", description="Evaluates risk factors using query parameters.")
def risk_assess_get(
    origin: str = Query("Mumbai", description="Origin city/port", examples=["Mumbai"]),
    destination: str = Query("Delhi", description="Destination city/port", examples=["Delhi"]),
    mode: str = Query("Ocean", description="Transport mode", examples=["Ocean"]),
    cargo_type: str = Query("Electronics", description="Type of cargo", examples=["Electronics"]),
    cargo_value: float = Query(1000000.0, description="Value of the cargo", examples=[1000000.0]),
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
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def get_landing(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="landing.html"
    )


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def get_main_dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"active_page": "dashboard"},
    )

@app.get("/shipment-delay", response_class=HTMLResponse, include_in_schema=False)
def get_shipment_delay(request: Request):
    return templates.TemplateResponse(
        request=request, name="shipment_delay.html",
        context={"active_page": "shipment_delay"},
    )

@app.get("/emergency-transport", response_class=HTMLResponse, include_in_schema=False)
def get_emergency_transport(request: Request):
    return templates.TemplateResponse(
        request=request, name="emergency_transport.html",
        context={"active_page": "emergency_transport"},
    )

@app.get("/hs-classifier", response_class=HTMLResponse, include_in_schema=False)
def get_hs_classifier(request: Request):
    return templates.TemplateResponse(
        request=request, name="hs_classifier.html",
        context={"active_page": "hs_classifier"},
    )

@app.get("/risk-assessment", response_class=HTMLResponse, include_in_schema=False)
def get_risk_assessment(request: Request):
    return templates.TemplateResponse(
        request=request, name="risk_assessment.html",
        context={"active_page": "risk_assessment"},
    )

@app.get("/shipment-tracking", response_class=HTMLResponse, include_in_schema=False)
def get_shipment_tracking(request: Request):
    return templates.TemplateResponse(
        request=request, name="shipment_tracking.html",
        context={"active_page": "shipment_tracking"},
    )

if __name__ == "__main__":
    print("=" * 60)
    print("  LogiSPARK AI Logistics Platform  –  Starting…")
    print("  Dashboard →  http://127.0.0.1:8000")
    print("=" * 60)
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
