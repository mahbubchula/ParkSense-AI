"""
ParkSense-AI Configuration
==========================
Handles all configuration settings, API keys, and theme colors.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# API KEYS
# =============================================================================

LTA_API_KEY = os.getenv("LTA_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# =============================================================================
# LTA API SETTINGS
# =============================================================================

LTA_BASE_URL = "https://datamall2.mytransport.sg/ltaodataservice"
CARPARK_ENDPOINT = f"{LTA_BASE_URL}/CarParkAvailabilityv2"

# =============================================================================
# LLM SETTINGS (GROQ)
# =============================================================================

LLM_MODELS = {
    "main": "llama-3.3-70b-versatile",      # For detailed analysis
    "fast": "llama-3.1-8b-instant"           # For quick tasks
}

# =============================================================================
# THEME COLORS (AI + Sustainability + Mobility)
# =============================================================================

COLORS = {
    # Primary Theme
    "primary": "#1E3A8A",           # Deep Blue (AI/Tech)
    "secondary": "#10B981",         # Green (Sustainability)
    "accent": "#F97316",            # Orange (Mobility)
    "background": "#0F172A",        # Dark Navy
    "surface": "#1E293B",           # Card Background
    "text": "#F1F5F9",              # Light Gray Text
    "text_secondary": "#94A3B8",    # Muted Text
    
    # Agency Colors
    "HDB": "#3B82F6",               # Blue (Public Housing)
    "LTA": "#10B981",               # Green (Transport Authority)  
    "URA": "#F97316",               # Orange (Urban Planning)
    
    # Status Colors
    "available": "#22C55E",         # Green (Good availability)
    "moderate": "#EAB308",          # Yellow (Moderate)
    "limited": "#EF4444",           # Red (Limited/Full)
}

# =============================================================================
# MAP SETTINGS
# =============================================================================

SINGAPORE_CENTER = [1.3521, 103.8198]  # Singapore coordinates
DEFAULT_ZOOM = 12

# =============================================================================
# VALIDATION
# =============================================================================

def validate_config():
    """Check if all required configurations are set."""
    errors = []
    
    if not LTA_API_KEY:
        errors.append("LTA_API_KEY not found in .env file")
    
    if not GROQ_API_KEY:
        errors.append("GROQ_API_KEY not found in .env file")
    
    if errors:
        for error in errors:
            print(f"❌ Config Error: {error}")
        return False
    
    print("✅ Configuration loaded successfully!")
    print(f"   LTA API Key: {LTA_API_KEY[:10]}...")
    print(f"   Groq API Key: {GROQ_API_KEY[:10]}...")
    return True


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("Testing ParkSense-AI Configuration")
    print("=" * 50)
    validate_config()