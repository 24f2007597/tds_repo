import json
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List

file_path = 'q-vercel-latency.json'

class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

# --- FastAPI App Setup ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/vercel")
async def vercel_latency(request_data: LatencyRequest):
    try:
        with open(file_path, 'r') as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        return JSONResponse(status_code=500, content={"error": f"Data file not found at path: {file_path}"})
    except json.JSONDecodeError:
        return JSONResponse(status_code=500, content={"error": "Could not parse the JSON data file."})

    metrics = []
    threshold = request_data.threshold_ms

    for region in request_data.regions:
        # Filter data for the current region
        region_data = [entry for entry in existing_data if entry.get("region") == region]

        # FIX #3: Handle cases where a region has no data
        if not region_data:
            metrics.append({"region": region, "error": "No data found for this region."})
            continue

        # FIX #2: Create a latency list for this specific region for correct P95 calculation
        region_latency_list = [entry["latency"] for entry in region_data]
        
        breaches = sum(1 for latency in region_latency_list if latency > threshold)
        
        avg_latency = sum(region_latency_list) / len(region_latency_list)
        p95_latency = np.percentile(region_latency_list, 95)
        
        uptime_list = [entry.get("uptime", 0) for entry in region_data]
        avg_uptime = sum(uptime_list) / len(uptime_list)

        metrics.append({
            "region": region,
            "avg_latency": round(avg_latency, 2),
            "avg_uptime": round(avg_uptime, 2),
            "p95_latency": round(p95_latency, 2),
            "breaches": breaches
        })

    return {"metrics": metrics}