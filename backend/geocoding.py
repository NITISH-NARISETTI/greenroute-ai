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
        # Use a more specific user agent to avoid shared-IP blocks
        self.user_agent = os.getenv("NOMINATIM_USER_AGENT", f"greenroute_explorer_{int(time.time())}")
        self.geolocator = Nominatim(user_agent=self.user_agent, timeout=15)
        self.google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        self.gmaps = None
        
        # In-memory cache for the life of the process
        self._cache = {}
        
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
        
        # 2. Remove Floor/Room/Unit/Flat patterns
        patterns = [
            r'\b(floor|level|room|unit|apt|apartment|flat|suite|block|gate|cabin|cabin no|plot|plot no)\b[\s#]*[a-z0-9-]+',
            r'\b(ground|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+floor\b',
            r'\b(ward|mandal|corporation|zone)\b[\s]*[a-z0-9-]+', # Strip specific local noise if too long
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
        """
        if not address or not address.strip():
            return None
        
        # Normalize and clean
        clean_address = " ".join(address.split()).strip()
        smart_cleaned = self._clean_address_noise(clean_address)
        
        # CHECK CACHE FIRST
        if smart_cleaned in self._cache:
            # print(f"   [CACHE HIT] {smart_cleaned}")
            return self._cache[smart_cleaned]
        
        # 1. Try Google Maps if available
        if self.gmaps:
            try:
                # Slight sleep for safety, but check cache first
                time.sleep(0.1)
                result = self.gmaps.geocode(smart_cleaned)
                if result:
                    location = result[0]['geometry']['location']
                    coords = (location['lat'], location['lng'])
                    self._cache[smart_cleaned] = coords
                    return coords
            except Exception as e:
                print(f"Google Maps geocoding error: {e}")
        
        # 2. Try Nominatim with Iterative Peeling
        coords = self._geocode_nominatim_robust(smart_cleaned)
        if coords:
            self._cache[smart_cleaned] = coords
            
        return coords

    def _geocode_nominatim_robust(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Robust Nominatim geocoding using iterative peeling.
        """
        parts = [p.strip() for p in address.split(',')]
        
        # Strategy: Try full address, then progressively remove the leftmost part
        # Limit peeling depth to prevent excessive API hits
        max_peeling = min(len(parts) - 1, 4) 
        
        for i in range(max_peeling + 1):
            current_search = ", ".join(parts[i:]).strip()
            
            # Skip if current search is just noise like "India" or a single pincode
            if len(current_search.split()) < 2 and i > 0:
                continue
            
            # Check cache for the "peeled" version too!
            if current_search in self._cache:
                return self._cache[current_search]
                
            try:
                # Strict 1s sleep ONLY if we are hitting Nominatim
                time.sleep(1)
                location = self.geolocator.geocode(current_search)
                
                if location:
                    coords = (location.latitude, location.longitude)
                    self._cache[current_search] = coords
                    if i > 0:
                        print(f"   [NOTICE] Resolved via fallback: '{current_search}'")
                    return coords
                
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
