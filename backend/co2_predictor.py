"""
CO₂ Emission Predictor using pre-trained ML model
Loads co2_model.pkl and predicts emissions for route segments
"""
import pickle
import os
import numpy as np
from typing import Union, List

# Vehicle type encoding (must match training data)
VEHICLE_TYPE_ENCODING = {
    'car': 0,
    'van': 1,
    'truck': 2,
    'bike': 3
}

class CO2Predictor:
    def __init__(self, model_path: str = "co2_model.pkl"):
        """
        Initialize CO2 predictor with pre-trained model
        
        Args:
            model_path: Path to the pickled scikit-learn model
        """
        self.model_path = model_path
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the pre-trained model from pickle file"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"CO2 model not found at {self.model_path}. "
                "Please ensure co2_model.pkl is in the project root."
            )
        
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            print(f"[OK] CO2 model loaded successfully from {self.model_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to load CO2 model: {e}")
    
    def predict_co2(
        self, 
        distance: float, 
        vehicle_type: str, 
        cargo_weight: float, 
        avg_speed: float
    ) -> float:
        """Predict CO₂ for a single segment (uses batch internally for efficiency)"""
        return self.predict_batch([distance], vehicle_type, cargo_weight, avg_speed)[0]
    
    def predict_batch(
        self,
        distances: List[float],
        vehicle_type: str,
        cargo_weight: float,
        avg_speed: float
    ) -> List[float]:
        """
        Predict CO₂ emissions for multiple route segments in one go (VERY FAST)
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        if not distances:
            return []

        # Encode vehicle type once
        vehicle_encoded = VEHICLE_TYPE_ENCODING.get(vehicle_type.lower(), 1)
        
        # Build feature matrix for all distances at once
        # Shape: (len(distances), 4)
        features = np.zeros((len(distances), 4))
        features[:, 0] = distances
        features[:, 1] = vehicle_encoded
        features[:, 2] = cargo_weight
        features[:, 3] = avg_speed
        
        # Batch Predict
        predictions = self.model.predict(features)
        
        # Ensure non-negative and convert to float list
        return [max(0.0, float(p)) for p in predictions]


# Singleton instance
_predictor_instance = None

def get_co2_predictor(model_path: str = "co2_model.pkl") -> CO2Predictor:
    """Get or create CO2 predictor singleton instance"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = CO2Predictor(model_path)
    return _predictor_instance
