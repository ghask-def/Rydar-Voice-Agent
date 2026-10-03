"""
Location Manager for storing and accessing current user location data.
"""
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

class LocationManager:
    _instance: Optional['LocationManager'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._latitude: Optional[float] = None
            self._longitude: Optional[float] = None
            self._last_updated: Optional[datetime] = None
            self._update_count: int = 0
            self._initialized = True
            print(f"[LocationManager] Initialized singleton instance")
    
    async def update_location(self, latitude: float, longitude: float) -> None:
        """Update the current location with validation."""
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            print(f"[LocationManager] Invalid latitude: {latitude} (must be between -90 and 90)")
            return
        
        if not (-180 <= longitude <= 180):
            print(f"[LocationManager] Invalid longitude: {longitude} (must be between -180 and 180)")
            return
        
        async with self._lock:
            old_lat, old_lon = self._latitude, self._longitude
            self._latitude = latitude
            self._longitude = longitude
            self._last_updated = datetime.now()
            self._update_count += 1
            
            # Log the update with context
            if old_lat is None and old_lon is None:
                print(f"[LocationManager] Initial location set: {latitude}, {longitude}")
            else:
                # Calculate rough distance for debugging
                lat_diff = abs(latitude - old_lat) if old_lat else 0
                lon_diff = abs(longitude - old_lon) if old_lon else 0
                if lat_diff > 0.001 or lon_diff > 0.001:  # Significant movement (roughly 100m)
                    print(f"[LocationManager] Location moved: {old_lat},{old_lon} -> {latitude},{longitude}")
                else:
                    print(f"[LocationManager] Location updated: {latitude}, {longitude} (#{self._update_count})")
    
    def get_current_location(self) -> Optional[Dict[str, Any]]:
        """Get the current location if available."""
        if self._latitude is not None and self._longitude is not None:
            return {
                'latitude': self._latitude,
                'longitude': self._longitude,
                'last_updated': self._last_updated,
                'update_count': self._update_count
            }
        return None
    
    def get_coordinates_string(self) -> Optional[str]:
        """Get coordinates as a formatted string for API calls."""
        if self._latitude is not None and self._longitude is not None:
            return f"{self._latitude},{self._longitude}"
        return None
    
    def has_location(self) -> bool:
        """Check if location data is available."""
        return self._latitude is not None and self._longitude is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed status for debugging."""
        return {
            'has_location': self.has_location(),
            'latitude': self._latitude,
            'longitude': self._longitude,
            'last_updated': self._last_updated.isoformat() if self._last_updated else None,
            'update_count': self._update_count,
            'coordinates_string': self.get_coordinates_string()
        }

# Global instance
location_manager = LocationManager() 