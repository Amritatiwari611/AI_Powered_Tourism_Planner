"""Tourism Orchestrator - Main coordination logic"""

import json
import re
from typing import Dict
from groq import Groq
from logger import logger
from config import GROQ_MODEL, DEFAULT_SEARCH_RADIUS, DEFAULT_MAX_PLACES
from core_agents import GeocodingAgent, WeatherAgent, PlacesAgent, TravelInsightsAgent


class TourismOrchestrator:
    """Parent agent that orchestrates all child agents"""
    
    def __init__(self, groq_api_key: str):
        logger.info("Initializing TourismOrchestrator")
        
        self.client = Groq(api_key=groq_api_key)
        self.geocoding = GeocodingAgent()
        self.weather = WeatherAgent()
        self.places = PlacesAgent()
        self.insights = TravelInsightsAgent(groq_api_key)
        
        logger.info("TourismOrchestrator initialized successfully")
    
    def _get_spelling_suggestions(self, place_name: str) -> str:
        """Use LLM to suggest correct spelling for a place name"""
        try:
            prompt = f"""The user searched for a place called "{place_name}" but it wasn't found.
            
What is the correct spelling of this city/place? Provide ONLY the corrected city name, nothing else.

Common examples:
- "bengalururu" → "Bangalore"
- "parris" → "Paris"
- "tokio" → "Tokyo"
- "mumbi" → "Mumbai"
- "delli" → "Delhi"
- "londun" → "London"

Corrected name for "{place_name}"?"""

            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=GROQ_MODEL,
                temperature=0.1,
                max_tokens=50
            )
            
            suggestion = response.choices[0].message.content.strip().strip('"').strip("'")
            logger.info("Spelling suggestion generated", original=place_name, suggestion=suggestion)
            return suggestion
        except Exception as e:
            logger.error("Error generating spelling suggestion", error=str(e))
            return place_name
    
    def extract_place_name(self, user_input: str) -> str:
        """Extract place name from user query using multiple strategies"""
        logger.info("Extracting place name from query", query=user_input)
        
        # Strategy 1: Common patterns
        patterns = [
            r"(?:going to|visit|plan.*trip to|travel to|in)\s+([A-Z][a-zA-Z\s]+?)(?:\s*[,\.]|$|\s+(?:let|what|and|for))",
            r"weather in\s+([A-Z][a-zA-Z\s]+?)(?:\s*[,\.\?]|$)",
            r"places (?:in|to visit in)\s+([A-Z][a-zA-Z\s]+?)(?:\s*[,\.\?]|$)",
            r"^([A-Z][a-zA-Z\s]+?)(?:\s+weather|places|trip|itinerary)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                place = match.group(1).strip()
                logger.info("Pattern matched", extracted_place=place)
                return place
        
        # Strategy 2: Look for capitalized words (likely city names)
        words = user_input.split()
        capitalized_words = [w for w in words if w and w[0].isupper() and w.lower() not in 
                           ['i', 'i\'m', 'going', 'to', 'what', 'let', 'plan', 'my', 'trip', 'the']]
        
        if capitalized_words:
            place = ' '.join(capitalized_words)
            logger.info("Capitalized words found", extracted_place=place)
            return place
        
        # Strategy 3: Use AI as fallback
        logger.info("Using AI to extract place name")
        return user_input
    
    def understand_query(self, user_input: str) -> Dict:
        """Use Groq AI to understand user intent with improved prompting"""
        logger.info("Understanding query", query=user_input)
        
        try:
            prompt = f"""You are a tourism assistant. Analyze this query and extract travel-related information.

Query: "{user_input}"

CRITICAL RULES:
1. If the query is just a greeting (hi, hello, hey, thanks, bye) or casual chat, set place to null and is_valid_query to false
2. If no specific city/location is mentioned, set place to null and is_valid_query to false
3. Extract ONLY the city/location name, not the entire sentence
4. **AUTOMATICALLY FIX SPELLING MISTAKES** in city names (e.g., "bengalururu" → "Bangalore", "parris" → "Paris", "tokio" → "Tokyo")
5. Use the most common/official English name for cities
6. If you're unsure about spelling, provide the closest match

Examples:
- "I'm going to go to Bangalore, let's plan my trip" → place: "Bangalore", intents: ["places", "itinerary"], is_valid_query: true
- "trip to bengalururu" → place: "Bangalore", intents: ["places"], is_valid_query: true (corrected spelling)
- "Weather in parris" → place: "Paris", intents: ["weather"], is_valid_query: true (corrected spelling)
- "What can I do in Tokio for 3 days?" → place: "Tokyo", intents: ["places", "itinerary"], days: 3, is_valid_query: true (corrected spelling)
- "Show me places in New York" → place: "New York", intents: ["places"], is_valid_query: true
- "hi" → place: null, intents: ["greeting"], is_valid_query: false
- "hello" → place: null, intents: ["greeting"], is_valid_query: false
- "I want to travel" → place: null, intents: ["general"], is_valid_query: false

Respond ONLY with valid JSON (use null without quotes for null values):
{{
    "place": "corrected city name" or null,
    "intents": ["weather", "places", "itinerary", "tips", "greeting", "general"],
    "days": 1,
    "is_valid_query": true or false
}}"""

            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=GROQ_MODEL,
                temperature=0.1,  # Lower temperature for more consistent extraction
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            
            # Normalize place to None if it's null or string "null"
            if result.get('place') in [None, 'null', 'None', '']:
                result['place'] = None
            
            logger.info("Query understood", 
                       place=result.get('place'), 
                       intents=result.get('intents'),
                       days=result.get('days'),
                       is_valid=result.get('is_valid_query', True))
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error("JSON decode error in query understanding", error=str(e))
            # Fallback to simple extraction
            place = self.extract_place_name(user_input)
            
            # Detect greetings
            greeting_words = ['hi', 'hello', 'hey', 'thanks', 'thank you', 'bye', 'goodbye']
            is_greeting = user_input.lower().strip() in greeting_words
            
            return {
                "place": place if not is_greeting else None,
                "intents": ["greeting"] if is_greeting else ["weather", "places"],
                "days": 1,
                "is_valid_query": not is_greeting and bool(place)
            }
        except Exception as e:
            logger.error("Error understanding query", error=str(e))
            # Fallback to simple extraction
            place = self.extract_place_name(user_input)
            
            # Detect greetings
            greeting_words = ['hi', 'hello', 'hey', 'thanks', 'thank you', 'bye', 'goodbye']
            is_greeting = user_input.lower().strip() in greeting_words
            
            return {
                "place": place if not is_greeting else None,
                "intents": ["greeting"] if is_greeting else ["weather", "places"],
                "days": 1,
                "is_valid_query": not is_greeting and bool(place)
            }
    
    def process_query(self, user_input: str, search_radius: int = DEFAULT_SEARCH_RADIUS, max_places: int = DEFAULT_MAX_PLACES) -> Dict:
        """Main orchestration method"""
        logger.info("Processing query", query=user_input, search_radius=search_radius, max_places=max_places)
        
        # Understand the query
        query_analysis = self.understand_query(user_input)
        place_name = query_analysis.get('place')
        intents = query_analysis.get('intents', ['weather', 'places'])
        days = query_analysis.get('days', 1)
        is_valid = query_analysis.get('is_valid_query', True)
        
        logger.info("Query analysis complete", 
                   place=place_name, 
                   intents=intents, 
                   days=days,
                   is_valid=is_valid)
        
        # Handle greetings and invalid queries
        if 'greeting' in intents or not place_name or not is_valid:
            logger.info("Non-travel query detected", query_type=intents)
            return {
                'success': False,
                'is_greeting': True,
                'message': "👋 Hello! I'm your AI travel assistant. Please tell me which city or place you'd like to visit, and I can help you with:\n\n• Current weather and 7-day forecasts\n• Top tourist attractions\n• Personalized itineraries\n• Travel tips and recommendations\n\nFor example, try:\n- 'I'm going to Paris'\n- 'What's the weather in Tokyo?'\n- 'Plan a 3-day trip to Rome'"
            }
        
        # Get coordinates
        geo_data = self.geocoding.get_coordinates(place_name)
        
        if not geo_data:
            logger.warning("Place not found", place=place_name)
            
            # Try to get spelling suggestions using LLM
            suggestion = self._get_spelling_suggestions(place_name)
            
            error_msg = f"I couldn't find a place called '{place_name}'."
            if suggestion and suggestion != place_name:
                error_msg += f"\n\n💡 Did you mean **{suggestion}**? Try searching for that instead!"
            else:
                error_msg += "\n\nPlease check the spelling or try a different location.\n\nTip: Try using well-known city names like 'London', 'New York', or 'Tokyo'."
            
            return {
                'success': False,
                'is_greeting': False,
                'message': error_msg
            }
        
        logger.info("Geocoding successful", 
                   place=place_name,
                   display_name=geo_data['display_name'])
        
        result = {
            'success': True,
            'place': place_name,
            'display_name': geo_data['display_name'],
            'coordinates': {'lat': geo_data['lat'], 'lon': geo_data['lon']},
            'intents': intents,
            'data': {}
        }
        
        # Fetch data based on intents
        if 'weather' in intents or 'general' in intents:
            logger.info("Fetching weather data")
            weather_data = self.weather.get_weather(geo_data['lat'], geo_data['lon'])
            if weather_data:
                result['data']['weather'] = weather_data
                logger.info("Weather data added to result")
        
        if 'places' in intents or 'general' in intents or 'itinerary' in intents:
            logger.info("Fetching places data", radius=search_radius, limit=max_places)
            places_data = self.places.get_tourist_places(
                geo_data['lat'], 
                geo_data['lon'],
                radius=search_radius,
                limit=max_places
            )
            if places_data:
                result['data']['places'] = places_data
                logger.info("Places data added to result", count=len(places_data))
        
        if 'tips' in intents and result['data'].get('weather') and result['data'].get('places'):
            logger.info("Generating travel tips")
            tips = self.insights.get_travel_tips(
                place_name,
                result['data']['weather'],
                result['data']['places']
            )
            result['data']['tips'] = tips
            logger.info("Travel tips added to result")
        
        if 'itinerary' in intents and result['data'].get('places'):
            logger.info("Generating itinerary", days=days)
            itinerary = self.insights.get_itinerary(
                place_name,
                result['data']['places'],
                days
            )
            result['data']['itinerary'] = itinerary
            logger.info("Itinerary added to result")
        
        # Generate AI summary
        logger.info("Generating AI summary")
        summary = self._generate_summary(user_input, place_name, result, intents)
        result['summary'] = summary
        logger.info("Summary added to result")
        
        logger.info("Query processing complete", 
                   success=True,
                   data_keys=list(result['data'].keys()))
        
        return result
    
    def _generate_summary(self, query: str, place: str, result: dict, intents: list) -> str:
        """Generate detailed AI summary based on gathered data"""
        try:
            # Prepare detailed context from data
            weather_details = "unavailable"
            forecast_info = ""
            if result['data'].get('weather'):
                weather_data = result['data']['weather']
                current = weather_data.get('current', {})
                
                # Use correct field names from Open-Meteo API
                temp = current.get('temperature_2m')
                humidity = current.get('relative_humidity_2m')
                wind = current.get('wind_speed_10m')
                weather_code = current.get('weather_code', 0)
                
                # Get weather condition from code
                from core_agents import WeatherAgent
                condition = WeatherAgent.get_weather_description(weather_code)
                
                if temp is not None:
                    weather_details = f"{temp}°C with {condition.lower()}"
                    if humidity is not None:
                        weather_details += f", {humidity}% humidity"
                    if wind is not None:
                        weather_details += f", wind speed {wind} km/h"
                
                # Add forecast info if available
                daily = weather_data.get('daily', {})
                if daily:
                    max_temps = daily.get('temperature_2m_max', [])
                    min_temps = daily.get('temperature_2m_min', [])
                    if max_temps and min_temps:
                        forecast_info = f"\n- 7-Day Forecast: Temperatures ranging from {min(min_temps):.0f}°C to {max(max_temps):.0f}°C"
            
            places_info = ""
            if result['data'].get('places'):
                places = result['data']['places']
                places_count = len(places)
                
                # Enhanced filtering for actual tourist attractions
                # Keywords for tourist spots (expanded for Indian landmarks)
                tourist_keywords = [
                    'temple', 'park', 'museum', 'palace', 'fort', 'garden', 'lake', 'monument', 
                    'church', 'cathedral', 'mosque', 'tower', 'gallery', 'center', 'centre', 
                    'stadium', 'zoo', 'aquarium', 'beach', 'hill', 'viewpoint', 'mandir', 'masjid',
                    'gurdwara', 'memorial', 'hall', 'statue', 'square', 'planetarium',
                    'library', 'auditorium', 'vidhana', 'bhavan', 'soudha', 'ashram', 'ashrama',
                    'arch', 'bridge', 'gate', 'glasshouse', 'glass house', 'hanging'
                ]
                
                # Exclude keywords - only exclude obvious non-tourist places
                exclude_keywords = [
                    'atm', 'office building', 'police station', 'pharmacy', 'apartment complex'
                ]
                
                actual_attractions = []
                all_place_names = []
                
                for p in places:
                    name = p.get('name', '')
                    if not name or name == 'Unknown':
                        continue
                    
                    name_lower = name.lower()
                    tags = p.get('tags', {})
                    place_type = p.get('type', '').lower()
                    
                    # Collect all valid place names (skip only obvious excludes)
                    should_exclude = any(exclude in name_lower for exclude in exclude_keywords)
                    if not should_exclude:
                        all_place_names.append(name)
                    
                    # Check if it's a tourist attraction based on multiple criteria
                    has_tourist_keyword = any(keyword in name_lower for keyword in tourist_keywords)
                    has_tourist_type = place_type in ['attraction', 'museum', 'viewpoint', 'artwork', 'gallery', 'monument', 'memorial']
                    
                    # Check tags if available
                    tourism_tag = tags.get('tourism', '').lower() if tags else ''
                    historic_tag = tags.get('historic', '').lower() if tags else ''
                    leisure_tag = tags.get('leisure', '').lower() if tags else ''
                    
                    has_tourist_tag = (
                        tourism_tag in ['attraction', 'museum', 'viewpoint', 'artwork', 'gallery', 'yes'] or
                        historic_tag in ['yes', 'monument', 'memorial', 'castle', 'fort', 'palace', 'archaeological_site'] or
                        leisure_tag in ['park', 'garden', 'stadium']
                    )
                    
                    is_attraction = has_tourist_keyword or has_tourist_type or has_tourist_tag
                    
                    if is_attraction and not should_exclude:
                        actual_attractions.append(name)
                
                # Derive simple category set for variety description
                categories = set()
                for p in places:
                    t = (p.get('type','') or '').lower()
                    if t:
                        categories.add(t)
                    tags = p.get('tags',{}) or {}
                    for k in ['tourism','historic','leisure','amenity','natural']:
                        val = (tags.get(k,'') or '').lower()
                        if val:
                            categories.add(val)
                # Normalize some category labels
                normalize_map = {
                    'place_of_worship':'spiritual site',
                    'museum':'museum',
                    'gallery':'gallery',
                    'park':'park',
                    'garden':'garden',
                    'viewpoint':'viewpoint',
                    'attraction':'attraction',
                    'fort':'fort',
                    'palace':'palace',
                    'castle':'castle',
                    'temple':'temple',
                    'mosque':'mosque',
                    'church':'church',
                    'stadium':'stadium',
                    'peak':'peak',
                    'waterfall':'waterfall'
                }
                categories_clean = []
                for c in categories:
                    if c in normalize_map:
                        categories_clean.append(normalize_map[c])
                categories_clean = sorted(set(categories_clean))
                category_phrase = ''
                if categories_clean:
                    category_phrase = f"\n- Variety: mix of " + ', '.join(categories_clean[:5]) + (', etc.' if len(categories_clean) > 5 else '')

                # Build places info generically without hard-coded counts, avoid far excursions
                if actual_attractions:
                    sample_places = actual_attractions[:3]
                    places_info = f"\n- Sample nearby points: {', '.join(sample_places)}"
                elif all_place_names:
                    sample_places = all_place_names[:3]
                    places_info = f"\n- Nearby places include: {', '.join(sample_places)}"
                else:
                    places_info = "\n- Local point-of-interest data is limited; consider exploring public parks and neighborhood markets."
                places_info += category_phrase


            
            itinerary_info = ""
            if result['data'].get('itinerary'):
                days = len([line for line in result['data']['itinerary'].split('\n') if line.strip().startswith('**Day')])
                itinerary_info = f"\n- {days}-day itinerary prepared with curated activities"
            
            tips_info = ""
            if result['data'].get('tips'):
                tips_info = "\n- Personalized travel tips and recommendations included"
            
            display_name = result.get('display_name', place)
            
            # Create updated prompt for point-wise summary strictly within current radius context
            prompt = f"""Create a concise, point-wise travel overview for the user.

Context:
Query: {query}
Location: {place} ({display_name})

DATA SNAPSHOT:
- Weather: {weather_details}{forecast_info}{places_info}{itinerary_info}{tips_info}

Guidelines:
- Provide 6-7 bullet points.
- ONLY reference attraction names provided in data; DO NOT invent or add distant city/day-trip suggestions.
- Avoid stating total counts of attractions; use qualitative wording (e.g., 'notable spots', 'a mix of').
- Include: current weather insight, best outdoor time today, clothing/preparedness suggestion, sample nearby points, variety description (if present), navigation/local movement tip, experiential highlight.
- Each bullet max one sentence (can use a semicolon for nuance once).
- Avoid hard numbers except those directly in weather data (temperature range, current readings).
- Do NOT mention places outside the immediate area or famous distant excursions.

Output ONLY the bullet points, no intro or outro text."""

            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You are a precise local tourism assistant. NEVER include distant excursion suggestions or fabricate attraction names. Only use attraction names supplied in the data snapshot. Avoid giving totals; provide qualitative, helpful, actionable bullet points."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=350
            )
            
            summary = response.choices[0].message.content.strip()
            logger.debug("Detailed summary generated", length=len(summary))
            return summary
            
        except Exception as e:
            logger.error("Summary generation failed", error=str(e))
            return f"I found comprehensive information about {place} including current weather conditions, locations to explore, and travel recommendations. Check the detailed tabs below for complete information!"
