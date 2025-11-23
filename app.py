"""Main Streamlit application for AI Tourism Planner"""

import streamlit as st
import folium
from streamlit_folium import st_folium
from orchestrator import TourismOrchestrator
from ui_components import display_weather, display_places, apply_custom_styles
from logger import logger

def initialize_app():
    """Initialize the Streamlit app"""
    st.set_page_config(
        page_title="AI Tourism Planner",
        page_icon="✈️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    apply_custom_styles()
    logger.info("Application started")

def render_sidebar():
    """Render the sidebar with settings and examples"""
    with st.sidebar:
        st.header("⚙️ Settings")
        
        search_radius = st.slider(
            "Search Radius (km)",
            min_value=5,
            max_value=100,
            value=30,
            step=5,
            help="Adjust the search radius for finding attractions"
        )
        
        max_places = st.slider(
            "Number of Places",
            min_value=5,
            max_value=20,
            value=8,
            step=1,
            help="Maximum number of attractions to display"
        )
        
        st.divider()
        
        st.header("💡 Quick Examples")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🌤️ Paris Weather", use_container_width=True, key="example_paris"):
                st.session_state['query'] = "What's the weather in Paris?"
                st.session_state['trigger_search'] = True
                logger.info("Quick example selected", example="Paris Weather")
                st.rerun()
        
        with col2:
            if st.button("📍 Tokyo Places", use_container_width=True, key="example_tokyo"):
                st.session_state['query'] = "Show me places to visit in Tokyo"
                st.session_state['trigger_search'] = True
                logger.info("Quick example selected", example="Tokyo Places")
                st.rerun()
        
        col3, col4 = st.columns(2)
        
        with col3:
            if st.button("🗓️ Rome 3-day", use_container_width=True, key="example_rome"):
                st.session_state['query'] = "Plan a 3-day itinerary for Rome with travel tips"
                st.session_state['trigger_search'] = True
                logger.info("Quick example selected", example="Rome 3-day")
                st.rerun()
        
        with col4:
            if st.button("✈️ Bangalore Trip", use_container_width=True, key="example_bangalore"):
                st.session_state['query'] = "I'm going to Bangalore, let's plan my trip"
                st.session_state['trigger_search'] = True
                logger.info("Quick example selected", example="Bangalore Trip")
                st.rerun()
        
        st.divider()
        
        st.markdown("### 🎯 Features")
        st.markdown("""
        - 🤖 AI-powered query understanding
        - 🌍 Global location support
        - 🌤️ 7-day weather forecasts
        - 📍 Tourist attraction discovery
        - 🗺️ Smart itinerary generation
        - 💡 Personalized travel tips
        - 📊 Distance calculations
        - 🔗 Direct map links
        - ✨ Auto spell correction
        """)
    
    return search_radius * 1000, max_places  # Convert km to meters

def render_header():
    """Render the main header"""
    st.markdown('<h1 class="main-header">✈️ AI-Powered Tourism Planner</h1>', unsafe_allow_html=True)
    st.markdown("*Powered by Groq AI • Real-time Weather • Smart Recommendations*")

def get_user_input():
    """Get user input with query persistence"""
    # Use session state for input persistence
    if 'query' not in st.session_state:
        st.session_state['query'] = ''
    
    query = st.text_input(
        "🔍 Ask me about your travel destination:",
        value=st.session_state.get('query', ''),
        placeholder="e.g., 'I'm going to Bangalore, let's plan my trip' or 'Weather in London?'",
        key='user_input'
    )
    
    # Update session state
    if query != st.session_state.get('query', ''):
        st.session_state['query'] = query
    
    return query

def render_action_buttons():
    """Render action buttons"""
    col1, col2, col3 = st.columns([1, 1, 4])
    
    with col1:
        search_button = st.button("🚀 Search", type="primary", use_container_width=True)
    
    with col2:
        clear_button = st.button("🗑️ Clear", use_container_width=True)
    
    return search_button, clear_button

def process_search(orchestrator, query, search_radius, max_places):
    """Process the search query"""
    logger.info("NEW SEARCH", query=query)
    
    with st.spinner("🔍 Analyzing your request and gathering information..."):
        result = orchestrator.process_query(query, search_radius, max_places)
    
    if not result['success']:
        if result.get('is_greeting', False):
            st.info(result['message'])
            logger.info("Greeting/invalid query handled", query=query)
        else:
            st.error(result.get('message', f"❌ Error: {result.get('error', 'Unknown error occurred')}"))
            logger.warning("Search failed", error_msg=result.get('message'))
        return
    
    # Cache result
    st.session_state['last_result'] = result
    
    logger.info("Search successful", place=result['place'])
    
    # Display AI Summary
    if result.get('summary'):
        st.success("### 🤖 AI Summary")
        st.markdown(result['summary'])
        st.divider()
    
    # Display location info
    st.info(f"**📍 Location:** {result['display_name']}")
    
    # Create tabs for different information
    tabs = []
    if result['data'].get('weather'):
        tabs.append("🌤️ Weather")
    if result['data'].get('places'):
        tabs.append("📍 Places")
    if result['data'].get('itinerary'):
        tabs.append("🗓️ Itinerary")
    if result['data'].get('tips'):
        tabs.append("💡 Travel Tips")
    
    if tabs:
        tab_objects = st.tabs(tabs)
        tab_idx = 0
        
        # Weather tab
        if result['data'].get('weather'):
            with tab_objects[tab_idx]:
                display_weather(result['data']['weather'], result['place'])
            tab_idx += 1
        
        # Places tab
        if result['data'].get('places'):
            with tab_objects[tab_idx]:
                display_places(result['data']['places'], result['coordinates'])
            tab_idx += 1
        
        # Itinerary tab
        if result['data'].get('itinerary'):
            with tab_objects[tab_idx]:
                st.subheader("🗓️ Suggested Itinerary")
                st.markdown(result['data']['itinerary'])
            tab_idx += 1
        
        # Tips tab
        if result['data'].get('tips'):
            with tab_objects[tab_idx]:
                st.subheader("💡 Travel Tips")
                st.info(result['data']['tips'])
            tab_idx += 1
    
    # Interactive Map View
    if result['data'].get('places') and result['data']['places']:
        st.subheader("🗺️ Interactive Map")
        
        places_with_coords = [p for p in result['data']['places'] if p.get('lat') and p.get('lon')]
        
        if places_with_coords:
            center_lat = result['coordinates']['lat']
            center_lon = result['coordinates']['lon']
            
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=12,
                tiles='OpenStreetMap',
                control_scale=True
            )
            
            folium.Marker(
                [center_lat, center_lon],
                popup=f"<b>{result['place']}</b><br>Your destination",
                tooltip=result['place'],
                icon=folium.Icon(color='red', icon='star', prefix='fa')
            ).add_to(m)
            
            for idx, place in enumerate(places_with_coords[:20], 1):
                if place.get('lat') and place.get('lon'):
                    popup_html = f"""
                    <div style="min-width: 200px;">
                        <h4>{place.get('name', 'Unknown')}</h4>
                        <p><b>Type:</b> {place.get('type', 'N/A').title()}</p>
                        {f"<p><b>Address:</b> {place['address']}</p>" if place.get('address') else ""}
                        <a href="https://www.google.com/maps/search/?api=1&query={place['lat']},{place['lon']}" target="_blank">Open in Google Maps</a>
                    </div>
                    """
                    
                    folium.Marker(
                        [place['lat'], place['lon']],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=f"{idx}. {place.get('name', 'Unknown')}",
                        icon=folium.Icon(color='blue', icon='info-sign')
                    ).add_to(m)
            
            # Prevent map interaction from triggering reruns
            st_folium(m, width=None, height=500, key="tourism_map", returned_objects=[])
            logger.info("Interactive map displayed", locations=len(places_with_coords))
        else:
            st.info("Map data not available for the selected places.")

def main():
    """Main application entry point"""
    initialize_app()
    
    # Render UI components
    search_radius, max_places = render_sidebar()
    render_header()
    
    # Initialize orchestrator
    if 'orchestrator' not in st.session_state:
        try:
            st.session_state['orchestrator'] = TourismOrchestrator(st.secrets["GROQ_API_KEY"])
            logger.info("Orchestrator initialized successfully")
        except Exception as e:
            st.error(f"Failed to initialize application: {str(e)}")
            logger.critical("Failed to initialize orchestrator", error=str(e))
            return
    
    # Get user input
    user_query = get_user_input()
    
    # Action buttons
    search_button, clear_button = render_action_buttons()
    
    # Handle clear button
    if clear_button:
        st.session_state['query'] = ''
        st.session_state['trigger_search'] = False
        st.session_state.pop('last_result', None)
        st.session_state.pop('last_query', None)
        logger.info("UI cleared")
        st.rerun()
    
    # Handle search button or triggered search from examples
    should_search = (search_button and user_query) or (st.session_state.get('trigger_search', False) and user_query)
    
    if should_search:
        # Reset trigger flag
        st.session_state['trigger_search'] = False
        
        # Process search
        st.session_state['last_query'] = user_query
        process_search(
            st.session_state['orchestrator'],
            user_query,
            search_radius,
            max_places
        )
    elif search_button:
        st.warning("⚠️ Please enter a destination to search.")
        logger.warning("Search attempted with empty query")

if __name__ == "__main__":
    main()