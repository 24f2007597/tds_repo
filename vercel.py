from fastapi import FastAPI
import json
import numpy as np
from fastapi.middleware.cors import CORSMiddleware

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

@app.post("/vercel")
async def vercel_latency(data: dict):
    with open(file_path, 'r') as file:
        existing_data = json.load(file)

    metrics = []
    threshold = data["threshold"]

    for region in data["regions"]:
        sum_latency, count_latency, sum_uptime, count_uptime, breaches = 0, 0, 0, 0, 0
        latency_list = [entry["latency"] for entry in existing_data if entry["region"] in data["regions"]]
        region_data = [entry for entry in existing_data if entry["region"] == region]
        for entry in region_data:
            latency = entry["latency"]
            uptime = entry["uptime"]
            sum_latency += latency
            count_latency += 1
            sum_uptime += uptime
            count_uptime += 1
            if latency > threshold:
                breaches += 1

        avg_latency = sum_latency / count_latency
        avg_uptime = sum_uptime / count_uptime
        p95_latency = np.percentile(latency_list, 95)

        metrics.append({
            "region": region,
            "avg_latency": avg_latency,
            "avg_uptime": avg_uptime,
            "p95_latency": p95_latency,
            "breaches": breaches
        })

    return {"metrics": metrics}