from sqlalchemy.orm import Session
from database import models
from typing import List, Dict, Any

def get_shipment(db: Session, shipment_id: str):
    return db.query(models.Shipment).filter(models.Shipment.shipment_id == shipment_id).first()

def get_all_shipments(db: Session):
    return db.query(models.Shipment).all()

def get_active_shipments_count(db: Session):
    return db.query(models.Shipment).filter(models.Shipment.status != "Delivered").count()

def create_shipment(db: Session, data: Dict[str, Any]):
    db_item = models.Shipment(**data)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def save_prediction(db: Session, data: Dict[str, Any]):
    db_item = models.DelayPrediction(**data)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_predictions(db: Session):
    return db.query(models.DelayPrediction).all()

def save_emergency_plan(db: Session, data: Dict[str, Any]):
    db_item = models.EmergencyPlan(**data)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def save_hs_classification(db: Session, query: str, predicted_hs_code: str, confidence: float):
    db_item = models.HSClassificationHistory(query=query, predicted_hs_code=predicted_hs_code, confidence=confidence)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_recent_hs_classifications(db: Session, limit: int = 5):
    return db.query(models.HSClassificationHistory).order_by(models.HSClassificationHistory.created_at.desc()).limit(limit).all()

def save_conversation(db: Session, session_id: str, user_message: str, assistant_response: str):
    db_item = models.AIConversation(session_id=session_id, user_message=user_message, assistant_response=assistant_response)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_conversation_history(db: Session, session_id: str):
    return db.query(models.AIConversation).filter(models.AIConversation.session_id == session_id).order_by(models.AIConversation.created_at.asc()).all()
