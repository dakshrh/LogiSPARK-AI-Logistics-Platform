import io
import os
import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from .predictor import ShipmentPredictor
from .report_generator import generate_pdf_report

router = APIRouter()
predictor = ShipmentPredictor()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

@router.get("/api/shipments")
def get_shipments():
    return predictor.get_all_shipments()

@router.get("/api/stats")
def get_global_stats():
    return predictor.get_summary_stats()

@router.get("/predict/{shipment_id}")
def predict_shipment(shipment_id: str):
    try:
        return predictor.predict(shipment_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predict/{shipment_id}/json")
def export_json(shipment_id: str):
    return predictor.predict(shipment_id)

@router.get("/predict/{shipment_id}/excel")
def export_excel(shipment_id: str):
    res = predictor.predict(shipment_id)
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

@router.get("/predict/{shipment_id}/pdf")
def export_pdf(shipment_id: str):
    res = predictor.predict(shipment_id)
    out_path = os.path.join(REPORTS_DIR, f"Delay_Report_{shipment_id}.pdf")
    generate_pdf_report(res, out_path)
    return FileResponse(out_path, filename=f"Delay_Report_{shipment_id}.pdf", media_type="application/pdf")
