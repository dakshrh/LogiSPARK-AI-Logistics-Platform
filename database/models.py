from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON
from datetime import datetime
from database.database import Base

class Shipment(Base):
    __tablename__ = "shipments"
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(String, unique=True, index=True)
    origin = Column(String)
    destination = Column(String)
    carrier = Column(String)
    weight = Column(Float, nullable=True)
    status = Column(String)
    current_location = Column(String)
    eta = Column(String)
    delay_probability = Column(String)
    risk_score = Column(String)
    timeline_step = Column(Integer, default=1)
    insights = Column(JSON, nullable=True)
    mode = Column(String, default="Ocean")
    customer_tier = Column(String, default="Standard")
    created_at = Column(DateTime, default=datetime.utcnow)

class Carrier(Base):
    __tablename__ = "carriers"
    id = Column(Integer, primary_key=True, index=True)
    carrier_name = Column(String, unique=True, index=True)
    reliability_score = Column(Float)
    average_delay = Column(Float)
    cost_per_kg = Column(Float)
    active = Column(Boolean, default=True)

class Route(Base):
    __tablename__ = "routes"
    id = Column(Integer, primary_key=True, index=True)
    origin = Column(String)
    destination = Column(String)
    distance = Column(Float)
    estimated_days = Column(Integer)
    risk_score = Column(Float)
    cost = Column(Float)

class DelayPrediction(Base):
    __tablename__ = "delay_predictions"
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(String, index=True)
    predicted_delay_days = Column(Float)
    delay_probability = Column(Float)
    primary_cause = Column(String)
    secondary_cause = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)
    estimated_loss = Column(Float, nullable=True)
    recommended_action = Column(String, nullable=True)
    predicted_eta = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    full_prediction = Column(JSON, nullable=True)

class EmergencyPlan(Base):
    __tablename__ = "emergency_plans"
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(String, index=True, nullable=True)
    recommended_carrier = Column(String)
    recommended_route = Column(String)
    alternative_route = Column(String)
    estimated_recovery_days = Column(Float)
    generated_at = Column(DateTime, default=datetime.utcnow)
    full_plan = Column(JSON, nullable=True)

class HSClassificationHistory(Base):
    __tablename__ = "hs_classification_history"
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True)
    predicted_hs_code = Column(String)
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class AIConversation(Base):
    __tablename__ = "ai_conversations"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    user_message = Column(String)
    assistant_response = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
