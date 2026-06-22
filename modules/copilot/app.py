from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session
from database.database import get_db
from database import crud

router = APIRouter(prefix="/api/copilot", tags=["Platform"])

# ──────────────────────────────────────────────────────────────────────────────
# PYDANTIC MODELS
# ──────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str = Field("default-session", description="Conversation session ID")
    message: str = Field(..., description="Message from the user to the Copilot", examples=["Why is my shipment delayed?"])

class ExecutiveDetails(BaseModel):
    name: str = Field(..., description="Name of the executive", examples=["Sarah Jenkins"])
    department: str = Field(..., description="Department of the executive", examples=["VP Logistics"])
    email: str = Field(..., description="Email address", examples=["sarah.j@logispark.com"])
    phone: str = Field(..., description="Phone number", examples=["+1 555-0192"])

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI response text", examples=["Based on my analysis..."])
    show_executive: bool = Field(..., description="Flag to show executive details", examples=[False])
    executive_details: Optional[ExecutiveDetails] = Field(None, description="Executive contact details if escalation is requested")

# ──────────────────────────────────────────────────────────────────────────────
# LOGIC
# ──────────────────────────────────────────────────────────────────────────────

def process_ai_response(db: Session, msg: str) -> dict:
    msg_lower = msg.lower()
    
    # Example logic using DB
    if "delay" in msg_lower or "shipment" in msg_lower:
        # Fetch the most delayed shipment from DB
        preds = crud.get_predictions(db)
        if preds:
            worst = sorted(preds, key=lambda x: x.delay_probability, reverse=True)[0]
            return {
                "response": f"Based on my analysis, shipment {worst.shipment_id} has a {worst.delay_probability}% chance of delay due to {worst.primary_cause}. I recommend reviewing the emergency plans.",
                "show_executive": False
            }
        else:
            return {
                "response": "Currently, there are no recorded shipment delay predictions in the database.",
                "show_executive": False
            }
            
    elif "best carrier" in msg_lower or "germany" in msg_lower:
        return {
            "response": "For Germany (Rotterdam/Antwerp routes), DHL Air and FedEx Air Priority are currently the top-rated carriers with 98% reliability this month.",
            "show_executive": False
        }
    elif "route" in msg_lower:
        return {
            "response": "The current primary route has a 45% risk of congestion. I've generated alternative routes. Would you like to review them in the Emergency Transport module?",
            "show_executive": False
        }
    elif "hs code" in msg_lower:
        # Fetch recent classifications
        recent = crud.get_recent_hs_classifications(db, limit=1)
        if recent:
            return {
                "response": f"I use a Hybrid AI approach. Your recent query '{recent[0].query}' was classified as {recent[0].predicted_hs_code} with {recent[0].confidence}% confidence.",
                "show_executive": False
            }
        else:
            return {
                "response": "I use a Hybrid AI approach combining semantic similarity with domain rules to classify products accurately.",
                "show_executive": False
            }
    elif "executive" in msg_lower or "escalate" in msg_lower:
        return {
            "response": "I have prepared the escalation details for you. Please see the contact card below.",
            "show_executive": True,
            "executive_details": {
                "name": "Sarah Jenkins",
                "department": "VP Logistics",
                "email": "sarah.j@logispark.com",
                "phone": "+1 555-0192"
            }
        }
    else:
        return {
            "response": "I can help you with shipment delays, carrier recommendations, route optimization, HS code classification, and executive escalation. How can I assist you today?",
            "show_executive": False
        }

# ──────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse, summary="Chat with AI Copilot", description="Interact with the LogiSPARK AI Copilot for logistics insights and escalation.")
def copilot_chat(req: ChatRequest, db: Session = Depends(get_db)):
    try:
        reply = process_ai_response(db, req.message)
        
        # Persist conversation
        crud.save_conversation(db, req.session_id, req.message, reply["response"])
        
        return reply
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
