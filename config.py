"""Configuration and constants for the Tourism Planner"""

# API Endpoints
WEATHER_API = "https://api.open-meteo.com/v1/forecast"
NOMINATIM_API = "https://nominatim.openstreetmap.org/search"
OVERPASS_API = "https://overpass-api.de/api/interpreter"

# Default Settings
DEFAULT_SEARCH_RADIUS = 30000  # meters (30 km)
DEFAULT_MAX_PLACES = 8
DEFAULT_FORECAST_DAYS = 7
DEFAULT_TEMPERATURE = 0.5
DEFAULT_MAX_TOKENS = 800

# Weather Code Descriptions
WEATHER_CODES = {
    0: "Clear sky ☀️", 1: "Mainly clear 🌤️", 2: "Partly cloudy ⛅", 3: "Overcast ☁️",
    45: "Foggy 🌫️", 48: "Depositing rime fog 🌫️", 51: "Light drizzle 🌦️", 53: "Moderate drizzle 🌦️",
    55: "Dense drizzle 🌧️", 56: "Light freezing drizzle 🌨️", 57: "Dense freezing drizzle 🌨️",
    61: "Slight rain 🌧️", 63: "Moderate rain 🌧️", 65: "Heavy rain ⛈️", 66: "Light freezing rain 🌨️",
    67: "Heavy freezing rain 🌨️", 71: "Slight snow 🌨️", 73: "Moderate snow ❄️", 75: "Heavy snow ❄️",
    77: "Snow grains 🌨️", 80: "Slight rain showers 🌦️", 81: "Moderate rain showers 🌧️",
    82: "Violent rain showers ⛈️", 85: "Slight snow showers 🌨️", 86: "Heavy snow showers ❄️",
    95: "Thunderstorm ⛈️", 96: "Thunderstorm with slight hail ⛈️", 99: "Thunderstorm with heavy hail ⛈️"
}

# Groq Models
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_FALLBACK_MODEL = "llama-3.1-8b-instant"