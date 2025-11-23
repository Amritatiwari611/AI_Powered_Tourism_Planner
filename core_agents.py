"""Core Agent Classes for Tourism Planner"""

import requests
from typing import Optional, Dict, List
from groq import Groq
from logger import logger
from config import (
    WEATHER_API, NOMINATIM_API, OVERPASS_API, WEATHER_CODES,
    DEFAULT_FORECAST_DAYS, DEFAULT_SEARCH_RADIUS, DEFAULT_MAX_PLACES, GROQ_MODEL, DEFAULT_TEMPERATURE
)

class GeocodingAgent:
    """Agent responsible for converting place names to coordinates"""
    
    def __init__(self):
        self.api_url = NOMINATIM_API
        logger.info("GeocodingAgent initialized")
    
    def get_coordinates(self, place_name: str) -> Optional[Dict]:
        """Get latitude and longitude for a place with fuzzy matching fallback"""
        logger.info("Getting coordinates for place", place=place_name)
        
        try:
            headers = {'User-Agent': 'TourismApp/2.0'}
            
            # First attempt: exact match
            params = {
                'q': place_name,
                'format': 'json',
                'addressdetails': 1,
                'limit': 5
            }
            
            response = requests.get(self.api_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data:
                # Prefer city/town/village results over other types
                for item in data:
                    if item.get('type') in ['city', 'town', 'village', 'municipality', 'administrative']:
                        result = {
                            'lat': float(item['lat']),
                            'lon': float(item['lon']),
                            'display_name': item['display_name']
                        }
                        logger.info("Coordinates found", 
                                   lat=result['lat'], 
                                   lon=result['lon'], 
                                   display_name=result['display_name'])
                        return result
                
                # If no city type found, use first result
                result = {
                    'lat': float(data[0]['lat']),
                    'lon': float(data[0]['lon']),
                    'display_name': data[0]['display_name']
                }
                logger.info("Coordinates found (first match)", 
                           lat=result['lat'], 
                           lon=result['lon'], 
                           display_name=result['display_name'])
                return result
            else:
                logger.warning("No coordinates found for place", place=place_name)
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Timeout while getting coordinates", place=place_name)
            return None
        except requests.exceptions.RequestException as e:
            logger.error("Request error in geocoding", error=str(e), place=place_name)
            return None
        except Exception as e:
            logger.error("Unexpected error in geocoding", error=str(e), place=place_name)
            return None


class WeatherAgent:
    """Agent responsible for weather information"""
    
    def __init__(self):
        self.api_url = WEATHER_API
        logger.info("WeatherAgent initialized")
    
    def get_weather(self, lat: float, lon: float, forecast_days: int = DEFAULT_FORECAST_DAYS) -> Optional[Dict]:
        """Get current and forecast weather data"""
        logger.info("Getting weather data", lat=lat, lon=lon, forecast_days=forecast_days)
        
        try:
            params = {
                'latitude': lat,
                'longitude': lon,
                'current': 'temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code',
                'hourly': 'temperature_2m,precipitation_probability,weather_code',
                'daily': 'temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code',
                'timezone': 'auto',
                'forecast_days': forecast_days
            }
            
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            logger.info("Weather data retrieved successfully")
            return data
            
        except requests.exceptions.Timeout:
            logger.error("Timeout while getting weather data", lat=lat, lon=lon)
            return None
        except requests.exceptions.RequestException as e:
            logger.error("Request error in weather API", error=str(e), lat=lat, lon=lon)
            return None
        except Exception as e:
            logger.error("Unexpected error in weather agent", error=str(e))
            return None
    
    @staticmethod
    def get_weather_description(weather_code: int) -> str:
        """Convert weather code to description"""
        description = WEATHER_CODES.get(weather_code, f"Unknown ({weather_code})")
        return description


class PlacesAgent:
    """Agent responsible for finding tourist attractions"""
    
    def __init__(self):
        self.api_url = OVERPASS_API
        logger.info("PlacesAgent initialized")
    
    def get_tourist_places(self, lat: float, lon: float, radius: int = DEFAULT_SEARCH_RADIUS, limit: int = DEFAULT_MAX_PLACES) -> List[Dict]:
        """Get tourist attractions using Overpass API"""
        logger.info("Getting tourist places", lat=lat, lon=lon, radius=radius, limit=limit)
        
        try:
            # Enhanced Overpass query for comprehensive tourist attractions
            query = f"""
            [out:json][timeout:25];
            (
              node["tourism"](around:{radius},{lat},{lon});
              node["historic"](around:{radius},{lat},{lon});
              node["leisure"="park"](around:{radius},{lat},{lon});
              node["amenity"="place_of_worship"](around:{radius},{lat},{lon});
                            node["amenity"="museum"](around:{radius},{lat},{lon});
                            node["tourism"="museum"](around:{radius},{lat},{lon});
                            node["tourism"="gallery"](around:{radius},{lat},{lon});
                            node["tourism"="attraction"](around:{radius},{lat},{lon});
                            node["tourism"="viewpoint"](around:{radius},{lat},{lon});
                            node["natural"="peak"](around:{radius},{lat},{lon});
                            node["natural"="waterfall"](around:{radius},{lat},{lon});
              way["tourism"](around:{radius},{lat},{lon});
              way["historic"](around:{radius},{lat},{lon});
              way["leisure"="park"](around:{radius},{lat},{lon});
              way["amenity"="place_of_worship"](around:{radius},{lat},{lon});
                            way["amenity"="museum"](around:{radius},{lat},{lon});
                            way["tourism"="museum"](around:{radius},{lat},{lon});
                            way["tourism"="gallery"](around:{radius},{lat},{lon});
                            way["tourism"="attraction"](around:{radius},{lat},{lon});
                            way["tourism"="viewpoint"](around:{radius},{lat},{lon});
                            way["natural"="peak"](around:{radius},{lat},{lon});
                            way["natural"="waterfall"](around:{radius},{lat},{lon});
              relation["tourism"](around:{radius},{lat},{lon});
              relation["historic"](around:{radius},{lat},{lon});
              relation["leisure"="park"](around:{radius},{lat},{lon});
              relation["amenity"="place_of_worship"](around:{radius},{lat},{lon});
                            relation["amenity"="museum"](around:{radius},{lat},{lon});
                            relation["tourism"="museum"](around:{radius},{lat},{lon});
                            relation["tourism"="gallery"](around:{radius},{lat},{lon});
                            relation["tourism"="attraction"](around:{radius},{lat},{lon});
                            relation["tourism"="viewpoint"](around:{radius},{lat},{lon});
            );
            out center {limit * 5};
            """
            
            response = requests.post(
                self.api_url, 
                data={'data': query}, 
                timeout=30,
                headers={'User-Agent': 'TourismApp/2.0'}
            )
            response.raise_for_status()
            data = response.json()
            
            places = []
            seen_names = set()
            
            for element in data.get('elements', []):
                tags = element.get('tags', {})
                name = tags.get('name')
                
                if name and name not in seen_names:
                    # Get coordinates (handle node, way, and relation differently)
                    lat_coord = element.get('lat')
                    lon_coord = element.get('lon')
                    
                    # For ways and relations, use center coordinates
                    if not lat_coord and element.get('center'):
                        lat_coord = element['center'].get('lat')
                        lon_coord = element['center'].get('lon')
                    
                    place_info = {
                        'name': name,
                        'type': tags.get('tourism') or tags.get('historic') or tags.get('leisure') or tags.get('amenity', 'attraction'),
                        'tags': tags,  # Store all tags for better filtering
                        'address': tags.get('addr:street', ''),
                        'website': tags.get('website', ''),
                        'wikipedia': tags.get('wikipedia', ''),
                        'lat': lat_coord,
                        'lon': lon_coord
                    }
                    places.append(place_info)
                    seen_names.add(name)
            
            # If we collected more than needed, rank & trim for diversity and relevance
            if len(places) > limit:
                def rank(p: Dict) -> tuple:
                    tags = p.get('tags', {})
                    return (
                        0 if tags.get('wikipedia') or tags.get('website') else 1,
                        0 if tags.get('tourism') in ['museum','gallery','attraction','viewpoint'] else 1,
                        0 if tags.get('historic') else 1,
                        0 if tags.get('leisure') in ['park','garden'] else 1,
                        len(p['name'])  # shorter names first (often landmarks)
                    )
                places = sorted(places, key=rank)[:limit]
            
            logger.info("Retrieved tourist places", count=len(places))
            return places
            
        except requests.exceptions.Timeout:
            logger.error("Timeout while getting places", lat=lat, lon=lon)
            return []
        except requests.exceptions.RequestException as e:
            logger.error("Request error in places API", error=str(e), lat=lat, lon=lon)
            return []
        except Exception as e:
            logger.error("Unexpected error in places agent", error=str(e))
            return []


class TravelInsightsAgent:
    """Advanced agent for travel insights and recommendations"""
    
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.model = GROQ_MODEL
        logger.info("TravelInsightsAgent initialized", model=self.model)
    
    def get_travel_tips(self, place_name: str, weather_data: Dict, places: List[Dict]) -> str:
        """Generate AI-powered travel tips using Groq"""
        logger.info("Generating travel tips", place=place_name)
        
        try:
            current_temp = weather_data.get('current', {}).get('temperature_2m', 'N/A')
            places_list = ', '.join([p['name'] for p in places[:3]]) if places else 'various attractions'
            
            prompt = f"""Based on the following information about {place_name}, provide 3-5 concise, practical travel tips:

Weather: Current temperature is {current_temp}°C
Places to visit: {places_list}

Provide tips about:
1. Best time to visit during the day
2. What to wear/pack
3. Local transportation suggestions
4. Budget considerations
5. Safety tips

Keep each tip brief (1-2 sentences max)."""

            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=DEFAULT_TEMPERATURE,
                max_tokens=500
            )
            
            result = response.choices[0].message.content
            logger.info("Travel tips generated successfully")
            return result
            
        except Exception as e:
            logger.error("Error generating travel tips", error=str(e), place=place_name)
            return f"Unable to generate travel tips at this time."
    
    def get_itinerary(self, place_name: str, places: List[Dict], days: int = 1) -> str:
        """Generate a day-by-day itinerary"""
        logger.info("Generating itinerary", place=place_name, days=days, places_count=len(places))
        
        try:
            places_list = '\n'.join([f"- {p['name']} ({p['type']})" for p in places])
            
            prompt = f"""Create a {days}-day itinerary for visiting {place_name} with these attractions:
{places_list}

Provide a realistic schedule including:
- Morning, afternoon, and evening activities
- Estimated time at each location
- Travel time between locations
- Meal breaks

Format as a clear day-by-day plan."""

            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=DEFAULT_TEMPERATURE,
                max_tokens=800
            )
            
            result = response.choices[0].message.content
            logger.info("Itinerary generated successfully")
            return result
            
        except Exception as e:
            logger.error("Error generating itinerary", error=str(e), place=place_name)
            return f"Unable to generate itinerary at this time."