import os
import pandas as pd
import numpy as np

os.makedirs('data', exist_ok=True)
np.random.seed(42)

n_records = 1100
shipment_ids = [f"SH{i}" for i in range(100, 100 + n_records)]

origins = ["Port of Shanghai", "Port of Singapore", "Port of Rotterdam", "Port of Los Angeles", "Port of Hamburg", "Port of Mumbai", "Port of Tokyo", "Port of Newark"]
destinations = ["Port of Mumbai", "Port of Hamburg", "Port of Dubai", "Port of Sydney", "Port of London", "Port of New York", "Port of Singapore", "Port of Shanghai"]
carriers = ["Oceanic Link", "Global Trans", "Swift Logistics", "Atlas Freight", "Apex Cargo"]
modes = ["Ocean", "Air", "Road", "Rail"]
container_types = ["Standard", "Reefer", "Dry Van", "Open Top", "Flat Rack"]
tiers = ["Tier 1", "Tier 2", "Tier 3"]

# --- shipments.csv ---
shipment_data = []
for s_id in shipment_ids:
    org = np.random.choice(origins)
    dest = np.random.choice([d for d in destinations if d != org])
    
    if s_id == "SH110":
        org = "Port of Shanghai"
        dest = "Port of Los Angeles"
        carrier = "Oceanic Link"
        mode = "Ocean"
        distance = 10500
        cargo_value = 5000000 
        container_type = "Reefer"
        customer_tier = "Tier 1"
    else:
        carrier = np.random.choice(carriers)
        mode = np.random.choice(modes)
        distance = int(np.random.randint(500, 15000))
        cargo_value = int(np.random.randint(50000, 10000000))
        container_type = np.random.choice(container_types)
        customer_tier = np.random.choice(tiers, p=[0.2, 0.3, 0.5])
        
    departure_days = np.random.randint(1, 30)
    scheduled_departure = f"2026-06-{departure_days:02d}T08:00:00"
    speed_kph = 50 if mode == "Ocean" else (800 if mode == "Air" else (70 if mode == "Road" else 60))
    duration_hours = distance / speed_kph
    arrival_day = departure_days + int(duration_hours // 24)
    arrival_hour = int(duration_hours % 24)
    if arrival_day > 30: arrival_day = 30
    scheduled_arrival = f"2026-06-{arrival_day:02d}T{arrival_hour:02d}:00:00"

    shipment_data.append({
        "shipment_id": s_id, "origin": org, "destination": dest, "carrier": carrier,
        "mode": mode, "scheduled_departure": scheduled_departure, "scheduled_arrival": scheduled_arrival,
        "distance_km": distance, "cargo_value": cargo_value, "container_type": container_type,
        "customer_tier": customer_tier
    })
pd.DataFrame(shipment_data).to_csv("data/shipments.csv", index=False)

# --- weather_data.csv ---
weather_data = []
for s_id in shipment_ids:
    if s_id == "SH110":
        weather_score = 15  # Severe weather
        rainfall = 120
        storm_risk = 0.95
        visibility = 1.2
    else:
        weather_score = int(np.random.randint(40, 100))
        rainfall = int(np.random.randint(0, 50))
        storm_risk = round(float(np.random.uniform(0.0, 0.4)), 2)
        visibility = round(float(np.random.uniform(5.0, 10.0)), 1)
    weather_data.append({"shipment_id": s_id, "weather_score": weather_score, "rainfall": rainfall, "storm_risk": storm_risk, "visibility": visibility})
pd.DataFrame(weather_data).to_csv("data/weather_data.csv", index=False)

# --- traffic_data.csv ---
traffic_data = []
for s_id in shipment_ids:
    if s_id == "SH110":
        traffic_index = 30
        road_closure = 0
        congestion_level = "Low"
    else:
        traffic_index = int(np.random.randint(10, 80))
        road_closure = int(np.random.choice([0, 1], p=[0.95, 0.05]))
        congestion_level = "High" if traffic_index > 75 else ("Medium" if traffic_index > 40 else "Low")
    traffic_data.append({"shipment_id": s_id, "traffic_index": traffic_index, "road_closure": road_closure, "congestion_level": congestion_level})
pd.DataFrame(traffic_data).to_csv("data/traffic_data.csv", index=False)

# --- port_data.csv ---
port_data = []
for s_id in shipment_ids:
    if s_id == "SH110":
        port_congestion = 40
        berth_wait_hours = 12.0
        vessel_queue = 5
    else:
        port_congestion = int(np.random.randint(10, 70))
        berth_wait_hours = round(float(np.random.uniform(0.0, 24.0)), 1)
        vessel_queue = int(np.random.randint(0, 15))
    port_data.append({"shipment_id": s_id, "port_congestion": port_congestion, "berth_wait_hours": berth_wait_hours, "vessel_queue": vessel_queue})
pd.DataFrame(port_data).to_csv("data/port_data.csv", index=False)

# --- customs_data.csv ---
customs_data = []
for s_id in shipment_ids:
    if s_id == "SH110":
        customs_clearance_time = 8.0
        documentation_errors = 0
        inspection_required = 0
    else:
        customs_clearance_time = round(float(np.random.uniform(1.0, 24.0)), 1)
        documentation_errors = int(np.random.choice([0, 1, 2], p=[0.8, 0.15, 0.05]))
        inspection_required = int(np.random.choice([0, 1], p=[0.9, 0.1]))
    customs_data.append({"shipment_id": s_id, "customs_clearance_time": customs_clearance_time, "documentation_errors": documentation_errors, "inspection_required": inspection_required})
pd.DataFrame(customs_data).to_csv("data/customs_data.csv", index=False)

print("Generated 1100 realistic shipments and matching datasets.")
