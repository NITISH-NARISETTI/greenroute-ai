
import requests
import json

def test_local_optimize():
    url = "http://127.0.0.1:8000/optimize"
    payload = {
        "start_address": "Rajiv Gandhi International Airport, Shamshabad, Hyderabad, Telangana 500409, India",
        "destination_addresses": [
            "Cyber Towers, HITEC City Road, Madhapur, Kondapur, Hyderabad, Serilingampalle mandal, Ranga Reddy, Telangana, 500081, India",
            "IKEA Hyderabad, Raidurg, HITEC City, Hyderabad, Telangana 500081, India"
        ],
        "vehicle_type": "van",
        "cargo_weight": 500,
        "avg_speed": 40
    }
    
    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, json=payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS: Optimization complete!")
            print(json.dumps(response.json()['metrics'], indent=2))
        else:
            print(f"FAILED: {response.text}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_local_optimize()
