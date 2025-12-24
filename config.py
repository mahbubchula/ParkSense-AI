"""
ParkSense-AI Configuration
==========================
Handles all configuration settings, API keys, and theme colors.
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# =============================================================================
# API KEYS (Works both locally and on Streamlit Cloud)
# =============================================================================

def get_api_key(key_name: str) -> str:
    """Get API key from Streamlit secrets or environment variables."""
    # Try Streamlit secrets first (for cloud deployment)
    try:
        return st.secrets[key_name]
    except:
        pass
    
    # Fall back to environment variables (for local development)
    return os.getenv(key_name, "")

LTA_API_KEY = get_api_key("LTA_API_KEY")
GROQ_API_KEY = get_api_key("GROQ_API_KEY")

# =============================================================================
# LTA API SETTINGS
# =============================================================================

LTA_BASE_URL = "https://datamall2.mytransport.sg/ltaodataservice"
CARPARK_ENDPOINT = f"{LTA_BASE_URL}/CarParkAvailabilityv2"

# =============================================================================
# LLM SETTINGS (GROQ)
# =============================================================================

LLM_MODELS = {
    "main": "llama-3.3-70b-versatile",
    "fast": "llama-3.1-8b-instant"
}

# =============================================================================
# THEME COLORS
# =============================================================================

COLORS = {
    "primary": "#1E3A8A",
    "secondary": "#10B981",
    "accent": "#F97316",
    "background": "#0F172A",
    "surface": "#1E293B",
    "text": "#F1F5F9",
    "text_secondary": "#94A3B8",
    
    "HDB": "#3B82F6",
    "LTA": "#10B981",
    "URA": "#F97316",
    
    "available": "#22C55E",
    "moderate": "#EAB308",
    "limited": "#EF4444",
}

# =============================================================================
# MAP SETTINGS
# =============================================================================

SINGAPORE_CENTER = [1.3521, 103.8198]
DEFAULT_ZOOM = 12

# =============================================================================
# VALIDATION
# =============================================================================

def validate_config():
    """Check if all required configurations are set."""
    errors = []
    
    if not LTA_API_KEY:
        errors.append("LTA_API_KEY not found")
    
    if not GROQ_API_KEY:
        errors.append("GROQ_API_KEY not found")
    
    if errors:
        for error in errors:
            print(f"❌ Config Error: {error}")
        return False
    
    return True


if __name__ == "__main__":
    print("Testing ParkSense-AI Configuration")
    print("=" * 50)
    validate_config()