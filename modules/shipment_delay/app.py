import io
import os
import pandas as pd
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Path, Depends
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.database import get_db
from database import crud
from .predictor import ShipmentPredictor
from .report_generator import generate_pdf_report

router = APIRouter()
predictor = ShipmentPredictor()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# ──────────────────────────────────────────────────────────────────────────────
# PYDANTIC MODELS
# ──────────────────────────────────────────────────────────────────────────────

class ShipmentItem(BaseModel):
    shipment_id: str = Field(..., description="Unique identifier for the shipment", examples=["LS1001"])
    origin: str = Field(..., description="Origin port or city", examples=["Mumbai"])
    destination: str = Field(..., description="Destination port or city", examples=["Rotterdam"])
    mode: str = Field(..., description="Mode of transport", examples=["Ocean"])
    customer_tier: str = Field(..., description="Tier of the customer", examples=["Platinum"])
    # Using extra allows for other fields
    class Config:
        extra = "allow"

class ShipmentStatsResponse(BaseModel):
    total_savings_generated: float = Field(..., description="Total cost savings generated in INR", examples=[1250000.0])
    potential_loss_prevented: float = Field(..., description="Total potential loss prevented in INR", examples=[5000000.0])
    avg_delay_reduction_hrs: float = Field(..., description="Average delay reduction in hours")
    critical_alerts: int = Field(..., description="Number of critical alerts currently active", examples=[15])
    high_risk_shipments: int = Field(..., description="Number of high risk shipments", examples=[42])
    roi_generated_pct: int = Field(..., description="ROI generated percentage")
    cause_distribution: Dict[str, int] = Field(..., description="Distribution of delay causes")

class ShipmentInformation(BaseModel):
    shipment_id: str
    origin: str
    destination: str
    carrier: str
    transport_mode: str
    weight_kg: float
    cargo_value: float

class PredictionDetails(BaseModel):
    delay_probability: float
    predicted_delay_days: float
    confidence: float
    risk_level: str
    status: str

class ETAAnalysis(BaseModel):
    original_eta_date: str
    original_eta_day: str
    predicted_eta_date: str
    predicted_eta_day: str
    additional_days: float
    on_time_probability: float

class ContributingFactor(BaseModel):
    factor: str
    impact_percentage: float

class RootCauseAnalysis(BaseModel):
    primary_cause: str
    secondary_cause: str
    contributing_factors: List[ContributingFactor]

class RouteAnalysis(BaseModel):
    current_route: str
    distance_km: float
    route_risk_score: float
    congestion_level: str
    customs_risk: str

class CarrierAnalysis(BaseModel):
    current_carrier: str
    carrier_reliability: float
    historical_average_delay: float
    carrier_score: float

class CostImpactAnalysis(BaseModel):
    estimated_delay_cost: float
    storage_cost: float
    sla_penalty: float
    operational_loss: float
    total_estimated_loss: float

class AIRecommendation(BaseModel):
    recommended_action: str
    expected_days_saved: float
    additional_cost: float
    potential_savings: float

class AlternativeRoute(BaseModel):
    route_name: str
    eta_days: float
    risk_score: float
    cost: float
    advantage: str

class TimelineEvent(BaseModel):
    event: str
    date: str
    status: str

class ShipmentPredictionResponse(BaseModel):
    shipment_id: str = Field(..., description="Shipment ID", examples=["LS1001"])
    origin: str = Field(..., description="Origin", examples=["Mumbai"])
    destination: str = Field(..., description="Destination", examples=["Rotterdam"])
    carrier: str = Field(..., description="Carrier name")
    mode: str = Field(..., description="Transport mode", examples=["Ocean"])
    cargo_value: int = Field(..., description="Cargo value")
    container_type: str = Field(..., description="Container type")
    customer_tier: str = Field(..., description="Customer Tier", examples=["Platinum"])
    distance_km: int = Field(..., description="Distance in km")
    scheduled_departure: str = Field(..., description="Scheduled departure date")
    scheduled_arrival: str = Field(..., description="Scheduled arrival date")
    delay_probability: float = Field(..., description="Probability of delay as a percentage", examples=[78.5])
    risk_level: str = Field(..., description="Risk level")
    urgency: str = Field(..., description="Urgency level", examples=["High"])
    predicted_delay_hours: float = Field(..., description="Predicted delay in hours", examples=[48.5])
    root_cause: str = Field(..., description="Predicted root cause of delay", examples=["Port Congestion"])
    ai_summary: str = Field(..., description="AI narrative summary")
    advanced_root_cause: Dict[str, Any] = Field(..., description="Advanced root cause metrics")
    factor_contributions: Dict[str, int] = Field(..., description="Contributions of factors to delay")
    delay_classification: Dict[str, Any] = Field(..., description="Classification of the delay")
    financial_breakdown: Dict[str, Any] = Field(..., description="Financial impact of the delay")
    recommendation_v2: Dict[str, Any] = Field(..., description="AI recommendations for mitigating the delay")
    health_scores: Dict[str, int] = Field(..., description="Health scores for various factors")
    priority_matrix: Dict[str, Any] = Field(..., description="Priority metrics and action deadlines")

    # New nested models for Enterprise Engine
    shipment_information: ShipmentInformation
    prediction_details: PredictionDetails
    eta_analysis: ETAAnalysis
    root_cause_analysis: RootCauseAnalysis
    route_analysis: RouteAnalysis
    carrier_analysis: CarrierAnalysis
    cost_impact_analysis: CostImpactAnalysis
    ai_recommendation_engine: AIRecommendation
    alternative_routes: List[AlternativeRoute]
    timeline_engine: List[TimelineEvent]
    ai_insights: str

# ──────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/api/shipments", response_model=List[ShipmentItem], tags=["Analytics"], summary="List All Shipments", description="Retrieve a list of all active shipments being monitored by the platform.")
def get_shipments(db: Session = Depends(get_db)):
    db_shipments = crud.get_all_shipments(db)
    result = []
    for s in db_shipments:
        result.append({
            "shipment_id": s.shipment_id,
            "origin": s.origin,
            "destination": s.destination,
            "mode": s.mode or "Ocean",
            "customer_tier": s.customer_tier or "Standard"
        })
    # Also blend predictor shipments for demo
    pred_shipments = predictor.get_all_shipments()
    return result + pred_shipments

@router.get("/api/stats", response_model=ShipmentStatsResponse, tags=["Analytics"], summary="Get Global Analytics Stats", description="Retrieve global predictive analytics and financial savings statistics.")
def get_global_stats(db: Session = Depends(get_db)):
    # Keep predictor stats for logic
    base = predictor.get_summary_stats()
    return base

@router.get("/predict/{shipment_id}", response_model=ShipmentPredictionResponse, tags=["Delay Prediction"], summary="Predict Shipment Delay", description="Get AI-powered delay predictions and recommendations for a specific shipment.")
def predict_shipment(shipment_id: str = Path(..., description="The ID of the shipment to predict", examples=["LS1001"]), db: Session = Depends(get_db)):
    try:
        res = predictor.predict(shipment_id, db)
        # Store in DB
        crud.save_prediction(db, {
            "shipment_id": shipment_id,
            "predicted_delay_days": res.get("predicted_delay_hours", 0) / 24.0,
            "delay_probability": res.get("delay_probability", 0),
            "primary_cause": res.get("root_cause", ""),
            "confidence": res.get("prediction_details", {}).get("confidence"),
            "risk_level": res.get("prediction_details", {}).get("risk_level"),
            "estimated_loss": res.get("cost_impact_analysis", {}).get("total_estimated_loss"),
            "recommended_action": res.get("ai_recommendation_engine", {}).get("recommended_action"),
            "predicted_eta": res.get("eta_analysis", {}).get("predicted_eta_date"),
            "full_prediction": res
        })
        return res
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predict/{shipment_id}/json", response_model=ShipmentPredictionResponse, tags=["Delay Prediction"], summary="Predict Shipment Delay (JSON Export)", description="Export the shipment delay prediction as a JSON object.")
def export_json(shipment_id: str = Path(..., description="The ID of the shipment to predict", examples=["LS1001"]), db: Session = Depends(get_db)):
    try:
        return predict_shipment(shipment_id=shipment_id, db=db)
    except HTTPException:
        raise

@router.get("/predict/{shipment_id}/excel", tags=["Delay Prediction"], summary="Export Prediction to Excel", description="Generate and download an Excel report containing the delay prediction details.")
def export_excel(shipment_id: str = Path(..., description="The ID of the shipment to predict", examples=["LS1001"]), db: Session = Depends(get_db)):
    try:
        res = predictor.predict(shipment_id, db)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    flat = {
        "Shipment ID": res["shipment_id"],
        "Origin": res["origin"],
        "Destination": res["destination"],
        "Mode": res["mode"],
        "Customer Tier": res["customer_tier"],
        "Delay Probability (%)": res["delay_probability"],
        "Urgency": res["urgency"],
        "Root Cause": res["root_cause"],
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
    return StreamingResponse(
        output, headers=headers,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

@router.get("/predict/{shipment_id}/pdf", tags=["Delay Prediction"], summary="Export Prediction to PDF", description="Generate and download a PDF report containing the delay prediction details.")
def export_pdf(shipment_id: str = Path(..., description="The ID of the shipment to predict", examples=["LS1001"]), db: Session = Depends(get_db)):
    try:
        res = predictor.predict(shipment_id, db)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    out_path = os.path.join(REPORTS_DIR, f"Delay_Report_{shipment_id}.pdf")
    generate_pdf_report(res, out_path)
    return FileResponse(out_path, filename=f"Delay_Report_{shipment_id}.pdf", media_type="application/pdf")
