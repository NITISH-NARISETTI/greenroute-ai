"""
Geocoding module using OpenStreetMap Nominatim API
Converts human-readable addresses to geographic coordinates
"""
import os
import time
import re
from typing import Tuple, Optional, List
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from dotenv import load_dotenv

load_dotenv()

class Geocoder:
    def __init__(self):
        self.user_agent = os.getenv("NOMINATIM_USER_AGENT", "greenroute_app_v1")
        self.geolocator = Nominatim(user_agent=self.user_agent, timeout=10)
        self.google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        self.gmaps = None
        
        if self.google_api_key:
            try:
                import googlemaps
                self.gmaps = googlemaps.Client(key=self.google_api_key)
                print("[OK] Google Maps Geocoding enabled.")
            except ImportError:
                print("Warning: 'googlemaps' library not found. Please install it.")
            except Exception as e:
                print(f"Error initializing Google Maps: {e}")
    
    def _clean_address_noise(self, address: str) -> str:
        """
        Remove non-geographic noise like floor numbers, room numbers, 
        and parenthetical notes that confuse geocoders.
        """
        # 1. Remove everything inside parentheses
        address = re.sub(r'\(.*?\)', '', address)
        
        # 2. Remove Floor/Room/Unit/Flat patterns (e.g. "Floor 5", "Flat 2b", "Room 101")
        # Matches keywords followed by numbers/letters until a comma or end of string
        patterns = [
            r'\b(floor|level|room|unit|apt|apartment|flat|suite|block|gate|cabin|cabin no|plot|plot no)\b[\s#]*[a-z0-9-]+',
            r'\b(ground|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+floor\b'
        ]
        
        for pattern in patterns:
            address = re.sub(pattern, '', address, flags=re.IGNORECASE)
            
        # 3. Clean up extra commas and spaces
        address = re.sub(r',\s*,', ',', address) # Double commas
        address = re.sub(r'\s+', ' ', address)   # Double spaces
        
        return address.strip().strip(',')

    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convert address to (latitude, longitude) coordinates
        
        Tries Google Maps first (if configured), then falls back to 
        Nominatim with iterative "peeling" for complex addresses.
        """
        if not address or not address.strip():
            return None
        
        # Normalize: Join multi-lines, strip extra spaces
        clean_address = " ".join(address.split()).strip()
        
        # NEW: Smart Cleaning for non-geographic noise
        smart_cleaned = self._clean_address_noise(clean_address)
        if smart_cleaned != clean_address:
            print(f"   [CLEANED] '{clean_address}' -> '{smart_cleaned}'")
        
        # 1. Try Google Maps if available
        if self.gmaps:
            try:
                # Add slight delay for safety
                time.sleep(0.1)
                result = self.gmaps.geocode(smart_cleaned)
                if result:
                    location = result[0]['geometry']['location']
                    return (location['lat'], location['lng'])
            except Exception as e:
                print(f"Google Maps geocoding error: {e}")
        
        # 2. Try Nominatim with Iterative Peeling
        return self._geocode_nominatim_robust(smart_cleaned)

    def _geocode_nominatim_robust(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Robust Nominatim geocoding using iterative peeling of address parts.
        Useful for detailed addresses with landmarks.
        """
        parts = [p.strip() for p in address.split(',')]
        
        # Strategy: Try full address, then progressively remove the leftmost part
        # e.g. "Cyber Towers, HITEC City, Hyderabad" -> "HITEC City, Hyderabad" -> "Hyderabad"
        for i in range(len(parts)):
            current_search = ", ".join(parts[i:]).strip()
            if not current_search:
                continue
                
            try:
                # Respect Nominatim usage policy
                time.sleep(1)
                location = self.geolocator.geocode(current_search)
                
                if location:
                    if i > 0:
                        print(f"   [NOTICE] Resolved via fallback: '{current_search}'")
                    return (location.latitude, location.longitude)
                
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                print(f"Warning: Geocoder service error for '{current_search}': {e}")
                continue
            except Exception as e:
                print(f"Error: Unexpected error geocoding '{current_search}': {e}")
                continue
        
        print(f"Warning: All geocoding attempts failed for: {address}")
        return None
    
    def geocode_addresses(self, addresses: List[str]) -> List[Optional[Tuple[float, float]]]:
        """
        Batch geocode multiple addresses
        
        Args:
            addresses: List of address strings
            
        Returns:
            List of (latitude, longitude) tuples or None for failed geocoding
        """
        return [self.geocode_address(addr) for addr in addresses]


# Singleton instance
_geocoder_instance = None

def get_geocoder() -> Geocoder:
    """Get or create geocoder singleton instance"""
    global _geocoder_instance
    if _geocoder_instance is None:
        _geocoder_instance = Geocoder()
    return _geocoder_instance
