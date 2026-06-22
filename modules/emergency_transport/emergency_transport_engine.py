"""
Emergency Transport Engine
==========================
Simulated logistics disruption response engine.
Provides alternate carrier suggestions, emergency route recommendations,
ETA impact, cost impact, and risk-level assessment for P1 logistics failures.
"""

import random
import math
from datetime import datetime, timedelta


# ── Carrier Database ────────────────────────────────────────────────────────
_CARRIERS = {
    "Air": [
        {"name": "IndiGo Cargo Express",  "reliability": 97, "cost_multiplier": 3.2, "eta_days": 1},
        {"name": "Blue Dart Aviation",     "reliability": 95, "cost_multiplier": 3.0, "eta_days": 1},
        {"name": "Air India Cargo",        "reliability": 91, "cost_multiplier": 2.8, "eta_days": 2},
        {"name": "FedEx Air Priority",     "reliability": 98, "cost_multiplier": 3.8, "eta_days": 1},
    ],
    "Ocean": [
        {"name": "MSC Emergency Slot",    "reliability": 88, "cost_multiplier": 1.6, "eta_days": 5},
        {"name": "Maersk Spot Booking",   "reliability": 91, "cost_multiplier": 1.8, "eta_days": 4},
        {"name": "COSCO Express",         "reliability": 85, "cost_multiplier": 1.5, "eta_days": 6},
        {"name": "Evergreen Priority",    "reliability": 89, "cost_multiplier": 1.7, "eta_days": 5},
    ],
    "Road": [
        {"name": "BlueDart Surface",      "reliability": 94, "cost_multiplier": 1.3, "eta_days": 2},
        {"name": "DTDC Express Road",     "reliability": 90, "cost_multiplier": 1.2, "eta_days": 3},
        {"name": "Delhivery Priority",    "reliability": 92, "cost_multiplier": 1.4, "eta_days": 2},
        {"name": "Ecom Express Fleet",   "reliability": 88, "cost_multiplier": 1.1, "eta_days": 3},
    ],
    "Rail": [
        {"name": "Indian Railways Parcel Express", "reliability": 82, "cost_multiplier": 0.9, "eta_days": 4},
        {"name": "Double-Stack Rail",    "reliability": 84, "cost_multiplier": 0.95, "eta_days": 5},
        {"name": "Container Express Rail", "reliability": 87, "cost_multiplier": 1.0, "eta_days": 4},
    ],
}

_EMERGENCY_ROUTES = {
    "Mumbai":     ["JNPT Alternate Gate", "Mumbai Air Cargo Complex", "Nhava Sheva Express"],
    "Delhi":      ["TKD Rail Hub", "Delhi Air Cargo Terminal", "NH-48 Truck Corridor"],
    "Chennai":    ["Ennore Port", "Chennai Air Cargo", "ECR Coastal Highway"],
    "Kolkata":    ["Haldia Dock", "Kolkata Air Cargo", "NH-12 Express Route"],
    "Bangalore":  ["KIA Cargo Hub", "Bangalore ICD", "NH-275 Fast Lane"],
    "default":    ["Alternate Port Gateway", "Air Freight Hub", "Cross-Dock Facility"],
}

_ACTIONS = {
    "critical": {
        "action": "Immediate Air Freight Diversion",
        "description": "Critical delay detected. Divert entire shipment to air freight to meet SLA. Pre-book emergency slots.",
        "savings_pct": 0.75,
        "risk_after": "Low",
    },
    "high": {
        "action": "Priority Alternate Carrier Booking",
        "description": "High-severity delay. Book priority slot with alternate carrier. Notify customer of revised ETA.",
        "savings_pct": 0.60,
        "risk_after": "Medium",
    },
    "medium": {
        "action": "Route Optimization & Carrier Upgrade",
        "description": "Moderate delay. Upgrade to express tier and optimize route via alternate corridor.",
        "savings_pct": 0.45,
        "risk_after": "Low",
    },
    "low": {
        "action": "Monitor & Standby Alert",
        "description": "Low impact. Enable real-time monitoring. Trigger escalation if delay exceeds threshold.",
        "savings_pct": 0.20,
        "risk_after": "Low",
    },
}

# ── Seeded determinism for demo consistency ─────────────────────────────────
def _seed(transport_type: str, severity: str) -> int:
    return sum(ord(c) for c in (transport_type + severity))


# ══════════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════════
def plan_emergency(
    transport_type: str = "Ocean",
    severity: str = "high",
    origin: str = "Mumbai",
    destination: str = "Delhi",
    cargo_value: float = 1_000_000.0,
    current_delay_hrs: float = 24.0,
) -> dict:
    """
    Generate an emergency transport response plan.

    Parameters
    ----------
    transport_type : "Air" | "Ocean" | "Road" | "Rail"
    severity       : "critical" | "high" | "medium" | "low"
    origin         : origin city / port
    destination    : destination city / port
    cargo_value    : cargo value in INR
    current_delay_hrs : estimated current delay in hours

    Returns
    -------
    Full emergency response plan dict
    """
    severity = severity.lower()
    if severity not in _ACTIONS:
        severity = "high"
    if transport_type not in _CARRIERS:
        transport_type = "Ocean"

    rng = random.Random(_seed(transport_type, severity))

    # ── Carrier suggestions ──────────────────────────────────────────────
    carrier_pool = _CARRIERS.get(transport_type, _CARRIERS["Ocean"])
    # Suggest top 5 carriers, sorted by reliability × (1/cost)
    sorted_carriers = sorted(
        carrier_pool,
        key=lambda c: c["reliability"] / c["cost_multiplier"],
        reverse=True,
    )[:5]

    base_cost_per_day = cargo_value * 0.002
    carrier_suggestions = []
    for i, c in enumerate(sorted_carriers):
        cost = round(base_cost_per_day * c["cost_multiplier"] * c["eta_days"], 0)
        eta_hrs = c["eta_days"] * 24 - rng.randint(2, 8)
        delay_reduction = round(max(0, current_delay_hrs - (c["eta_days"] * 24 * 0.3)), 1)
        
        # New ranking factors
        hist_perf = rng.randint(85, 99)
        dis_risk = rng.choice(["Low", "Medium", "High"])
        w_risk = rng.choice(["Clear", "Minor Warning", "Storm Alert"])
        p_cong = rng.choice(["Normal", "Elevated", "Severe"])
        c_delays = rng.choice(["None", "12-24h", "24-48h"])
        
        carrier_suggestions.append({
            "rank": i + 1,
            "name": c["name"],
            "reliability": c["reliability"],
            "estimated_cost": int(cost),
            "eta_hours": eta_hrs,
            "delay_reduction_hrs": delay_reduction,
            "recommended": i == 0,
            "historical_performance": f"{hist_perf}%",
            "disruption_risk": dis_risk,
            "weather_risk": w_risk,
            "port_congestion": p_cong,
            "customs_delays": c_delays
        })

    # ── Emergency routes ─────────────────────────────────────────────────
    origin_key = next((k for k in _EMERGENCY_ROUTES if k.lower() in origin.lower()), "default")
    routes_raw = _EMERGENCY_ROUTES[origin_key]
    
    # Generate Advanced Routes
    route_types = ["Primary Route", "Alternative Route A", "Alternative Route B", "Emergency Route"]
    emergency_routes = []
    
    for i in range(4):
        route_name = route_types[i]
        path_name = routes_raw[i % len(routes_raw)]
        
        distance = rng.randint(300, 1500) + (i * 150)
        risk_pct = rng.randint(15, 45) if i == 0 else rng.randint(35, 80)
        congestion = rng.randint(10, 30) if i == 0 else rng.randint(40, 90)
        cost_impact = round(base_cost_per_day * (0.8 + i * 0.3), 0)
        eta_impact = round(current_delay_hrs * (0.4 + i * 0.2), 1)
        
        emergency_routes.append({
            "type": route_name,
            "path": path_name,
            "distance_km": distance,
            "risk_pct": risk_pct,
            "congestion_score": congestion,
            "cost_impact": int(cost_impact),
            "eta_impact_hrs": eta_impact,
            "is_recommended": i == 0,
        })

    # ── Action plan ──────────────────────────────────────────────────────
    action_data = _ACTIONS[severity]
    estimated_loss = round(cargo_value * 0.004 * current_delay_hrs / 24, 2)
    savings = round(estimated_loss * action_data["savings_pct"], 2)
    impl_cost = round(base_cost_per_day * 0.5, 2)
    net_benefit = round(savings - impl_cost, 2)

    # ── ETA Impact ───────────────────────────────────────────────────────
    original_eta = datetime.now() + timedelta(days=5)
    revised_eta = datetime.now() + timedelta(hours=carrier_suggestions[0]["eta_hours"])
    delay_reduction_pct = round((1 - carrier_suggestions[0]["eta_hours"] / (current_delay_hrs + 72)) * 100, 1)

    # ── Risk Levels ──────────────────────────────────────────────────────
    severity_map = {"critical": "Critical", "high": "High", "medium": "Medium", "low": "Low"}
    severity_colors = {"Critical": "#ef4444", "High": "#f59e0b", "Medium": "#3b82f6", "Low": "#10b981"}
    current_risk_label = severity_map[severity]

    return {
        "transport_type": transport_type,
        "severity": severity,
        "severity_label": current_risk_label,
        "severity_color": severity_colors[current_risk_label],
        "origin": origin,
        "destination": destination,
        "cargo_value": int(cargo_value),
        "current_delay_hrs": current_delay_hrs,
        "recommended_action": action_data["action"],
        "action_description": action_data["description"],
        "risk_level_after": action_data["risk_after"],
        "estimated_loss": estimated_loss,
        "estimated_savings": savings,
        "implementation_cost": impl_cost,
        "net_benefit": net_benefit,
        "carrier_suggestions": carrier_suggestions,
        "emergency_routes": emergency_routes,
        "eta_impact": {
            "original_eta": original_eta.strftime("%Y-%m-%d %H:%M"),
            "revised_eta": revised_eta.strftime("%Y-%m-%d %H:%M"),
            "delay_reduction_pct": delay_reduction_pct,
            "delay_reduction_hrs": round(current_delay_hrs * action_data["savings_pct"], 1),
        },
        "ai_narrative": (
            f"P1 Logistics Alert: {transport_type} shipment from {origin} to {destination} "
            f"facing {current_delay_hrs}h delay ({current_risk_label} severity). "
            f"Recommended: {action_data['action']}. "
            f"Estimated savings: ₹{int(savings):,} with {round(action_data['savings_pct']*100)}% delay reduction. "
            f"Top carrier: {carrier_suggestions[0]['name']} (Reliability: {carrier_suggestions[0]['reliability']}%)."
        ),
    }
