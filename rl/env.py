"""
Delivery Route Environment for Reinforcement Learning
Gymnasium environment for optimizing delivery sequences based on CO₂ emissions
"""
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import Optional, Tuple

class DeliveryEnv(gym.Env):
    """
    Custom Gymnasium environment for delivery route optimization
    
    State:
        - current_location: index of current location
        - visited_mask: binary array indicating visited locations
        
    Action:
        - next_location: index of next location to visit (must be unvisited)
        
    Reward:
        - reward = -CO₂_cost(current → next)
        - Episode ends when all locations are visited
    """
    
    metadata = {'render_modes': []}
    
    def __init__(self, co2_matrix: np.ndarray, start_index: int = 0):
        """
        Initialize delivery environment
        
        Args:
            co2_matrix: NxN matrix of CO₂ costs between locations
            start_index: Starting location index
        """
        super().__init__()
        
        self.co2_matrix = co2_matrix
        self.n_locations = len(co2_matrix)
        self.start_index = start_index
        
        # Action space: choose next location (0 to n-1)
        self.action_space = spaces.Discrete(self.n_locations)
        
        # Observation space: current location + visited mask
        # Shape: (n_locations + 1,)
        # First element: current location (normalized to [0, 1])
        # Remaining elements: visited mask (0 or 1)
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(self.n_locations + 1,),
            dtype=np.float32
        )
        
        # Episode state
        self.current_location = None
        self.visited_mask = None
        self.route_history = None
        self.total_co2 = None
        self.steps = None
    
    def reset(self, seed: Optional[int] = None, options: Optional[dict] = None) -> Tuple[np.ndarray, dict]:
        """
        Reset environment to initial state
        
        Returns:
            Initial observation and info dict
        """
        super().reset(seed=seed)
        
        self.current_location = self.start_index
        self.visited_mask = np.zeros(self.n_locations, dtype=np.float32)
        self.visited_mask[self.start_index] = 1.0  # Mark start as visited
        self.route_history = [self.start_index]
        self.total_co2 = 0.0
        self.steps = 0
        
        observation = self._get_observation()
        info = {}
        
        return observation, info
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, dict]:
        """
        Execute one step in the environment
        
        Args:
            action: Index of next location to visit
            
        Returns:
            observation, reward, terminated, truncated, info
        """
        # Validate action
        if action < 0 or action >= self.n_locations:
            # Invalid action - large penalty
            reward = -1000.0
            terminated = True
            truncated = False
            info = {"error": "invalid_action"}
            return self._get_observation(), reward, terminated, truncated, info
        
        # Check if location already visited
        if self.visited_mask[action] == 1.0:
            # Already visited - penalty
            reward = -100.0
            terminated = False
            truncated = False
            info = {"error": "already_visited"}
            return self._get_observation(), reward, terminated, truncated, info
        
        # Valid action - calculate CO₂ cost and move
        co2_cost = self.co2_matrix[self.current_location][action]
        
        # Reward is negative CO₂ cost (we want to minimize CO₂)
        reward = -co2_cost
        
        # Update state
        self.current_location = action
        self.visited_mask[action] = 1.0
        self.route_history.append(action)
        self.total_co2 += co2_cost
        self.steps += 1
        
        # Check if all locations visited
        terminated = (np.sum(self.visited_mask) == self.n_locations)
        truncated = False
        
        info = {
            "co2_cost": co2_cost,
            "total_co2": self.total_co2,
            "route": self.route_history.copy()
        }
        
        observation = self._get_observation()
        
        return observation, reward, terminated, truncated, info
    
    def _get_observation(self) -> np.ndarray:
        """
        Get current observation
        
        Returns:
            Observation array: [normalized_current_location, visited_mask...]
        """
        # Normalize current location to [0, 1]
        normalized_location = self.current_location / max(1, self.n_locations - 1)
        
        # Concatenate current location and visited mask
        observation = np.concatenate([
            [normalized_location],
            self.visited_mask
        ]).astype(np.float32)
        
        return observation
    
    def render(self):
        """Render environment (not implemented)"""
        pass
    
    def get_route(self) -> list:
        """Get current route history"""
        return self.route_history.copy()
    
    def get_total_co2(self) -> float:
        """Get total CO₂ emissions for current route"""
        return self.total_co2


def create_random_co2_matrix(n_locations: int, seed: Optional[int] = None) -> np.ndarray:
    """
    Create random CO₂ cost matrix for training
    
    Args:
        n_locations: Number of locations
        seed: Random seed for reproducibility
        
    Returns:
        NxN CO₂ cost matrix
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Generate random costs between 1 and 100 kg CO₂
    matrix = np.random.uniform(1.0, 100.0, size=(n_locations, n_locations))
    
    # Set diagonal to 0 (no cost to stay at same location)
    np.fill_diagonal(matrix, 0.0)
    
    return matrix
