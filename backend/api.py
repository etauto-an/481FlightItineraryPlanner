from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from backend.main import compute_itinerary

app = FastAPI(title="Itinerary Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ItineraryRequest(BaseModel):
    start: str
    targets: List[str]
    max_iterations: int = 2000
    time_limit: float = 10.0

class ItineraryResponse(BaseModel):
    path: List[str]
    details: List[Dict[str, Any]]
    cost: float
    total_flight_time: Optional[float] = 0.0  # [New Field]

@app.get("/")
async def root():
    return {"message": "Itinerary Planner API is running."}

@app.post("/itinerary", response_model=ItineraryResponse)
def post_itinerary(req: ItineraryRequest):
    try:
        res = compute_itinerary(req.start, req.targets, max_iterations=req.max_iterations, time_limit=req.time_limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if res is None:
        raise HTTPException(status_code=503, detail="No solution found within limits or graph disconnected")

    path, details, cost = res
    total_time = sum((leg.get("flight_time") or 0) for leg in details)

    return ItineraryResponse(
        path=path, 
        details=details, 
        cost=cost, 
        total_flight_time=total_time
    )