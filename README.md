# 🌱 GreenRoute - CO₂ Optimized Delivery Routing

**Final Year Academic Project**

An intelligent delivery routing system that minimizes CO₂ emissions using Machine Learning and Reinforcement Learning.

---

## 📌 Project Overview

GreenRoute is a full-stack application that:
- ✅ Accepts delivery addresses from users
- ✅ Converts addresses to geographic coordinates using geocoding
- ✅ Predicts CO₂ emissions using a pre-trained ML model
- ✅ Optimizes visiting order using Reinforcement Learning (PPO)
- ✅ Visualizes optimized routes on an interactive map

---

## 🧱 Technology Stack

### Backend
- **Python 3** - Core programming language
- **FastAPI** - Modern web framework for APIs
- **scikit-learn** - Machine learning model (CO₂ prediction)
- **stable-baselines3** - Reinforcement learning (PPO algorithm)
- **Gymnasium** - RL environment framework

### Frontend
- **HTML5** - Structure
- **CSS3** - Modern styling with glassmorphism
- **Vanilla JavaScript** - Dynamic interactions
- **Leaflet.js** - Interactive map visualization

### APIs
- **OpenStreetMap Nominatim** - Geocoding service

---

## 📂 Project Structure

```
greenroute/
├── api/
│   └── main.py                 # FastAPI server
├── backend/
│   ├── geocoding.py           # Address → Coordinates
│   ├── distance.py            # Haversine distance calculation
│   ├── co2_predictor.py       # ML-based CO₂ prediction
│   ├── co2_matrix.py          # CO₂ cost matrix builder
│   └── optimizer.py           # Route optimization logic
├── rl/
│   ├── env.py                 # Custom Gymnasium environment
│   ├── train_ppo.py           # PPO training script
│   └── infer.py               # RL inference for optimization
├── frontend/
│   ├── index.html             # Main UI
│   ├── styles.css             # Modern CSS styling
│   └── main.js                # Frontend logic
├── co2_model.pkl              # Pre-trained ML model
├── rl_models/                 # Trained RL models (generated)
├── requirements.txt           # Python dependencies
├── .env                       # Environment configuration
└── README.md                  # This file
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser
- Internet connection (for geocoding)

### Option 1: Using run.bat (Windows - Recommended)
```bash
run.bat
```
This will automatically:
- Create virtual environment
- Install dependencies
- Start the API server

### Option 2: Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start API server
python api/main.py
```

Server will start at `http://localhost:8000`

### Open Frontend
Open `frontend/index.html` in your web browser

---

## 🎯 How to Use

1. **Enter Starting Address** - Your delivery depot/warehouse
2. **Add Delivery Stops** - Click "+ Add Stop" to add multiple destinations
3. **Configure Vehicle** - Select vehicle type (car/van/truck/bike)
4. **Set Parameters** - Cargo weight and average speed
5. **Optimize Route** - Click "Optimize Route" button
6. **View Results** - See optimized route on map with metrics

### Example Addresses (US-based)
```
Start: 1600 Amphitheatre Parkway, Mountain View, CA
Stop 1: 1 Infinite Loop, Cupertino, CA
Stop 2: 1 Apple Park Way, Cupertino, CA
Stop 3: 500 Oracle Parkway, Redwood City, CA
```

---

## 🧠 System Architecture

### 1️⃣ Geocoding
- Uses **OpenStreetMap Nominatim API**
- Converts human-readable addresses to (latitude, longitude)
- Implements rate limiting (1 request/second)

### 2️⃣ Distance Calculation
- **Haversine formula** for great-circle distance
- Computes NxN distance matrix for all location pairs

### 3️⃣ CO₂ Prediction (ML)
- **Supervised Learning Model** (scikit-learn)
- Input features: distance, vehicle type, cargo weight, speed
- Output: CO₂ emissions in kg
- Model file: `co2_model.pkl`

### 4️⃣ CO₂ Cost Matrix
- For N locations, builds NxN matrix
- Each entry: `CO₂(i → j) = ML_predict(distance, vehicle, cargo, speed)`

### 5️⃣ Route Optimization (RL)
- **Proximal Policy Optimization (PPO)** algorithm
- Custom Gymnasium environment (`DeliveryEnv`)
- **State**: current location + visited mask
- **Action**: select next unvisited location
- **Reward**: `-CO₂_cost(current → next)`
- Trained on random CO₂ matrices for generalization

### 6️⃣ Visualization
- **Leaflet.js** for interactive maps
- Numbered markers for route sequence
- Polyline showing optimized path
- Metrics panel with distance, CO₂, time, cost

---

## 📊 API Endpoints

### `POST /optimize`
Optimize delivery route to minimize CO₂ emissions.

**Request:**
```json
{
  "start_address": "1600 Amphitheatre Parkway, Mountain View, CA",
  "destination_addresses": [
    "1 Infinite Loop, Cupertino, CA",
    "1 Apple Park Way, Cupertino, CA"
  ],
  "vehicle_type": "van",
  "cargo_weight": 500,
  "avg_speed": 50
}
```

**Response:**
```json
{
  "success": true,
  "message": "Route optimized successfully",
  "route": [
    {
      "address": "...",
      "latitude": 37.4220,
      "longitude": -122.0841,
      "sequence": 0
    }
  ],
  "metrics": {
    "total_distance_km": 45.2,
    "total_co2_kg": 12.5,
    "total_time_hours": 0.9,
    "estimated_cost_usd": 40.6,
    "num_stops": 2
  }
}
```

### `POST /geocode`
Geocode a single address (for testing).

### `GET /health`
Health check endpoint.

### `GET /docs`
Interactive API documentation (Swagger UI).

---

## 🔬 RL Model Training Details

### PPO Configuration
- **Algorithm**: Proximal Policy Optimization
- **Policy Network**: MLP (Multi-Layer Perceptron)
- **Training Environments**: 4 parallel environments
- **Total Timesteps**: 100,000
- **Learning Rate**: 0.0003
- **Gamma**: 0.99
- **Training Time**: ~5-10 minutes on modern CPU

---

## 🎨 Frontend Features

- ✨ **Modern Dark Theme** with glassmorphism effects
- 🎯 **Dynamic Form** with add/remove delivery stops
- 🗺️ **Interactive Map** with custom markers
- 📊 **Real-time Metrics** display
- 🎭 **Smooth Animations** and transitions
- 📱 **Responsive Design** for mobile/tablet
- ⚡ **Fast Performance** with vanilla JavaScript

---

## 🔒 Constraints & Limitations

### What This System Does NOT Use:
- ❌ No hardcoded coordinates
- ❌ No dummy/fake routes
- ❌ No elevation data
- ❌ No weather APIs
- ❌ No Node.js or frontend frameworks
- ❌ No React/Vue/Angular

### Current Limitations:
- Geocoding rate limited to 1 request/second (Nominatim policy)
- Simple cost estimation model
- No real-time traffic data

---

## 🧪 Testing

### Test the System
```bash
python test_system.py
```

### Test API Endpoint
```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "start_address": "New York, NY",
    "destination_addresses": ["Boston, MA", "Philadelphia, PA"],
    "vehicle_type": "van",
    "cargo_weight": 500,
    "avg_speed": 50
  }'
```

---

## 📈 Future Enhancements

- [ ] Real-time traffic integration
- [ ] Weather-based CO₂ adjustments
- [ ] Multi-vehicle routing
- [ ] Time window constraints
- [ ] Driver break scheduling
- [ ] Historical route analytics
- [ ] Mobile app version

---

## 🤝 Contributing

This is an academic project. For educational purposes only.

---

## 📄 License

Academic Project - For Educational Use

---

## 👨‍💻 Author

Final Year Project - 2026

---

## 🙏 Acknowledgments

- OpenStreetMap for geocoding services
- Stable-Baselines3 team for RL framework
- Leaflet.js for mapping library
- FastAPI for modern Python web framework

---

## 📞 Troubleshooting

### Common Issues:

**1. Geocoding fails**
- Check internet connection
- Nominatim has rate limits (1 req/sec)

**2. RL model not found**
- Run: `python rl/train_ppo.py`
- System will use greedy fallback

**3. Import errors**
- Run: `pip install -r requirements.txt`

**4. API not starting**
- Check port 8000 is available
- Verify all dependencies installed

---

**Built with ❤️ using Machine Learning & Reinforcement Learning**
