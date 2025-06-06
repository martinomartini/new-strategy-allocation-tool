"""
Configuration and constants for the Room Allocation System.
"""
import streamlit as st
import pytz
import json
import os

# -----------------------------------------------------
# Global Constants and Configuration
# -----------------------------------------------------

# Database Configuration
DATABASE_URL = "postgresql://postgres.orrpkvjajaslmsqpaecu:KPMGtrainee123!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"
# DATABASE_URL = st.secrets.get("SUPABASE_DB_URI", os.environ.get("SUPABASE_DB_URI"))

# Timezone Configuration
OFFICE_TIMEZONE_STR = st.secrets.get("OFFICE_TIMEZONE", os.environ.get("OFFICE_TIMEZONE", "UTC"))
try:
    OFFICE_TIMEZONE = pytz.timezone(OFFICE_TIMEZONE_STR)
except pytz.UnknownTimeZoneError:
    st.error(f"Invalid Timezone: '{OFFICE_TIMEZONE_STR}', defaulting to UTC.")
    OFFICE_TIMEZONE = pytz.utc

# Admin Configuration
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin123")

# Room Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOMS_FILE = os.path.join(BASE_DIR, 'rooms.json')

def load_room_configuration():
    """Load room configuration from JSON file."""
    try:
        with open(ROOMS_FILE, 'r') as f:
            available_rooms = json.load(f)
    except FileNotFoundError:
        st.error(f"Error: {ROOMS_FILE} not found.")
        available_rooms = []
    
    # Get room configurations
    project_rooms = [r for r in available_rooms if r.get("name") != "Oasis" and "capacity" in r and "name" in r]
    oasis_config = next((r for r in available_rooms if r.get("name") == "Oasis"), {"name": "Oasis", "capacity": 15})
    
    return available_rooms, project_rooms, oasis_config

# Load room configurations
AVAILABLE_ROOMS, PROJECT_ROOMS, OASIS_CONFIG = load_room_configuration()
