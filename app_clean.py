"""
Clean Room & Oasis Allocation System - Main Application
A modular Streamlit application for managing office room and Oasis desk allocations.
"""
import streamlit as st
from datetime import timedelta, date

# Import modules
from config import PROJECT_ROOMS, OASIS_CONFIG
from week_management import get_current_week, get_next_week
from display import show_current_allocations, show_oasis_allocations, show_week_allocations
from forms import submit_team_preference, submit_oasis_preference, submit_advance_team_preference, submit_advance_oasis_preference
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
    
    # Week selection
    current_week = get_current_week()
    next_week = get_next_week()
    
    # Add week selector in sidebar
    with st.sidebar:
        st.header("📅 Week Selection")
        selected_week = st.radio(
            "Choose week to view/book:",
            options=[
                ("current", f"This Week ({current_week.strftime('%b %d')} - {(current_week + timedelta(days=6)).strftime('%b %d')})"),
                ("next", f"Next Week ({next_week.strftime('%b %d')} - {(next_week + timedelta(days=6)).strftime('%b %d')})")
            ],
            format_func=lambda x: x[1],
            index=1  # Default to next week for advance booking
        )[0]
    
    # Determine the target week
    target_week = next_week if selected_week == "next" else current_week
    week_end = target_week + timedelta(days=6)
    
    # Display current week info
    week_label = "Next Week" if selected_week == "next" else "This Week"
    st.info(f"**{week_label}:** {target_week.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}")
    
    # Main content area
    col1, col2 = st.columns([2, 1])    
    with col1:
        st.header("📊 Current Allocations")
        
        # Show allocations for selected week
        show_week_allocations(target_week, selected_week == "next")
        
        # Allocation buttons (only show for next week or admins)
        if selected_week == "next" or st.session_state.get("admin_logged_in", False):
            st.divider()
            st.subheader("🎯 Run Allocations")
            
            col_btn1, col_btn2 = st.columns(2)            
            with col_btn1:
                if st.button("🏢 Allocate Rooms", type="primary", use_container_width=True):
                    with st.spinner("Running room allocation..."):
                        try:
                            from config import DATABASE_URL
                            success, messages = run_allocation(DATABASE_URL, "project", target_week)
                            if success:
                                st.success("✅ Room allocation completed!")
                                st.rerun()
                            else:
                                st.error("❌ Room allocation failed.")
                                if messages:
                                    for msg in messages:
                                        st.error(msg)
                        except Exception as e:
                            st.error(f"❌ Allocation error: {str(e)}")
            
            with col_btn2:
                if st.button("🌴 Allocate Oasis", type="secondary", use_container_width=True):
                    with st.spinner("Running Oasis allocation..."):
                        try:
                            from config import DATABASE_URL
                            success, messages = run_allocation(DATABASE_URL, "oasis", target_week)
                            if success:
                                st.success("✅ Oasis allocation completed!")
                                st.rerun()
                            else:
                                st.error("❌ Oasis allocation failed.")
                                if messages:
                                    for msg in messages:
                                        st.error(msg)
                        except Exception as e:
                            st.error(f"❌ Allocation error: {str(e)}")
    
    with col2:
        st.header("📝 Submit Preferences")
        
        if selected_week == "next":
            # Advance booking forms for next week
            submit_advance_team_preference(target_week)
            st.divider()
            submit_advance_oasis_preference(target_week)
        else:
            # Current week forms (keep for admin/current week use)
            submit_team_preference()
            st.divider()
            submit_oasis_preference()
    
    st.divider()
    
    # Admin section
    admin_controls()

if __name__ == "__main__":
    main()
