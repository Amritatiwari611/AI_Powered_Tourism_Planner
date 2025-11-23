"""UI Components for the Tourism Planner"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List
from math import radians, sin, cos, sqrt, atan2
from core_agents import WeatherAgent
from logger import logger


def apply_custom_styles():
    """Apply custom CSS styles to the app"""
    st.markdown("""
        <style>
        .main-header {
            font-size: 3rem;
            font-weight: bold;
            text-align: center;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2rem;
        }
        .stExpander {
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)


def display_weather(weather_data: Dict, place_name: str):
    """Display weather information in an attractive format"""
    logger.info("Displaying weather for", place=place_name)
    
    st.subheader("🌤️ Weather Information")
    
    current = weather_data.get('current', {})
    daily = weather_data.get('daily', {})
    
    # Current weather
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Temperature",
            f"{current.get('temperature_2m', 'N/A')}°C"
        )
    
    with col2:
        st.metric(
            "Humidity",
            f"{current.get('relative_humidity_2m', 'N/A')}%"
        )
    
    with col3:
        st.metric(
            "Wind Speed",
            f"{current.get('wind_speed_10m', 'N/A')} km/h"
        )
    
    with col4:
        rain_prob = daily.get('precipitation_probability_max', [0])[0] if daily.get('precipitation_probability_max') else 0
        st.metric(
            "Rain Chance",
            f"{rain_prob}%"
        )
    
    # Weather description
    weather_code = current.get('weather_code', 0)
    weather_desc = WeatherAgent.get_weather_description(weather_code)
    st.info(f"**Current Conditions:** {weather_desc}")
    
    # 7-day forecast
    if daily:
        st.subheader("📅 7-Day Forecast")
        forecast_cols = st.columns(7)
        
        for i, col in enumerate(forecast_cols):
            if i < len(daily.get('temperature_2m_max', [])):
                date = (datetime.now() + timedelta(days=i)).strftime('%a')
                max_temp = daily['temperature_2m_max'][i]
                min_temp = daily['temperature_2m_min'][i]
                
                with col:
                    st.markdown(f"**{date}**")
                    st.markdown(f"🔺 {max_temp:.0f}°C")
                    st.markdown(f"🔻 {min_temp:.0f}°C")


def display_places(places: List[Dict], coordinates: Dict):
    """Display tourist places in an attractive format"""
    logger.info("Displaying places", count=len(places))
    
    st.subheader("📍 Top Tourist Attractions")
    
    if not places:
        st.warning("No tourist attractions found in this area.")
        return
    
    for idx, place in enumerate(places, 1):
        with st.expander(f"**{idx}. {place['name']}**", expanded=(idx <= 5)):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Type:** {place['type'].title()}")
                if place.get('address'):
                    st.markdown(f"**Address:** {place['address']}")
                if place.get('website'):
                    st.markdown(f"**Website:** [{place['website']}]({place['website']})")
                if place.get('wikipedia'):
                    wiki_url = f"https://en.wikipedia.org/wiki/{place['wikipedia'].split(':')[1]}"
                    st.markdown(f"**Wikipedia:** [Learn more]({wiki_url})")
            
            with col2:
                if place.get('lat') and place.get('lon'):
                    # Calculate distance from city center
                    lat1, lon1 = radians(coordinates['lat']), radians(coordinates['lon'])
                    lat2, lon2 = radians(place['lat']), radians(place['lon'])
                    
                    dlat = lat2 - lat1
                    dlon = lon2 - lon1
                    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                    c = 2 * atan2(sqrt(a), sqrt(1-a))
                    distance = 6371 * c  # Earth radius in km
                    
                    st.metric("Distance", f"{distance:.1f} km")
                    
                    # Google Maps link
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={place['lat']},{place['lon']}"
                    st.markdown(f"[📍 View on Map]({maps_url})")