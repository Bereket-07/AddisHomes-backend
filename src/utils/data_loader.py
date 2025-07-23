import json
from pathlib import Path
from typing import List, Dict, Any

class LocationDataManager:
    def __init__(self, data_path: Path = Path("src/data/addis_ababa_locations.json")):
        self._data = self._load_json(data_path)
        self._sub_cities_data = self._data.get("sub_cities", {})

    def _load_json(self, filepath: Path) -> Dict[str, Any]:
        """Loads the unified locations JSON file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"CRITICAL ERROR: Could not load location data from {filepath}: {e}")
            return {}

    def get_addis_sub_cities(self) -> List[str]:
        """Returns a list of all sub-city names."""
        return list(self._sub_cities_data.keys())

    def get_condo_sites_for_sub_city(self, sub_city_name: str) -> List[str]:
        """Returns a list of condominium sites for a given sub-city."""
        return self._sub_cities_data.get(sub_city_name, {}).get("condominium_sites", [])

    def get_neighborhoods_for_sub_city(self, sub_city_name: str) -> List[str]:
        """Returns a list of famous neighborhoods for a given sub-city."""
        return self._sub_cities_data.get(sub_city_name, {}).get("neighborhoods", [])

# Create a single instance to be used throughout the application
location_data = LocationDataManager()