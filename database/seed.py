from sqlalchemy.orm import Session
from database.database import engine, Base
from database import models

def seed_db(db: Session):
    # Only seed if empty
    if db.query(models.Shipment).first():
        return
    
    mock_shipments = [
        {
            "shipment_id": "LS1001",
            "status": "In Transit",
            "current_location": "Suez Canal",
            "eta": "2026-06-25",
            "delay_probability": "High",
            "risk_score": "High",
            "carrier": "Maersk",
            "origin": "Mumbai",
            "destination": "Rotterdam",
            "timeline_step": 2,
            "insights": {
                "delay_probability": "78%",
                "risk_factors": ["Port Congestion at destination", "Weather warning in Mediterranean"],
                "recommended_actions": ["Prepare alternate clearance port", "Notify customer of potential delay"],
                "carrier_performance": "88% on-time this month",
                "alternative_plan": "Divert to Antwerp if Rotterdam delay > 48h"
            }
        },
        {
            "shipment_id": "LS1002",
            "status": "At Customs",
            "current_location": "Port of Los Angeles",
            "eta": "2026-06-23",
            "delay_probability": "Medium",
            "risk_score": "Medium",
            "carrier": "COSCO",
            "origin": "Shanghai",
            "destination": "Los Angeles",
            "timeline_step": 3,
            "insights": {
                "delay_probability": "45%",
                "risk_factors": ["Customs inspection backlog"],
                "recommended_actions": ["Expedite document review", "Contact local broker"],
                "carrier_performance": "92% on-time this month",
                "alternative_plan": "Use priority rail terminal post-clearance"
            }
        },
        {
            "shipment_id": "LS1003",
            "status": "Delivered",
            "current_location": "Frankfurt Warehouse",
            "eta": "Delivered",
            "delay_probability": "Low",
            "risk_score": "Low",
            "carrier": "DHL Air",
            "origin": "Delhi",
            "destination": "Frankfurt",
            "timeline_step": 6,
            "insights": {
                "delay_probability": "0%",
                "risk_factors": ["None"],
                "recommended_actions": ["None"],
                "carrier_performance": "98% on-time this month",
                "alternative_plan": "None"
            }
        },
        {
            "shipment_id": "LS1004",
            "status": "Booked",
            "current_location": "Chennai ICD",
            "eta": "2026-07-01",
            "delay_probability": "Low",
            "risk_score": "Low",
            "carrier": "Evergreen",
            "origin": "Chennai",
            "destination": "Singapore",
            "timeline_step": 1,
            "insights": {
                "delay_probability": "12%",
                "risk_factors": ["Vessel delay at previous port"],
                "recommended_actions": ["Monitor vessel position"],
                "carrier_performance": "85% on-time this month",
                "alternative_plan": "Shift to later vessel if delayed > 2 days"
            }
        },
        {
            "shipment_id": "LS1005",
            "status": "Out for Delivery",
            "current_location": "Local Depot, London",
            "eta": "2026-06-22",
            "delay_probability": "Low",
            "risk_score": "Low",
            "carrier": "UPS",
            "origin": "Heathrow",
            "destination": "Central London",
            "timeline_step": 5,
            "insights": {
                "delay_probability": "5%",
                "risk_factors": ["Local traffic"],
                "recommended_actions": ["Provide live tracking link to customer"],
                "carrier_performance": "96% on-time this month",
                "alternative_plan": "None"
            }
        }
    ]
    
    for s in mock_shipments:
        db.add(models.Shipment(**s))
        
    mock_carriers = [
        {"carrier_name": "Maersk", "reliability_score": 88.0, "average_delay": 2.5, "cost_per_kg": 1.2},
        {"carrier_name": "COSCO", "reliability_score": 92.0, "average_delay": 1.8, "cost_per_kg": 1.0},
        {"carrier_name": "DHL Air", "reliability_score": 98.0, "average_delay": 0.5, "cost_per_kg": 5.5},
        {"carrier_name": "Evergreen", "reliability_score": 85.0, "average_delay": 3.0, "cost_per_kg": 1.1},
        {"carrier_name": "UPS", "reliability_score": 96.0, "average_delay": 0.8, "cost_per_kg": 4.8},
    ]
    for c in mock_carriers:
        db.add(models.Carrier(**c))
        
    db.commit()
