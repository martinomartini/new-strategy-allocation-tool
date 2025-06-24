"""
Main Streamlit application for the Office Room & Oasis Booking System.
Modular structure for better maintainability.
"""
import streamlit as st

# Import all modules
from config import PROJECT_ROOMS, OASIS_CONFIG
from display import show_current_allocations, show_oasis_allocations
from forms import submit_team_preference, submit_oasis_preference
from admin import admin_controls

# Configure page (MUST BE FIRST STREAMLIT COMMAND)
st.set_page_config(
    page_title="Office Room & Oasis Booking",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def main():
    """Main application function."""
    
    # Header
    st.title("🏢 Office Room & Oasis Booking System")
    st.markdown("---")
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📅 Current Allocations", "📝 Submit Preferences", "👨‍💼 Admin"])
    
    with tab1:
        st.header("📅 Current Allocations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            show_current_allocations()
        
        with col2:
            show_oasis_allocations()
    
    with tab2:
        st.header("📝 Submit Your Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            submit_team_preference()
        
        with col2:
            submit_oasis_preference()
    
    st.divider()
    
    # Admin section
    admin_controls()

if __name__ == "__main__":
    main()
