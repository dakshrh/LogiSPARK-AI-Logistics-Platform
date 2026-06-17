"""
Risk Assessment Engine
======================
Multi-factor supply chain risk analysis engine.
Assesses: Operational, Customs, Weather, Port, and Carrier risk.
Produces overall risk score, category, AI recommendations, and mitigation actions.
"""

import random
import math


# ── Risk factor definitions ──────────────────────────────────────────────────
_WEATHER_RISK_REGIONS = {
    "mumbai":     {"base": 55, "season_peak": 80},
    "chennai":    {"base": 50, "season_peak": 75},
    "kolkata":    {"base": 60, "season_peak": 85},
    "delhi":      {"base": 35, "season_peak": 50},
    "bangalore":  {"base": 30, "season_peak": 45},
    "gujarat":    {"base": 45, "season_peak": 70},
    "shanghai":   {"base": 40, "season_peak": 65},
    "singapore":  {"base": 35, "season_peak": 55},
    "dubai":      {"base": 20, "season_peak": 30},
    "london":     {"base": 38, "season_peak": 55},
    "los angeles":{"base": 25, "season_peak": 40},
    "default":    {"base": 40, "season_peak": 60},
}

_PORT_RISK_MAP = {
    "mumbai": 72, "nhava sheva": 68, "chennai": 60, "kolkata": 65,
    "kandla": 55, "cochin": 48, "jnpt": 70, "shanghai": 55,
    "singapore": 30, "dubai": 35, "rotterdam": 25, "hamburg": 28,
    "los angeles": 50, "long beach": 52, "default": 50,
}

_CUSTOMS_RISK_MAP = {
    "Air": 30, "Ocean": 55, "Road": 45, "Rail": 40,
}

_CARRIER_RELIABILITY = {
    "Air": 88, "Ocean": 75, "Road": 82, "Rail": 78,
}

_CARGO_OPERATIONAL_RISK = {
    "Perishable":    85, "Hazardous":     90, "Electronics":  65,
    "Textiles":      40, "Machinery":     55, "Pharmaceuticals": 70,
    "Automotive":    60, "FMCG":          45, "default":      50,
}

_RECOMMENDATIONS = {
    "Critical": [
        "Activate emergency logistics protocol immediately",
        "Engage dedicated risk management team for real-time tracking",
        "Pre-position contingency carriers at origin and destination",
        "Notify all stakeholders and insurance underwriters",
        "Consider multi-modal route segmentation to reduce single-point failure",
    ],
    "High": [
        "Increase shipment monitoring frequency to every 2 hours",
        "Pre-book alternative carriers as standby",
        "Expedite customs documentation to minimize clearance time",
        "Enable real-time GPS tracking with geofence alerts",
        "Conduct pre-shipment weather corridor analysis",
    ],
    "Medium": [
        "Monitor weather and port congestion reports daily",
        "Ensure all documentation is complete before departure",
        "Confirm carrier SLA compliance and service guarantees",
        "Set automated alerts for delay thresholds",
        "Review insurance coverage for identified risk categories",
    ],
    "Low": [
        "Maintain standard monitoring schedule",
        "Confirm carrier on-time performance scores",
        "Ensure customs documents are pre-validated",
        "Standard operational checklist applies",
    ],
}

_MITIGATION_ACTIONS = {
    "weather": [
        "Reroute via weather-safe corridor",
        "Enable satellite weather monitoring",
        "Pre-approve alternate storm-bypass routes",
    ],
    "port": [
        "Pre-register for priority berthing",
        "Activate port congestion alerts",
        "Arrange inland container depot as buffer",
    ],
    "customs": [
        "Submit pre-arrival customs declarations",
        "Engage licensed customs broker for expedited clearance",
        "Verify HS code classification for all cargo items",
    ],
    "operational": [
        "Activate contingency logistics partner",
        "Deploy IoT cargo sensors for real-time condition monitoring",
        "Establish dedicated operations war room",
    ],
    "carrier": [
        "Dual-book with primary and backup carrier",
        "Verify carrier insurance and liability coverage",
        "Confirm vehicle/vessel condition before loading",
    ],
}


# ── Seeded RNG for demo determinism ─────────────────────────────────────────
def _seed(origin: str, destination: str, mode: str) -> int:
    return sum(ord(c) for c in (origin + destination + mode))


def _region_key(location: str) -> str:
    loc = location.lower()
    for key in _WEATHER_RISK_REGIONS:
        if key in loc:
            return key
    return "default"


def _port_key(location: str) -> str:
    loc = location.lower()
    for key in _PORT_RISK_MAP:
        if key in loc:
            return key
    return "default"


# ══════════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════════
def assess_risk(
    origin: str = "Mumbai",
    destination: str = "Delhi",
    mode: str = "Ocean",
    cargo_type: str = "Electronics",
    cargo_value: float = 1_000_000.0,
    route_region: str = "",
) -> dict:
    """
    Assess multi-factor supply chain risk.

    Parameters
    ----------
    origin      : origin city / port
    destination : destination city / port
    mode        : "Air" | "Ocean" | "Road" | "Rail"
    cargo_type  : type of cargo (Perishable, Electronics, etc.)
    cargo_value : cargo value in INR
    route_region: optional route descriptor

    Returns
    -------
    Full risk assessment dict with scores, category, recommendations, mitigations
    """
    rng = random.Random(_seed(origin, destination, mode))

    # ── Weather Risk ─────────────────────────────────────────────────────
    origin_key = _region_key(origin)
    dest_key = _region_key(destination)
    origin_weather = _WEATHER_RISK_REGIONS[origin_key]["base"]
    dest_weather = _WEATHER_RISK_REGIONS[dest_key]["base"]
    weather_score = round((origin_weather + dest_weather) / 2 + rng.uniform(-5, 10), 1)
    weather_score = max(5, min(95, weather_score))

    # ── Port Risk ────────────────────────────────────────────────────────
    origin_port = _PORT_RISK_MAP.get(_port_key(origin), _PORT_RISK_MAP["default"])
    dest_port = _PORT_RISK_MAP.get(_port_key(destination), _PORT_RISK_MAP["default"])
    port_score = round((origin_port * 0.6 + dest_port * 0.4) + rng.uniform(-8, 8), 1)
    port_score = max(5, min(95, port_score))
    if mode in ("Road", "Air"):
        port_score = round(port_score * 0.5, 1)  # road/air reduces port risk

    # ── Customs Risk ─────────────────────────────────────────────────────
    customs_base = _CUSTOMS_RISK_MAP.get(mode, 45)
    customs_score = round(customs_base + rng.uniform(-10, 15), 1)
    customs_score = max(5, min(95, customs_score))

    # ── Carrier Risk ─────────────────────────────────────────────────────
    carrier_rel = _CARRIER_RELIABILITY.get(mode, 80)
    carrier_score = round((100 - carrier_rel) + rng.uniform(-5, 10), 1)
    carrier_score = max(5, min(95, carrier_score))

    # ── Operational Risk ─────────────────────────────────────────────────
    cargo_key = next((k for k in _CARGO_OPERATIONAL_RISK if k.lower() in cargo_type.lower()), "default")
    op_base = _CARGO_OPERATIONAL_RISK[cargo_key]
    op_score = round(op_base + rng.uniform(-10, 10), 1)
    op_score = max(5, min(95, op_score))

    # ── Overall Risk Score ───────────────────────────────────────────────
    # Weighted: Operational 30%, Port 25%, Customs 20%, Weather 15%, Carrier 10%
    overall = round(
        op_score * 0.30
        + port_score * 0.25
        + customs_score * 0.20
        + weather_score * 0.15
        + carrier_score * 0.10,
        1,
    )
    overall = max(5, min(98, overall))

    # ── Risk Category ────────────────────────────────────────────────────
    if overall >= 75:
        category = "Critical"
        category_color = "#ef4444"
        category_badge = "b-red"
    elif overall >= 55:
        category = "High"
        category_color = "#f59e0b"
        category_badge = "b-amber"
    elif overall >= 35:
        category = "Medium"
        category_color = "#3b82f6"
        category_badge = "b-blue"
    else:
        category = "Low"
        category_color = "#10b981"
        category_badge = "b-green"

    # ── Risk Scores dict ─────────────────────────────────────────────────
    risk_scores = {
        "Operational": round(op_score, 1),
        "Port":        round(port_score, 1),
        "Customs":     round(customs_score, 1),
        "Weather":     round(weather_score, 1),
        "Carrier":     round(carrier_score, 1),
    }

    # ── AI Recommendations ───────────────────────────────────────────────
    recommendations = _RECOMMENDATIONS.get(category, _RECOMMENDATIONS["Medium"])

    # ── Mitigation Actions ───────────────────────────────────────────────
    # Select 2 mitigations from each category relevant to top risks
    top_risks = sorted(risk_scores.items(), key=lambda x: x[1], reverse=True)
    mitigation_map_keys = {
        "Weather": "weather", "Port": "port", "Customs": "customs",
        "Operational": "operational", "Carrier": "carrier",
    }
    mitigations = []
    for risk_name, _ in top_risks[:3]:
        key = mitigation_map_keys.get(risk_name, "operational")
        mitigations.extend(_MITIGATION_ACTIONS[key][:2])

    # ── Financial Risk Exposure ──────────────────────────────────────────
    financial_exposure = round(cargo_value * (overall / 100) * 0.08, 2)
    mitigation_potential = round(financial_exposure * 0.65, 2)

    # ── Heatmap data (for radar chart) ──────────────────────────────────
    heatmap = [
        {"factor": k, "score": v, "color": (
            "#ef4444" if v >= 70 else "#f59e0b" if v >= 50 else "#3b82f6" if v >= 30 else "#10b981"
        )}
        for k, v in risk_scores.items()
    ]

    # ── AI Narrative ─────────────────────────────────────────────────────
    top_risk_name, top_risk_val = top_risks[0]
    ai_narrative = (
        f"Supply chain risk assessment for {origin} → {destination} ({mode}) "
        f"yields an Overall Risk Score of {overall}/100 — classified as {category} Risk. "
        f"Primary concern: {top_risk_name} risk at {top_risk_val}/100. "
        f"Estimated financial exposure: ₹{int(financial_exposure):,}. "
        f"Mitigation potential: ₹{int(mitigation_potential):,} savings."
    )

    return {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "cargo_type": cargo_type,
        "cargo_value": int(cargo_value),
        "risk_scores": risk_scores,
        "overall_score": overall,
        "category": category,
        "category_color": category_color,
        "category_badge": category_badge,
        "heatmap": heatmap,
        "recommendations": recommendations,
        "mitigations": list(dict.fromkeys(mitigations)),  # dedupe
        "financial_exposure": financial_exposure,
        "mitigation_potential": mitigation_potential,
        "ai_narrative": ai_narrative,
        "top_risk": {"factor": top_risk_name, "score": top_risk_val},
    }
