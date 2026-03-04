"""
Route Optimizer using Reinforcement Learning
Integrates RL inference to optimize delivery sequence
"""
import numpy as np
from typing import List, Tuple
from rl.infer import optimize_route_with_fallback

def optimize_delivery_route(
    co2_matrix: np.ndarray,
    start_index: int = 0
) -> Tuple[List[int], float]:
    """
    Optimize delivery route using trained RL model
    
    Args:
        co2_matrix: NxN CO₂ cost matrix
        start_index: Index of starting location (default: 1)
        
    Returns:
        Tuple of (optimized_route_order, total_co2_emissions)
    """
    # Use RL inference to get optimized route (with greedy fallback)
    optimized_order = optimize_route_with_fallback(co2_matrix, start_index)
    
    # Calculate total CO₂ for optimized route
    total_co2 = 0.0
    for i in range(len(optimized_order) - 1):
        current_idx = optimized_order[i]
        next_idx = optimized_order[i + 1]
        total_co2 += co2_matrix[current_idx][next_idx]
    
    return optimized_order, total_co2


def calculate_route_metrics(
    optimized_order: List[int],
    coordinates: List[Tuple[float, float]],
    co2_matrix: np.ndarray,
    avg_speed: float
) -> dict:
    """
    Calculate comprehensive metrics for optimized route
    
    Args:
        optimized_order: Optimized sequence of location indices
        coordinates: List of (lat, lon) tuples
        co2_matrix: CO₂ cost matrix
        avg_speed: Average speed in km/h
        
    Returns:
        Dictionary with route metrics
    """
    from backend.distance import haversine_distance
    
    total_distance = 0.0
    total_co2 = 0.0
    
    # Calculate total distance and CO₂
    for i in range(len(optimized_order) - 1):
        current_idx = optimized_order[i]
        next_idx = optimized_order[i + 1]
        
        # Distance
        distance = haversine_distance(
            coordinates[current_idx],
            coordinates[next_idx]
        )
        total_distance += distance
        
        # CO₂
        total_co2 += co2_matrix[current_idx][next_idx]
    
    # Calculate time (hours)
    total_time_hours = total_distance / avg_speed if avg_speed > 0 else 0
    
    # Estimate cost in Indian Rupees (INR)
    # Model: ₹40 per km + ₹1500 per hour
    estimated_cost = (total_distance * 40) + (total_time_hours * 1500)
    
    # Calculate non-optimized (sequential) route for comparison
    sequential_order = list(range(len(coordinates)))  # Just visit in order: 0, 1, 2, 3...
    sequential_distance = 0.0
    sequential_co2 = 0.0
    
    for i in range(len(sequential_order) - 1):
        current_idx = sequential_order[i]
        next_idx = sequential_order[i + 1]
        
        # Distance
        seq_dist = haversine_distance(
            coordinates[current_idx],
            coordinates[next_idx]
        )
        sequential_distance += seq_dist
        
        # CO₂
        sequential_co2 += co2_matrix[current_idx][next_idx]
    
    sequential_time = sequential_distance / avg_speed if avg_speed > 0 else 0
    sequential_cost = (sequential_distance * 40) + (sequential_time * 1500)
    
    # Calculate savings
    distance_saved = sequential_distance - total_distance
    co2_saved = sequential_co2 - total_co2
    time_saved = sequential_time - total_time_hours
    cost_saved = sequential_cost - estimated_cost
    
    # Calculate percentage savings
    distance_saved_pct = (distance_saved / sequential_distance * 100) if sequential_distance > 0 else 0
    co2_saved_pct = (co2_saved / sequential_co2 * 100) if sequential_co2 > 0 else 0
    cost_saved_pct = (cost_saved / sequential_cost * 100) if sequential_cost > 0 else 0
    
    return {
        "total_distance_km": round(total_distance, 2),
        "total_co2_kg": round(total_co2, 2),
        "total_time_hours": round(total_time_hours, 2),
        "estimated_cost_inr": round(estimated_cost, 2),
        "num_stops": len(optimized_order) - 1,
        
        # Comparison with non-optimized route
        "savings": {
            "distance_saved_km": round(distance_saved, 2),
            "co2_saved_kg": round(co2_saved, 2),
            "time_saved_hours": round(time_saved, 2),
            "cost_saved_inr": round(cost_saved, 2),
            "distance_saved_percent": round(distance_saved_pct, 1),
            "co2_saved_percent": round(co2_saved_pct, 1),
            "cost_saved_percent": round(cost_saved_pct, 1)
        }
    }
