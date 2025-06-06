"""
Clean Room & Oasis Allocation System - Main Application
A modular Streamlit application for managing office room and Oasis desk allocations.
"""
import streamlit as st
from datetime import timedelta

# Import modules
from config import project_rooms, oasis_config
from week_management import get_current_week
from display import show_current_allocations, show_oasis_allocations
from forms import submit_team_preference, submit_oasis_preference
from admin import admin_controls
from allocate_rooms import run_allocation

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
    
    # Show current week info
    current_week = get_current_week()
    week_end = current_week + timedelta(days=6)
    st.info(f"**Current Week:** {current_week.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📊 Current Allocations")
        
        # Room allocations
        show_current_allocations()
        
        st.divider()
        
        # Oasis allocations
        show_oasis_allocations()
        
        # Allocation buttons
        st.divider()
        st.subheader("🎯 Run Allocations")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🏢 Allocate Rooms", type="primary", use_container_width=True):
                with st.spinner("Running room allocation..."):
                    try:
                        success = run_allocation("rooms")
                        if success:
                            st.success("✅ Room allocation completed!")
                            st.rerun()
                        else:
                            st.error("❌ Room allocation failed.")
                    except Exception as e:
                        st.error(f"❌ Allocation error: {str(e)}")
        
        with col_btn2:
            if st.button("🌴 Allocate Oasis", type="secondary", use_container_width=True):
                with st.spinner("Running Oasis allocation..."):
                    try:
                        success = run_allocation("oasis")
                        if success:
                            st.success("✅ Oasis allocation completed!")
                            st.rerun()
                        else:
                            st.error("❌ Oasis allocation failed.")
                    except Exception as e:
                        st.error(f"❌ Allocation error: {str(e)}")
    
    with col2:
        st.header("📝 Submit Preferences")
        
        # Team preference form
        submit_team_preference()
        
        st.divider()
        
        # Oasis preference form
        submit_oasis_preference()
    
    st.divider()
    
    # Admin section
    admin_controls()

if __name__ == "__main__":
    main()
