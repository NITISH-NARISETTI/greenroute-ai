"""
GreenRoute FastAPI Backend
Main API server for CO₂-optimized delivery routing
"""
import os
import sys
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
import numpy as np
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.geocoding import get_geocoder
from backend.co2_matrix import build_co2_matrix
from backend.optimizer import optimize_delivery_route, calculate_route_metrics

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="GreenRoute API",
    description="CO₂-Optimized Delivery Routing System",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class OptimizeRequest(BaseModel):
    """Request model for route optimization"""
    start_address: str = Field(..., description="Starting address")
    destination_addresses: List[str] = Field(..., description="List of delivery addresses")
    vehicle_type: str = Field(default="van", description="Vehicle type: car, van, truck, bike")
    cargo_weight: float = Field(default=500.0, description="Cargo weight in kg")
    avg_speed: float = Field(default=50.0, description="Average speed in km/h")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "start_address": "1600 Amphitheatre Parkway, Mountain View, CA",
                "destination_addresses": [
                    "1 Infinite Loop, Cupertino, CA",
                    "1 Apple Park Way, Cupertino, CA",
                    "500 Oracle Parkway, Redwood City, CA"
                ],
                "vehicle_type": "van",
                "cargo_weight": 500,
                "avg_speed": 50
            }
        }
    )


class LocationInfo(BaseModel):
    """Location information with coordinates"""
    address: str
    latitude: float
    longitude: float
    sequence: int


class OptimizeResponse(BaseModel):
    """Response model for route optimization"""
    success: bool
    message: str
    route: List[LocationInfo]
    metrics: dict
    co2_matrix: Optional[List[List[float]]] = None


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/optimize", response_model=OptimizeResponse)
async def optimize_route(request: OptimizeRequest):
    """
    Optimize delivery route to minimize CO₂ emissions
    
    Process:
    1. Geocode all addresses to coordinates
    2. Calculate distance matrix
    3. Build CO₂ cost matrix using ML model
    4. Optimize route sequence using RL
    5. Return optimized route with metrics
    """
    try:
        # Validate input
        if not request.destination_addresses:
            raise HTTPException(
                status_code=400,
                detail="At least one destination address is required"
            )
        
        if request.vehicle_type.lower() not in ['car', 'van', 'truck', 'bike']:
            raise HTTPException(
                status_code=400,
                detail="Invalid vehicle type. Must be: car, van, truck, or bike"
            )
        
        # Step 1: Geocode addresses
        import time
        t0 = time.time()
        geocoder = get_geocoder()
        
        all_addresses = [request.start_address] + request.destination_addresses
        coordinates = geocoder.geocode_addresses(all_addresses)
        
        # Check for geocoding failures
        failed_indices = [i for i, coord in enumerate(coordinates) if coord is None]
        if failed_indices:
            failed_addresses = [all_addresses[i] for i in failed_indices]
            raise HTTPException(
                status_code=400,
                detail=f"Failed to geocode addresses: {failed_addresses}"
            )
        
        t1 = time.time()
        print(f"   [TIME] Geocoding took: {t1 - t0:.2f}s")
        
        # Step 2: Build CO2 cost matrix
        co2_matrix = build_co2_matrix(
            coordinates=coordinates,
            vehicle_type=request.vehicle_type,
            cargo_weight=request.cargo_weight,
            avg_speed=request.avg_speed
        )
        t2 = time.time()
        print(f"   [TIME] Matrix Build took: {t2 - t1:.2f}s")
        
        # Step 3: Optimize route using RL
        optimized_order, total_co2 = optimize_delivery_route(
            co2_matrix=co2_matrix,
            start_index=0
        )
        t3 = time.time()
        print(f"   [TIME] RL Optimization took: {t3 - t2:.2f}s")
        
        # Step 4: Calculate comprehensive metrics
        metrics = calculate_route_metrics(
            optimized_order=optimized_order,
            coordinates=coordinates,
            co2_matrix=co2_matrix,
            avg_speed=request.avg_speed
        )
        
        # Step 5: Build response
        route_info = []
        for seq, idx in enumerate(optimized_order):
            lat, lon = coordinates[idx]
            route_info.append(LocationInfo(
                address=all_addresses[idx],
                latitude=lat,
                longitude=lon,
                sequence=seq
            ))
        
        response = OptimizeResponse(
            success=True,
            message=f"Route optimized in {time.time() - t0:.1f}s",
            route=route_info,
            metrics=metrics,
            co2_matrix=co2_matrix.tolist()
        )
        
        print(f"\n[SUCCESS] Total processing time: {time.time() - t0:.2f}s\n")
        
        return response
        
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Model file not found: {str(e)}"
        )
    except Exception as e:
        print(f"\n[ERROR] Error during optimization: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/geocode")
async def geocode_address(address: str):
    """
    Geocode a single address to coordinates
    
    Useful for testing and validation
    """
    try:
        geocoder = get_geocoder()
        coords = geocoder.geocode_address(address)
        
        if coords is None:
            raise HTTPException(
                status_code=404,
                detail=f"Could not geocode address: {address}"
            )
        
        lat, lon = coords
        return {
            "success": True,
            "address": address,
            "latitude": lat,
            "longitude": lon
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Geocoding error: {str(e)}"
        )


# Mount static files for the frontend - Define this LAST to avoid shadowing API routes
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")


# Run server
if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    print("=" * 60)
    print("GreenRoute API Server")
    print("=" * 60)
    print(f"Starting server at http://{host}:{port}")
    print("API Documentation: http://localhost:8000/docs")
    print("=" * 60)
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=True
    )
