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
    
    Args:
        coordinates: List of (latitude, longitude) tuples
        vehicle_type: Type of vehicle ('car', 'van', 'truck', 'bike')
        cargo_weight: Cargo weight in kilograms
        avg_speed: Average speed in km/h
        
    Returns:
        NxN numpy array where entry [i][j] is CO₂ cost from location i to j
    """
    n = len(coordinates)
    
    # Step 1: Calculate distance matrix
    distance_matrix = calculate_distance_matrix(coordinates)
    
    # Step 2: Get CO₂ predictor
    predictor = get_co2_predictor()
    
    # Step 3: Build CO₂ matrix
    co2_matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(n):
            if i != j:
                distance = distance_matrix[i][j]
                co2_emission = predictor.predict_co2(
                    distance=distance,
                    vehicle_type=vehicle_type,
                    cargo_weight=cargo_weight,
                    avg_speed=avg_speed
                )
                co2_matrix[i][j] = co2_emission
    
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
