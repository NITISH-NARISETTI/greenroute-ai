"""
Distance calculation using Haversine formula
Computes great-circle distance between two geographic coordinates
"""
import math
from typing import Tuple, List

# Earth's radius in kilometers
EARTH_RADIUS_KM = 6371.0

def haversine_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula
    
    Args:
        coord1: Tuple of (latitude, longitude) for first point
        coord2: Tuple of (latitude, longitude) for second point
        
    Returns:
        Distance in kilometers
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    lon1_rad = math.radians(lon1)
    lon2_rad = math.radians(lon2)
    
    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    distance = EARTH_RADIUS_KM * c
    
    return distance


def calculate_distance_matrix(coordinates: List[Tuple[float, float]]) -> List[List[float]]:
    """
    Calculate pairwise distance matrix for a list of coordinates
    
    Args:
        coordinates: List of (latitude, longitude) tuples
        
    Returns:
        NxN matrix where entry [i][j] is distance from point i to point j in km
    """
    n = len(coordinates)
    distance_matrix = [[0.0 for _ in range(n)] for _ in range(n)]
    
    for i in range(n):
        for j in range(n):
            if i != j:
                distance_matrix[i][j] = haversine_distance(coordinates[i], coordinates[j])
    
    return distance_matrix
