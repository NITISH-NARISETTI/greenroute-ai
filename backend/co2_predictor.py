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
        """
        Predict CO₂ emissions for a single route segment
        
        Args:
            distance: Distance in kilometers
            vehicle_type: Type of vehicle ('car', 'van', 'truck', 'bike')
            cargo_weight: Cargo weight in kilograms
            avg_speed: Average speed in km/h
            
        Returns:
            Predicted CO₂ emissions in kg
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        # Encode vehicle type
        vehicle_encoded = VEHICLE_TYPE_ENCODING.get(vehicle_type.lower(), 1)  # default to van
        
        # Prepare features in the exact order expected by the model
        # Feature order: [distance, vehicle_type, cargo_weight, avg_speed]
        features = np.array([[distance, vehicle_encoded, cargo_weight, avg_speed]])
        
        # Predict CO₂ emissions
        prediction = self.model.predict(features)[0]
        
        # Ensure non-negative prediction
        return max(0.0, float(prediction))
    
    def predict_batch(
        self,
        distances: List[float],
        vehicle_type: str,
        cargo_weight: float,
        avg_speed: float
    ) -> List[float]:
        """
        Predict CO₂ emissions for multiple route segments with same vehicle parameters
        
        Args:
            distances: List of distances in kilometers
            vehicle_type: Type of vehicle
            cargo_weight: Cargo weight in kilograms
            avg_speed: Average speed in km/h
            
        Returns:
            List of predicted CO₂ emissions in kg
        """
        return [
            self.predict_co2(dist, vehicle_type, cargo_weight, avg_speed)
            for dist in distances
        ]


# Singleton instance
_predictor_instance = None

def get_co2_predictor(model_path: str = "co2_model.pkl") -> CO2Predictor:
    """Get or create CO2 predictor singleton instance"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = CO2Predictor(model_path)
    return _predictor_instance
