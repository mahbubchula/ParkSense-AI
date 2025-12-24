"""
ParkSense-AI: Intelligent Parking Analysis System
=================================================
Real-time parking intelligence for Singapore using
HDB, LTA, and URA carpark data with LLM-powered insights.

Author: MAHBUB
Institution: Chulalongkorn University
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_folium import st_folium
import folium

# Import our modules
from config import COLORS, validate_config
from data_fetcher import CarparkDataFetcher
from analyzer import ParkingAnalyzer
from visualizations import ParkingMapVisualizer, ParkingChartVisualizer
from llm_agent import ParkingLLMAgent
from policy_simulator import ParkingPolicySimulator
from features import (
    HistoricalTracker, AlertSystem, CarparkSearch, 
    NearestParkingFinder, ReportExporter, POPULAR_LOCATIONS
)


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="ParkSense-AI | Smart Parking Intelligence",
    page_icon="🅿️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# CUSTOM CSS - PROFESSIONAL DARK THEME
# =============================================================================

def apply_custom_css():
    """Apply beautiful dark theme with excellent readability."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .stApp {
        background: linear-gradient(145deg, #0a0f1a 0%, #111827 50%, #0f172a 100%);
        color: #f8fafc;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a5f 0%, #0f172a 100%);
        border-right: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #ffffff !important; }
    
    h1 { color: #ffffff !important; font-weight: 700 !important; font-size: 2.5rem !important; }
    h2 { color: #f1f5f9 !important; font-weight: 600 !important; font-size: 1.8rem !important; }
    h3 { color: #e2e8f0 !important; font-weight: 600 !important; font-size: 1.3rem !important; }
    p, span, label, .stMarkdown { color: #cbd5e1 !important; }
    
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    [data-testid="stMetricValue"] { color: #22c55e !important; font-size: 2.2rem !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: #f1f5f9 !important; font-size: 1rem !important; font-weight: 500 !important; }
    
    .stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: #ffffff !important;
        border: none;
        border-radius: 12px;
        padding: 14px 32px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
    }
    
    .stSelectbox > div > div {
        background: #1e293b !important;
        border: 2px solid rgba(59, 130, 246, 0.4) !important;
        border-radius: 10px !important;
        color: #f1f5f9 !important;
    }
    
    .stSelectbox [data-baseweb="select"] > div { background: #1e293b !important; }
    .stSelectbox [data-baseweb="select"] span { color: #f1f5f9 !important; }
    
    [data-baseweb="popover"] { background: #1e293b !important; border: 1px solid rgba(59, 130, 246, 0.3) !important; }
    [data-baseweb="menu"] { background: #1e293b !important; }
    [role="option"] { color: #f1f5f9 !important; }
    [role="option"]:hover { background: #2563eb !important; }
    
    .stTextInput > div > div > input {
        background: #1e293b !important;
        border: 2px solid rgba(59, 130, 246, 0.4) !important;
        border-radius: 10px !important;
        color: #f1f5f9 !important;
        padding: 12px 16px !important;
    }
    
    .stTextInput > div > div > input::placeholder { color: #64748b !important; }
    
    .stRadio > div { background: transparent !important; }
    .stRadio label { color: #e2e8f0 !important; background: rgba(30, 41, 59, 0.5) !important; border-radius: 8px !important; padding: 10px 16px !important; }
    .stRadio label:hover { background: rgba(59, 130, 246, 0.2) !important; }
    
    .stCheckbox label { color: #e2e8f0 !important; }
    .stSlider label { color: #f1f5f9 !important; font-weight: 500 !important; }
    
    .streamlit-expanderHeader { background: rgba(30, 41, 59, 0.8) !important; border-radius: 10px !important; color: #f1f5f9 !important; }
    .streamlit-expanderContent { background: rgba(15, 23, 42, 0.8) !important; color: #cbd5e1 !important; }
    
    hr { border: none !important; height: 1px !important; background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.3), transparent) !important; margin: 2rem 0 !important; }
    
    .stAlert { background: rgba(30, 41, 59, 0.9) !important; border: 1px solid rgba(59, 130, 246, 0.3) !important; border-radius: 12px !important; color: #f1f5f9 !important; }
    
    .stTabs [data-baseweb="tab-list"] { background: transparent !important; gap: 8px !important; }
    .stTabs [data-baseweb="tab"] { background: rgba(30, 41, 59, 0.6) !important; border-radius: 10px !important; color: #cbd5e1 !important; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important; color: #ffffff !important; }
    
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 16px;
        padding: 24px;
        margin: 8px 0;
    }
    
    .agency-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 16px;
        padding: 24px;
        margin: 8px 0;
        transition: transform 0.3s ease;
    }
    
    .agency-card:hover { transform: translateY(-4px); }
    .agency-card-hdb { border-left: 4px solid #3b82f6; }
    .agency-card-lta { border-left: 4px solid #10b981; }
    .agency-card-ura { border-left: 4px solid #f97316; }
    
    .badge { display: inline-block; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 0.85rem; margin: 4px; }
    .badge-hdb { background: #3b82f6; color: #ffffff; }
    .badge-lta { background: #10b981; color: #ffffff; }
    .badge-ura { background: #f97316; color: #ffffff; }
    .badge-success { background: rgba(34, 197, 94, 0.2); color: #22c55e; border: 1px solid #22c55e; }
    .badge-warning { background: rgba(234, 179, 8, 0.2); color: #eab308; border: 1px solid #eab308; }
    .badge-danger { background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid #ef4444; }
    
    .alert-card { border-radius: 12px; padding: 16px 20px; margin: 10px 0; }
    .alert-critical { background: rgba(239, 68, 68, 0.15); border-left: 4px solid #ef4444; }
    .alert-warning { background: rgba(234, 179, 8, 0.15); border-left: 4px solid #eab308; }
    .alert-info { background: rgba(59, 130, 246, 0.15); border-left: 4px solid #3b82f6; }
    
    .insight-box {
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
    }
    
    .search-result {
        background: rgba(30, 41, 59, 0.6);
        border-radius: 10px;
        padding: 16px;
        margin: 8px 0;
        border: 1px solid rgba(59, 130, 246, 0.2);
        transition: all 0.2s ease;
    }
    
    .search-result:hover {
        background: rgba(30, 41, 59, 0.8);
        border-color: rgba(59, 130, 246, 0.4);
    }
    
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #0f172a; }
    ::-webkit-scrollbar-thumb { background: #3b82f6; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def init_session_state():
    """Initialize session state variables."""
    if "historical_tracker" not in st.session_state:
        st.session_state.historical_tracker = HistoricalTracker(max_snapshots=60)
    
    if "alert_system" not in st.session_state:
        st.session_state.alert_system = AlertSystem()
    
    if "last_data_fetch" not in st.session_state:
        st.session_state.last_data_fetch = None


# =============================================================================
# CACHING
# =============================================================================

@st.cache_data(ttl=60)
def fetch_parking_data():
    """Fetch and cache parking data."""
    fetcher = CarparkDataFetcher()
    data = fetcher.fetch_data()
    if data:
        df = fetcher.to_dataframe()
        summary = fetcher.get_summary(df)
        return df, summary, fetcher.last_fetch_time
    return None, None, None


@st.cache_resource
def get_analyzer():
    return ParkingAnalyzer()


@st.cache_resource
def get_llm_agent():
    return ParkingLLMAgent()


@st.cache_resource
def get_simulator():
    return ParkingPolicySimulator()


# =============================================================================
# SIDEBAR
# =============================================================================

def render_sidebar():
    """Render sidebar with navigation."""
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 30px 0;'>
            <div style='font-size: 3.5rem; margin-bottom: 10px;'>🅿️</div>
            <h1 style='color: #10b981; margin: 0; font-size: 1.8rem;'>ParkSense-AI</h1>
            <p style='color: #94a3b8; font-size: 0.95rem; margin-top: 8px;'>Smart Parking Intelligence</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        st.markdown("### 🧭 Navigation")
        page = st.radio(
            "Select Page",
            ["🏠 Dashboard", "🗺️ Live Map", "🔍 Search & Find", "📊 Analytics", 
             "🔔 Alerts", "🤖 AI Insights", "🎯 Policy Simulator", "📄 Export"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Data refresh
        st.markdown("### 🔄 Data Status")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        _, _, fetch_time = fetch_parking_data()
        if fetch_time:
            st.markdown(f"<p style='color: #64748b; font-size: 0.85rem; text-align: center;'>Last: {fetch_time.strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)
        
        st.divider()
        
        # Quick stats
        df, summary, _ = fetch_parking_data()
        if df is not None:
            st.markdown("### 📊 Quick Stats")
            st.markdown(f"""
            <div style='background: rgba(30,41,59,0.5); padding: 15px; border-radius: 10px;'>
                <p style='margin: 5px 0;'>🅿️ <strong>{len(df):,}</strong> Carparks</p>
                <p style='margin: 5px 0;'>🚗 <strong>{df['AvailableLots'].sum():,}</strong> Lots</p>
                <p style='margin: 5px 0;'>⚠️ <strong>{len(df[df['AvailableLots'] <= 10])}</strong> Stressed</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        with st.expander("ℹ️ About"):
            st.markdown("""
            **ParkSense-AI** v2.0
            
            Real-time parking intelligence for Singapore.
            
            **Built by:** MAHBUB  
            **Institution:** Chulalongkorn University
            """)
        
        return page


# =============================================================================
# DASHBOARD PAGE
# =============================================================================

def render_dashboard():
    """Render main dashboard."""
    st.markdown("""
    <div style='text-align: center; padding: 20px 0 30px 0;'>
        <h1 style='background: linear-gradient(135deg, #3b82f6, #10b981); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem;'>🅿️ ParkSense-AI Dashboard</h1>
        <p style='color: #94a3b8;'>Real-time parking intelligence across Singapore</p>
    </div>
    """, unsafe_allow_html=True)
    
    df, summary, fetch_time = fetch_parking_data()
    
    if df is None:
        st.error("❌ Failed to fetch parking data.")
        return
    
    # Update historical tracker
    st.session_state.historical_tracker.add_snapshot(df, summary)
    
    # Check alerts
    alerts = st.session_state.alert_system.analyze_and_alert(df, summary)
    alert_summary = st.session_state.alert_system.get_alert_summary()
    
    analyzer = get_analyzer()
    health = analyzer.analyze_overall_health(df)
    
    # Alert banner
    if alert_summary["critical"] > 0:
        st.markdown(f"""
        <div class='alert-card alert-critical'>
            <strong>🚨 {alert_summary['critical']} Critical Alert(s)</strong> - System requires attention!
            <a href='#' style='color: #ef4444; margin-left: 10px;'>View Alerts →</a>
        </div>
        """, unsafe_allow_html=True)
    
    # Top metrics
    st.markdown("### 📈 System Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🅿️ Total Carparks", f"{health['total_carparks']:,}")
    with col2:
        st.metric("🚗 Available Lots", f"{health['total_available_lots']:,}")
    with col3:
        st.metric("💚 System Health", f"{health['health_score']}%", delta=health['status'])
    with col4:
        st.metric("⚠️ Stressed", f"{health['stressed_carparks']}", delta=f"{health['stress_percentage']}%", delta_color="inverse")
    
    st.divider()
    
    # Agency cards
    st.markdown("### 🏢 Agency Performance")
    agency_stats = analyzer.analyze_by_agency(df)
    
    cols = st.columns(3)
    agency_colors = {"HDB": "#3b82f6", "LTA": "#10b981", "URA": "#f97316"}
    
    for i, (agency, stats) in enumerate(agency_stats.items()):
        with cols[i]:
            color = agency_colors.get(agency, "#666")
            emoji = "✅" if stats['health_score'] >= 70 else "⚠️" if stats['health_score'] >= 50 else "❌"
            
            st.markdown(f"""
            <div class='agency-card agency-card-{agency.lower()}'>
                <div style='display: flex; justify-content: space-between;'>
                    <h3 style='color: {color}; margin: 0;'>{agency}</h3>
                    <span style='font-size: 1.5rem;'>{emoji}</span>
                </div>
                <p style='color: #64748b; margin: 8px 0;'>{stats['total_carparks']} carparks</p>
                <h2 style='color: #f1f5f9; margin: 16px 0;'>{stats['total_lots']:,}</h2>
                <p style='color: #94a3b8;'>available lots</p>
                <div style='margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.1);'>
                    <p style='margin: 4px 0;'><span style='color: #94a3b8;'>Health:</span> <span style='color: {"#22c55e" if stats["health_score"] >= 70 else "#eab308"};'>{stats['health_score']}%</span></p>
                    <p style='margin: 4px 0;'><span style='color: #94a3b8;'>Stressed:</span> <span style='color: #ef4444;'>{stats['stress_percentage']}%</span></p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # Charts
    col1, col2 = st.columns(2)
    chart_viz = ParkingChartVisualizer()
    
    with col1:
        st.markdown("### 📊 Status Distribution")
        fig = chart_viz.create_status_donut(summary)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🏆 Top Available")
        fig = chart_viz.create_top_carparks_chart(df, n=8)
        st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# LIVE MAP PAGE
# =============================================================================

def render_live_map():
    """Render interactive map."""
    st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <h1>🗺️ Live Parking Map</h1>
        <p style='color: #94a3b8;'>Interactive real-time carpark availability</p>
    </div>
    """, unsafe_allow_html=True)
    
    df, _, _ = fetch_parking_data()
    if df is None:
        st.error("❌ Failed to fetch data")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        map_type = st.selectbox("🗺️ Map Type", ["By Agency", "By Status", "Heatmap"])
    with col2:
        agency_filter = st.selectbox("🏢 Agency", ["All", "HDB", "LTA", "URA"])
    with col3:
        cluster = st.checkbox("📍 Cluster Markers", value=True)
    
    df_filtered = df if agency_filter == "All" else df[df["Agency"] == agency_filter]
    
    st.markdown(f"""
    <div class='insight-box'>
        <div style='display: flex; justify-content: space-around; text-align: center;'>
            <div><h3 style='color: #3b82f6;'>{len(df_filtered):,}</h3><p>Carparks</p></div>
            <div><h3 style='color: #10b981;'>{df_filtered['AvailableLots'].sum():,}</h3><p>Available</p></div>
            <div><h3 style='color: #f97316;'>{len(df_filtered[df_filtered['Status'] == 'Limited'])}</h3><p>Limited</p></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    map_viz = ParkingMapVisualizer()
    
    if map_type == "By Agency":
        m = map_viz.create_availability_map(df_filtered, cluster=cluster)
    elif map_type == "By Status":
        m = map_viz.create_status_map(df_filtered)
    else:
        m = map_viz.create_heatmap(df_filtered)
    
    st_folium(m, width=None, height=600, use_container_width=True)


# =============================================================================
# SEARCH & FIND PAGE (NEW!)
# =============================================================================

def render_search_find():
    """Render search and nearest parking page."""
    st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <h1>🔍 Search & Find Parking</h1>
        <p style='color: #94a3b8;'>Find carparks by name or location</p>
    </div>
    """, unsafe_allow_html=True)
    
    df, _, _ = fetch_parking_data()
    if df is None:
        st.error("❌ Failed to fetch data")
        return
    
    tab1, tab2 = st.tabs(["🔍 Search Carparks", "📍 Find Nearest"])
    
    # TAB 1: Search
    with tab1:
        st.markdown("### 🔍 Search Carparks")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_query = st.text_input("Search by name:", placeholder="e.g., Marina, Orchard, Tampines...")
        
        with col2:
            agency_filter = st.multiselect("Agency:", ["HDB", "LTA", "URA"], default=["HDB", "LTA", "URA"])
        
        col3, col4 = st.columns(2)
        with col3:
            min_lots = st.slider("Minimum available lots:", 0, 100, 0)
        with col4:
            status_filter = st.multiselect("Status:", ["Available", "Moderate", "Limited"], default=["Available", "Moderate", "Limited"])
        
        # Search
        search = CarparkSearch(df)
        results = search.advanced_filter(
            query=search_query,
            agencies=agency_filter,
            statuses=status_filter,
            min_lots=min_lots
        )
        
        st.markdown(f"**Found {len(results)} carparks**")
        
        if not results.empty:
            for _, row in results.head(20).iterrows():
                status_color = {"Available": "#22c55e", "Moderate": "#eab308", "Limited": "#ef4444"}.get(row["Status"], "#666")
                agency_color = {"HDB": "#3b82f6", "LTA": "#10b981", "URA": "#f97316"}.get(row["Agency"], "#666")
                
                st.markdown(f"""
                <div class='search-result'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <strong style='color: #f1f5f9;'>{row['Development'][:50]}</strong>
                            <span class='badge' style='background: {agency_color}; margin-left: 10px;'>{row['Agency']}</span>
                        </div>
                        <div style='text-align: right;'>
                            <span style='color: {status_color}; font-size: 1.3rem; font-weight: 700;'>{row['AvailableLots']}</span>
                            <span style='color: #94a3b8;'> lots</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # TAB 2: Find Nearest
    with tab2:
        st.markdown("### 📍 Find Nearest Parking")
        
        col1, col2 = st.columns(2)
        
        with col1:
            location_choice = st.selectbox("📍 Select Location:", ["Custom"] + list(POPULAR_LOCATIONS.keys()))
        
        with col2:
            num_results = st.slider("Number of results:", 5, 20, 10)
        
        if location_choice == "Custom":
            col3, col4 = st.columns(2)
            with col3:
                lat = st.number_input("Latitude:", value=1.3521, format="%.4f")
            with col4:
                lon = st.number_input("Longitude:", value=103.8198, format="%.4f")
        else:
            lat = POPULAR_LOCATIONS[location_choice]["lat"]
            lon = POPULAR_LOCATIONS[location_choice]["lon"]
            st.info(f"📍 {location_choice}: {lat}, {lon}")
        
        min_avail = st.slider("Minimum available lots:", 1, 50, 1)
        
        if st.button("🔍 Find Nearest Parking", use_container_width=True):
            finder = NearestParkingFinder(df)
            nearest = finder.find_nearest(lat, lon, n=num_results, min_availability=min_avail)
            
            if not nearest.empty:
                st.markdown(f"### 🎯 {len(nearest)} Nearest Carparks")
                
                for i, (_, row) in enumerate(nearest.iterrows()):
                    agency_color = {"HDB": "#3b82f6", "LTA": "#10b981", "URA": "#f97316"}.get(row["Agency"], "#666")
                    
                    st.markdown(f"""
                    <div class='search-result'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div>
                                <span style='color: #3b82f6; font-weight: 600;'>#{i+1}</span>
                                <strong style='color: #f1f5f9; margin-left: 10px;'>{row['Development'][:40]}</strong>
                                <span class='badge' style='background: {agency_color};'>{row['Agency']}</span>
                            </div>
                            <div style='text-align: right;'>
                                <span style='color: #22c55e; font-weight: 700;'>{row['AvailableLots']}</span> lots
                                <span style='color: #94a3b8; margin-left: 15px;'>📍 {row['Distance_km']} km</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Show on map
                st.markdown("### 🗺️ Map View")
                m = folium.Map(location=[lat, lon], zoom_start=15, tiles="cartodbdark_matter")
                
                # User location marker
                folium.Marker(
                    [lat, lon],
                    popup="Your Location",
                    icon=folium.Icon(color="red", icon="user")
                ).add_to(m)
                
                # Carpark markers
                for _, row in nearest.iterrows():
                    folium.CircleMarker(
                        [row["Latitude"], row["Longitude"]],
                        radius=8,
                        popup=f"{row['Development']}<br>{row['AvailableLots']} lots<br>{row['Distance_km']} km",
                        color="#22c55e",
                        fill=True,
                        fill_opacity=0.7
                    ).add_to(m)
                
                st_folium(m, width=None, height=400, use_container_width=True)
            else:
                st.warning("No carparks found with the specified criteria.")


# =============================================================================
# ANALYTICS PAGE
# =============================================================================

def render_analytics():
    """Render analytics page."""
    st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <h1>📊 Detailed Analytics</h1>
        <p style='color: #94a3b8;'>In-depth parking analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    df, summary, _ = fetch_parking_data()
    if df is None:
        st.error("❌ Failed to fetch data")
        return
    
    analyzer = get_analyzer()
    chart_viz = ParkingChartVisualizer()
    
    st.markdown("### 🏢 Agency Comparison")
    fig = chart_viz.create_agency_comparison(summary)
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚗 Lot Types")
        fig = chart_viz.create_lot_type_chart(summary)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### ⚠️ Most Stressed")
        stress_df = analyzer.identify_stress_points(df, top_n=10)
        for _, row in stress_df.head(5).iterrows():
            color = "#ef4444" if row["AvailableLots"] <= 5 else "#eab308"
            st.markdown(f"""
            <div style='background: rgba(30,41,59,0.6); padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 3px solid {color};'>
                <strong style='color: #f1f5f9;'>{row['Development'][:35]}</strong>
                <span style='float: right; color: {color}; font-weight: 700;'>{row['AvailableLots']} lots</span>
            </div>
            """, unsafe_allow_html=True)


# =============================================================================
# ALERTS PAGE (NEW!)
# =============================================================================

def render_alerts():
    """Render alerts page."""
    st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <h1>🔔 System Alerts</h1>
        <p style='color: #94a3b8;'>Real-time parking system alerts</p>
    </div>
    """, unsafe_allow_html=True)
    
    df, summary, _ = fetch_parking_data()
    if df is None:
        st.error("❌ Failed to fetch data")
        return
    
    alerts = st.session_state.alert_system.analyze_and_alert(df, summary)
    alert_summary = st.session_state.alert_system.get_alert_summary()
    
    # Summary cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔔 Total Alerts", alert_summary["total"])
    col2.metric("🚨 Critical", alert_summary["critical"])
    col3.metric("⚠️ Warning", alert_summary["warning"])
    col4.metric("ℹ️ Info", alert_summary["info"])
    
    st.divider()
    
    if not alerts:
        st.success("✅ No alerts! System is operating normally.")
    else:
        st.markdown("### 📋 Active Alerts")
        
        for alert in alerts:
            if alert.level.value == "critical":
                css_class = "alert-critical"
                icon = "🚨"
            elif alert.level.value == "warning":
                css_class = "alert-warning"
                icon = "⚠️"
            else:
                css_class = "alert-info"
                icon = "ℹ️"
            
            st.markdown(f"""
            <div class='alert-card {css_class}'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <span style='font-size: 1.2rem;'>{icon}</span>
                        <strong style='color: #f1f5f9; margin-left: 10px;'>{alert.title}</strong>
                    </div>
                    <span style='color: #64748b; font-size: 0.85rem;'>{alert.timestamp.strftime('%H:%M:%S')}</span>
                </div>
                <p style='color: #cbd5e1; margin: 10px 0 0 30px;'>{alert.message}</p>
            </div>
            """, unsafe_allow_html=True)


# =============================================================================
# AI INSIGHTS PAGE
# =============================================================================

def render_ai_insights():
    """Render AI insights page."""
    st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <h1>🤖 AI-Powered Insights</h1>
        <p style='color: #94a3b8;'>Intelligent analysis powered by Llama LLM</p>
    </div>
    """, unsafe_allow_html=True)
    
    df, _, _ = fetch_parking_data()
    if df is None:
        st.error("❌ Failed to fetch data")
        return
    
    analyzer = get_analyzer()
    agent = get_llm_agent()
    
    analysis_type = st.selectbox(
        "🎯 Select Analysis:",
        ["📊 Overall System", "⚠️ Stress Points", "🏢 Agency Comparison", "🚗 Driver Tips"]
    )
    
    if st.button("🤖 Generate AI Analysis", use_container_width=True):
        with st.spinner("🧠 AI is analyzing..."):
            report = analyzer.generate_analysis_report(df)
            
            if "Overall" in analysis_type:
                result = agent.generate_overall_analysis(report)
            elif "Stress" in analysis_type:
                result = agent.explain_stress_points(report["stress_points"], report["agency_analysis"])
            elif "Agency" in analysis_type:
                result = agent.compare_agencies(report["agency_analysis"], report["agency_comparison"])
            else:
                result = agent.generate_driver_recommendations(report)
            
            st.markdown(result)
    
    st.divider()
    
    st.markdown("### 💡 Ask a Question")
    question = st.text_input("Enter your question:", placeholder="e.g., How can we improve URA parking?")
    
    if question and st.button("🔍 Analyze", key="q_btn"):
        with st.spinner("🧠 Analyzing..."):
            report = analyzer.generate_analysis_report(df)
            result = agent.generate_policy_insight(report, question)
            st.markdown(result)


# =============================================================================
# POLICY SIMULATOR PAGE
# =============================================================================

def render_policy_simulator():
    """Render policy simulator page."""
    st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <h1>🎯 Policy Simulator</h1>
        <p style='color: #94a3b8;'>Simulate parking policy impacts</p>
    </div>
    """, unsafe_allow_html=True)
    
    df, _, _ = fetch_parking_data()
    if df is None:
        st.error("❌ Failed to fetch data")
        return
    
    simulator = get_simulator()
    agent = get_llm_agent()
    analyzer = get_analyzer()
    
    baseline = simulator.create_baseline(df)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🅿️ Available", f"{baseline['total_available']:,}")
    col2.metric("📈 Utilization", f"{baseline['utilization_rate']}%")
    col3.metric("⚠️ Stressed", baseline['stressed_carparks'])
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        policy_type = st.selectbox("📋 Policy:", ["💰 Pricing", "🏗️ Capacity", "🎯 URA Intervention"])
    
    with col2:
        if "URA" not in policy_type:
            target = st.selectbox("🏢 Target:", ["All", "HDB", "LTA", "URA"])
        else:
            target = "URA"
    
    if "Pricing" in policy_type:
        change = st.slider("Price Change (%):", -50, 100, 20)
    elif "Capacity" in policy_type:
        change = st.slider("Capacity Change (%):", -30, 50, 15)
    else:
        intervention = st.selectbox("Type:", ["mixed", "pricing", "capacity"])
    
    if st.button("🚀 Run Simulation", use_container_width=True):
        with st.spinner("⚙️ Simulating..."):
            if "Pricing" in policy_type:
                result = simulator.simulate_pricing_policy(df, change, None if target == "All" else target)
            elif "Capacity" in policy_type:
                result = simulator.simulate_capacity_change(df, change, None if target == "All" else target)
            else:
                result = simulator.simulate_ura_intervention(df, intervention)
            
            st.markdown("### 📈 Results")
            if "projected" in result:
                for k, v in result["projected"].items():
                    if isinstance(v, (int, float)):
                        st.write(f"**{k.replace('_', ' ').title()}:** `{v:,.1f}`")
            
            st.divider()
            st.markdown("### 🤖 AI Analysis")
            with st.spinner("🧠 Generating..."):
                report = analyzer.generate_analysis_report(df)
                ai = agent.generate_policy_insight(report, f"Analyze {result.get('scenario_name', 'this policy')}")
                st.markdown(ai)


# =============================================================================
# EXPORT PAGE (NEW!)
# =============================================================================

def render_export():
    """Render export page."""
    st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <h1>📄 Export Reports</h1>
        <p style='color: #94a3b8;'>Download parking data and reports</p>
    </div>
    """, unsafe_allow_html=True)
    
    df, summary, _ = fetch_parking_data()
    if df is None:
        st.error("❌ Failed to fetch data")
        return
    
    analyzer = get_analyzer()
    report = analyzer.generate_analysis_report(df)
    exporter = ReportExporter(df, summary, report)
    
    st.markdown("### 📊 Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class='metric-card'>
            <h3>📄 CSV Data</h3>
            <p style='color: #94a3b8;'>Raw carpark data</p>
        </div>
        """, unsafe_allow_html=True)
        
        csv_data = exporter.to_csv()
        st.download_button(
            "⬇️ Download CSV",
            csv_data,
            file_name=f"parksense_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        st.markdown("""
        <div class='metric-card'>
            <h3>📝 Text Report</h3>
            <p style='color: #94a3b8;'>Summary report</p>
        </div>
        """, unsafe_allow_html=True)
        
        text_report = exporter.generate_text_report()
        st.download_button(
            "⬇️ Download Report",
            text_report,
            file_name=f"parksense_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    st.divider()
    
    st.markdown("### 📋 JSON Export")
    json_data = exporter.generate_json_report()
    st.download_button(
        "⬇️ Download JSON",
        json_data,
        file_name=f"parksense_full_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json",
        use_container_width=True
    )
    
    st.divider()
    
    st.markdown("### 👁️ Preview Report")
    with st.expander("View Text Report"):
        st.code(text_report)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main application."""
    apply_custom_css()
    init_session_state()
    
    if not validate_config():
        st.error("❌ Configuration error. Check .env file.")
        st.stop()
    
    page = render_sidebar()
    
    if page == "🏠 Dashboard":
        render_dashboard()
    elif page == "🗺️ Live Map":
        render_live_map()
    elif page == "🔍 Search & Find":
        render_search_find()
    elif page == "📊 Analytics":
        render_analytics()
    elif page == "🔔 Alerts":
        render_alerts()
    elif page == "🤖 AI Insights":
        render_ai_insights()
    elif page == "🎯 Policy Simulator":
        render_policy_simulator()
    elif page == "📄 Export":
        render_export()


if __name__ == "__main__":
    main()