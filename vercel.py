from fastapi import FastAPI
import json
import numpy as np
from fastapi.middleware.cors import CORSMiddleware
from pydantic import Field, List, BaseModel

file_path = 'q-vercel-latency.json'

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: int = Field(..., alias="threshold")

@app.post("/vercel")
async def vercel_latency(data: LatencyRequest):
    with open(file_path, 'r') as file:
        existing_data = json.load(file)

    metrics = []
    threshold = data.threshold_ms

    for region in data.regions:
        region_data = [entry for entry in existing_data if entry["region"] == region]

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