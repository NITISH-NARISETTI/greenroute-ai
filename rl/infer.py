"""
RL Inference Module
Uses trained PPO model to optimize delivery routes
"""
import os
import numpy as np
from typing import List
from stable_baselines3 import PPO
from rl.env import DeliveryEnv

# Default model path
DEFAULT_MODEL_PATH = "rl_models/ppo_delivery_route"

# Global model cache
_model_cache = None


def load_rl_model(model_path: str = DEFAULT_MODEL_PATH) -> PPO:
    """
    Load trained RL model
    
    Args:
        model_path: Path to trained model
        
    Returns:
        Loaded PPO model
    """
    global _model_cache
    
    if _model_cache is not None:
        return _model_cache
    
    if not os.path.exists(f"{model_path}.zip"):
        raise FileNotFoundError(
            f"RL model not found at {model_path}.zip. "
            "Please train the model first using rl/train_ppo.py"
        )
    
    try:
        _model_cache = PPO.load(model_path)
        print(f"RL model loaded successfully from {model_path}")
        return _model_cache
    except Exception as e:
        raise RuntimeError(f"Failed to load RL model: {e}")


def optimize_route_with_rl(
    co2_matrix: np.ndarray,
    start_index: int = 0,
    model_path: str = DEFAULT_MODEL_PATH,
    deterministic: bool = True
) -> List[int]:
    """
    Optimize delivery route using trained RL model
    
    Args:
        co2_matrix: NxN CO₂ cost matrix
        start_index: Starting location index
        model_path: Path to trained model
        deterministic: Use deterministic policy (recommended for inference)
        
    Returns:
        Optimized route as list of location indices
    """
    # Load model
    model = load_rl_model(model_path)
    
    # Create environment with the given CO₂ matrix
    env = DeliveryEnv(co2_matrix=co2_matrix, start_index=start_index)
    
    # Run episode with trained policy
    obs, info = env.reset()
    
    # SHAPE VALIDATION: Ensure model can handle this number of locations
    # (FastAPI/Render fix: prevent 18s timeouts on shape mismatch)
    expected_shape = model.observation_space.shape
    if obs.shape != expected_shape:
        raise ValueError(
            f"Observation shape {obs.shape} does not match model's expected shape {expected_shape}. "
            f"This model was likely trained for {expected_shape[0]-1} locations."
        )

    done = False
    max_steps = len(co2_matrix) * 2  # Safety limit
    steps = 0
    
    while not done and steps < max_steps:
        # Predict next action
        action, _states = model.predict(obs, deterministic=deterministic)
        
        # Execute action
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        steps += 1
    
    # Get optimized route
    optimized_route = env.get_route()
    
    # Close environment
    env.close()
    
    return optimized_route


def optimize_route_greedy(co2_matrix: np.ndarray, start_index: int = 0) -> List[int]:
    """
    Greedy baseline: always choose nearest unvisited location
    Used as fallback if RL model is not available
    
    Args:
        co2_matrix: NxN CO₂ cost matrix
        start_index: Starting location index
        
    Returns:
        Route as list of location indices
    """
    n = len(co2_matrix)
    route = [start_index]
    visited = {start_index}
    current = start_index
    
    while len(visited) < n:
        # Find unvisited location with minimum CO₂ cost
        min_cost = float('inf')
        next_location = None
        
        for j in range(n):
            if j not in visited:
                cost = co2_matrix[current][j]
                if cost < min_cost:
                    min_cost = cost
                    next_location = j
        
        if next_location is not None:
            route.append(next_location)
            visited.add(next_location)
            current = next_location
        else:
            break
    
    return route


def optimize_route_with_fallback(
    co2_matrix: np.ndarray,
    start_index: int = 0,
    use_rl: bool = True
) -> List[int]:
    """
    Optimize route with RL, falling back to greedy if RL fails
    
    Args:
        co2_matrix: NxN CO₂ cost matrix
        start_index: Starting location index
        use_rl: Whether to attempt RL optimization
        
    Returns:
        Optimized route as list of location indices
    """
    if use_rl:
        try:
            return optimize_route_with_rl(co2_matrix, start_index)
        except Exception as e:
            print(f"Warning: RL optimization failed ({e}), using greedy fallback")
            return optimize_route_greedy(co2_matrix, start_index)
    else:
        return optimize_route_greedy(co2_matrix, start_index)
