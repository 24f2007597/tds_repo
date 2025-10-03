import json
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from pathlib import Path # Import Path for robust file handling

# --- Configuration ---
# This robustly finds the project root from the api/ directory
# and builds the correct path to the data file.
try:
    BASE_DIR = Path(__file__).resolve().parent.parent
    file_path = BASE_DIR / 'q-vercel-latency.json'
except NameError:
    # Fallback for environments where __file__ is not defined
    file_path = 'q-vercel-latency.json'


# --- Pydantic Models for Automatic Validation ---
class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

# --- FastAPI App Setup ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.post("/vercel")
async def vercel_latency(request_data: LatencyRequest):
    try:
        with open(file_path, 'r') as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        return JSONResponse(status_code=500, content={"error": f"Data file not found. Ensure 'q-vercel-latency.json' is in your project's root directory."})
    except json.JSONDecodeError:
        return JSONResponse(status_code=500, content={"error": "Could not parse the JSON data file."})

    metrics = []
    threshold = request_data.threshold_ms

    for region in request_data.regions:
        region_data = [entry for entry in existing_data if entry.get("region") == region]

        if not region_data:
            metrics.append({"region": region, "error": "No data found for this region."})
            continue

        # --- FINAL FIX for KeyError ---
        # Safely create the list, skipping any entries that are missing a "latency" key.
        region_latency_list = [entry["latency_ms"] for entry in region_data if "latency_ms" in entry]

        # If after filtering, there are no valid latency entries, skip this region.
        if not region_latency_list:
            metrics.append({"region": region, "error": "No valid latency data found for this region."})
            continue
        
        breaches = sum(1 for latency in region_latency_list if latency > threshold)
        
        avg_latency = sum(region_latency_list) / len(region_latency_list)
        p95_latency = np.percentile(region_latency_list, 95)
        
        uptime_list = [entry.get("uptime_pct", 0) for entry in region_data]
        avg_uptime = sum(uptime_list) / len(uptime_list)

        metrics.append({
            "region": region,
            "avg_latency": round(avg_latency, 2),
            "avg_uptime": round(avg_uptime, 2),
            "p95_latency": round(p95_latency, 2),
            "breaches": breaches
        })

    return {"metrics": metrics}