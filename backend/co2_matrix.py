"""
CO₂ Cost Matrix Generator
Builds NxN matrix of CO₂ emissions between all location pairs
"""
import numpy as np
from typing import List, Tuple
from backend.distance import calculate_distance_matrix
from backend.co2_predictor import get_co2_predictor

def build_co2_matrix(
    coordinates: List[Tuple[float, float]],
    vehicle_type: str,
    cargo_weight: float,
    avg_speed: float
) -> np.ndarray:
    """
    Build CO₂ cost matrix for all pairs of locations
    """
    n = len(coordinates)
    distance_matrix = calculate_distance_matrix(coordinates)
    predictor = get_co2_predictor()
    
    # Flatten the NxN into a list for batch processing
    # We only care about i != j
    to_predict = []
    indices = []
    
    for i in range(n):
        for j in range(n):
            if i != j:
                to_predict.append(distance_matrix[i][j])
                indices.append((i, j))
    
    # Single batch prediction for EVERYTHING
    results = predictor.predict_batch(
        distances=to_predict,
        vehicle_type=vehicle_type,
        cargo_weight=cargo_weight,
        avg_speed=avg_speed
    )
    
    # Reconstruct matrix
    co2_matrix = np.zeros((n, n))
    for idx, (i, j) in enumerate(indices):
        co2_matrix[i][j] = results[idx]
    
    return co2_matrix


def get_total_co2_for_route(
    co2_matrix: np.ndarray,
    route_order: List[int]
) -> float:
    """
    Calculate total CO₂ emissions for a given route order
    
    Args:
        co2_matrix: NxN CO₂ cost matrix
        route_order: Ordered list of location indices
        
    Returns:
        Total CO₂ emissions in kg
    """
    total_co2 = 0.0
    
    for i in range(len(route_order) - 1):
        current_idx = route_order[i]
        next_idx = route_order[i + 1]
        total_co2 += co2_matrix[current_idx][next_idx]
    
    return total_co2
