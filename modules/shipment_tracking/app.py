from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List
from sqlalchemy.orm import Session

from database.database import get_db
from database import crud

router = APIRouter(prefix="/api/track-shipment", tags=["Shipment Tracking"])

# ──────────────────────────────────────────────────────────────────────────────
# PYDANTIC MODELS
# ──────────────────────────────────────────────────────────────────────────────

class ShipmentInsights(BaseModel):
    delay_probability: str = Field(..., description="Probability of delay", examples=["78%"])
    risk_factors: List[str] = Field(..., description="List of risk factors", examples=[["Port Congestion at destination"]])
    recommended_actions: List[str] = Field(..., description="Recommended actions", examples=[["Notify customer"]])
    carrier_performance: str = Field(..., description="Carrier performance this month", examples=["88% on-time this month"])
    alternative_plan: str = Field(..., description="Alternative plan if delay occurs", examples=["Divert to Antwerp"])

class ShipmentTrackingResponse(BaseModel):
    shipment_id: str = Field(..., description="Shipment ID", examples=["LS1001"])
    status: str = Field(..., description="Current status of the shipment", examples=["In Transit"])
    current_location: str = Field(..., description="Current location", examples=["Suez Canal"])
    eta: str = Field(..., description="Estimated Time of Arrival", examples=["2026-06-25"])
    delay_risk: str = Field(..., description="Risk of delay", examples=["High"])
    carrier: str = Field(..., description="Carrier name", examples=["Maersk"])
    route: str = Field(..., description="Route description", examples=["Mumbai -> Rotterdam"])
    timeline_step: int = Field(..., description="Current step in the timeline (1-6)", examples=[2])
    insights: ShipmentInsights = Field(..., description="AI insights regarding the shipment")

# ──────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/", response_model=ShipmentTrackingResponse, summary="Track Shipment", description="Retrieve tracking details and AI insights for a specific shipment.")
def track_shipment(shipment_id: str = Query(..., description="The ID of the shipment to track", examples=["LS1001"]), db: Session = Depends(get_db)):
    if not shipment_id:
        raise HTTPException(status_code=400, detail="Shipment ID required")
    
    shipment_id = shipment_id.upper()
    db_shipment = crud.get_shipment(db, shipment_id)
    if db_shipment:
        # Map db_shipment to response dict
        data = {
            "shipment_id": db_shipment.shipment_id,
            "status": db_shipment.status or "Unknown",
            "current_location": db_shipment.current_location or "Unknown",
            "eta": db_shipment.eta or "Pending",
            "delay_risk": db_shipment.risk_score or "Low",
            "carrier": db_shipment.carrier or "Unknown",
            "route": f"{db_shipment.origin} -> {db_shipment.destination}",
            "timeline_step": db_shipment.timeline_step or 1,
            "insights": db_shipment.insights or {
                "delay_probability": "0%",
                "risk_factors": ["None"],
                "recommended_actions": ["None"],
                "carrier_performance": "Unknown",
                "alternative_plan": "None"
            }
        }
        return data
    else:
        raise HTTPException(status_code=404, detail="Shipment not found")
