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
        # Specific user agent to avoid blocks
        self.user_agent = os.getenv("NOMINATIM_USER_AGENT", f"greenroute_explorer_{int(time.time())}")
        
        # 1. Google Maps (Primary Pro)
        self.google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        self.gmaps = None
        if self.google_api_key:
            try:
                import googlemaps
                self.gmaps = googlemaps.Client(key=self.google_api_key)
                print("[OK] Google Maps Geocoding enabled.")
            except Exception as e:
                print(f"Error initializing Google Maps: {e}")

        # 2. Mapbox (Secondary Pro - New)
        from geopy.geocoders import Nominatim, Photon, MapBox
        self.mapbox_api_key = os.getenv("MAPBOX_API_KEY")
        self.mapbox = None
        if self.mapbox_api_key:
            try:
                self.mapbox = MapBox(api_key=self.mapbox_api_key, user_agent=self.user_agent, timeout=20)
                print("[OK] Mapbox Geocoding enabled.")
            except Exception as e:
                print(f"Error initializing Mapbox: {e}")

        # 3. Free Fallbacks
        self.geolocator = Nominatim(user_agent=self.user_agent, timeout=20)
        self.photon = Photon(user_agent=self.user_agent, timeout=20)
        
        # In-memory cache
        self._cache = {}
        self.nominatim_blocked_until = 0
    
    def _clean_address_noise(self, address: str) -> str:
        """
        Remove non-geographic noise like floor numbers, room numbers, 
        and parenthetical notes that confuse geocoders.
        """
        # 1. Remove everything inside parentheses
        address = re.sub(r'\(.*?\)', '', address)
        
        # 2. Remove Floor/Room/Unit/Flat patterns
        patterns = [
            r'\b(floor|level|room|unit|apt|apartment|flat|suite|block|gate|cabin|cabin no|plot|plot no|house|house no)\b[\s#]*[a-z0-9-]+',
            r'\b(ground|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+floor\b',
            r'\b(ward|mandal|corporation|zone|village|colony|bapu bagh|greater hyderabad municipal corporation|north zone)\b[\s]*[a-z0-9-]*',
            r'\b(near|beside|opposite|behind|front of)\b[\s]*[a-z0-9-]+', # Landmark noise
        ]
        
        for pattern in patterns:
            address = re.sub(pattern, '', address, flags=re.IGNORECASE)
            
        # 3. Clean up extra commas and spaces
        address = re.sub(r',\s*,', ',', address) # Double commas
        address = re.sub(r'\s+', ' ', address)   # Double spaces
        
        return address.strip().strip(',')

    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convert address to (latitude, longitude) coordinates.
        Fallback chain: Google -> Mapbox -> Nominatim -> Photon.
        """
        if not address or not address.strip():
            return None
        
        # Normalize and clean
        clean_address = " ".join(address.split()).strip()
        smart_cleaned = self._clean_address_noise(clean_address)
        
        # 1. CHECK CACHE FIRST
        if smart_cleaned in self._cache:
            return self._cache[smart_cleaned]
        
        # 2. Try Google Maps if available
        if self.gmaps:
            try:
                time.sleep(0.1)
                result = self.gmaps.geocode(smart_cleaned)
                if result:
                    location = result[0]['geometry']['location']
                    coords = (location['lat'], location['lng'])
                    self._cache[smart_cleaned] = coords
                    return coords
            except Exception as e:
                print(f"Google Maps geocoding error: {e}")
        
        # 3. Try Mapbox if available (New)
        if self.mapbox:
            coords = self._geocode_mapbox_robust(smart_cleaned)
            if coords:
                self._cache[smart_cleaned] = coords
                return coords

        # 4. Try Nominatim (conditional on block)
        if time.time() > self.nominatim_blocked_until:
            coords = self._geocode_nominatim_robust(smart_cleaned)
            if coords:
                self._cache[smart_cleaned] = coords
                return coords
        else:
            print(f"   [NOTICE] Skipping Nominatim (Temporary Rate Limit Block)")
            
        # 5. Final Fallback: Photon
        coords = self._geocode_photon_robust(smart_cleaned)
        if coords:
            self._cache[smart_cleaned] = coords
            
        return coords

    def _geocode_mapbox_robust(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Robust Mapbox geocoding with iterative peeling.
        """
        parts = [p.strip() for p in address.split(',')]
        max_peeling = min(len(parts) - 1, 3) 
        
        for i in range(max_peeling + 1):
            current_search = ", ".join(parts[i:]).strip()
            if not current_search or (len(current_search.split()) < 2 and i > 0):
                continue
                
            try:
                # Mapbox is fast and generous
                time.sleep(0.1)
                location = self.mapbox.geocode(current_search)
                if location:
                    coords = (location.latitude, location.longitude)
                    if i > 0:
                        print(f"   [NOTICE] Resolved via Mapbox fallback: '{current_search}'")
                    return coords
            except Exception as e:
                print(f"Warning: Mapbox geocoding error for '{current_search}': {e}")
                continue
        return None

    def _geocode_nominatim_robust(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Robust Nominatim geocoding with 429 detection.
        """
        parts = [p.strip() for p in address.split(',')]
        max_peeling = min(len(parts) - 1, 4) 
        
        for i in range(max_peeling + 1):
            current_search = ", ".join(parts[i:]).strip()
            if len(current_search.split()) < 2 and i > 0:
                continue
            if current_search in self._cache:
                return self._cache[current_search]
                
            try:
                time.sleep(1)
                location = self.geolocator.geocode(current_search)
                if location:
                    coords = (location.latitude, location.longitude)
                    self._cache[current_search] = coords
                    if i > 0:
                        print(f"   [NOTICE] Resolved via Nominatim fallback: '{current_search}'")
                    return coords
                
            except GeocoderServiceError as e:
                if "429" in str(e):
                    print(f"   [ALERT] Nominatim Rate Limit (429)! Blocking for 1 min.")
                    self.nominatim_blocked_until = time.time() + 60
                    return None 
                print(f"Warning: Nominatim error for '{current_search}': {e}")
                continue
            except Exception as e:
                print(f"Error: Nominatim unexpected error for '{current_search}': {e}")
                continue
        return None

    def _geocode_photon_robust(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Fallback geocoding using Photon.
        """
        parts = [p.strip() for p in address.split(',')]
        max_peeling = min(len(parts) - 1, 2) 
        
        for i in range(max_peeling + 1):
            current_search = ", ".join(parts[i:]).strip()
            if not current_search or (len(current_search.split()) < 2 and i > 0):
                continue
                
            try:
                time.sleep(0.5)
                location = self.photon.geocode(current_search)
                if location:
                    coords = (location.latitude, location.longitude)
                    print(f"   [NOTICE] Resolved via Photon: '{current_search}'")
                    return coords
            except Exception as e:
                print(f"Warning: Photon geocoding error for '{current_search}': {e}")
                continue
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
