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
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2d5aa0 100%);
        padding: 2rem 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Week selection styling */
    .week-info {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f4e79;
        margin-bottom: 1.5rem;
    }
    
    /* Card styling for sections */
    .section-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    /* Button styling improvements */
    .stButton > button {
        border-radius: 8px;
        border: none;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }
    
    /* Table styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Form styling */
    .stForm {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    
    /* Status indicators */
    .status-success {
        background: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 6px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    
    .status-warning {
        background: #fff3cd;
        color: #856404;
        padding: 0.75rem;
        border-radius: 6px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom spacing */
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function."""
    # Professional header with company branding
    st.markdown("""
    <div class="main-header">
        <h1>🏢 Office Room & Oasis Booking System</h1>
        <p style="margin: 0; font-size: 1.1rem; opacity: 0.9;">
            Reserve your workspace efficiently and plan ahead
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Week selection
    current_week = get_current_week()
    next_week = get_next_week()
    
    # Enhanced sidebar with better styling
    with st.sidebar:
        st.markdown("### 📅 Week Selection")
        
        # Add helpful context
        st.markdown("""
        <div style="background: #e3f2fd; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
            <strong>💡 Pro Tip:</strong><br>
            Book for next week every Wednesday-Friday for optimal planning!
        </div>
        """, unsafe_allow_html=True)
        
        selected_week = st.radio(
            "Choose week to view/book:",
            options=[
                ("current", f"This Week ({current_week.strftime('%b %d')} - {(current_week + timedelta(days=6)).strftime('%b %d')})"),
                ("next", f"Next Week ({next_week.strftime('%b %d')} - {(next_week + timedelta(days=6)).strftime('%b %d')})")
            ],
            format_func=lambda x: x[1],
            index=1,  # Default to next week for advance booking
            help="Select which week you want to view or make bookings for"
        )[0]
        
        # Add booking status indicator
        if selected_week == "next":
            from datetime import datetime
            current_weekday = datetime.now().weekday()
            if current_weekday >= 2:  # Wednesday or later
                st.success("✅ Advance booking is open!")
            else:
                st.warning("⏰ Advance booking opens Wednesday")
    
    # Determine the target week
    target_week = next_week if selected_week == "next" else current_week
    week_end = target_week + timedelta(days=6)
    
    # Enhanced week info display
    week_label = "Next Week" if selected_week == "next" else "This Week"
    st.markdown(f"""
    <div class="week-info">
        <h3 style="margin: 0; color: #1f4e79;">📅 {week_label}</h3>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; font-weight: 500;">
            {target_week.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}
        </p>
    </div>
    """, unsafe_allow_html=True)
      # Main content area with enhanced layout
    col1, col2 = st.columns([2.5, 1.5], gap="large")
    
    with col1:
        st.markdown("""
        <div class="section-card">
            <h2 style="color: #1f4e79; margin-top: 0;">📊 Current Allocations</h2>
        """, unsafe_allow_html=True)
        
        # Show allocations for selected week
        show_week_allocations(target_week, selected_week == "next")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Allocation buttons (only show for next week or admins)
        if selected_week == "next" or st.session_state.get("admin_logged_in", False):
            st.markdown("""
            <div class="section-card" style="margin-top: 1.5rem;">
                <h3 style="color: #1f4e79; margin-top: 0;">🎯 Run Allocations</h3>
                <p style="color: #666; margin-bottom: 1.5rem;">
                    Click below to automatically assign rooms and Oasis spots based on submitted preferences.
                </p>
            """, unsafe_allow_html=True)
            
            col_btn1, col_btn2 = st.columns(2, gap="medium")
            
            with col_btn1:
                if st.button("🏢 Allocate Rooms", type="primary", use_container_width=True, help="Assign team rooms based on preferences"):
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
                if st.button("🌴 Allocate Oasis", type="secondary", use_container_width=True, help="Assign Oasis desk spots based on preferences"):
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
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="section-card">
            <h2 style="color: #1f4e79; margin-top: 0;">📝 Submit Preferences</h2>
            <p style="color: #666; margin-bottom: 1.5rem;">
                Submit your workspace preferences for the selected week.
            </p>
        """, unsafe_allow_html=True)
        
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
        
        st.markdown("</div>", unsafe_allow_html=True)    
    # Enhanced admin section
    st.markdown("""
    <div class="section-card" style="margin-top: 2rem;">
        <h3 style="color: #1f4e79; margin-top: 0;">⚙️ Administration</h3>
    """, unsafe_allow_html=True)
    
    admin_controls()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Footer with helpful information
    st.markdown("""
    <div style="margin-top: 3rem; padding: 2rem; background: #f8f9fa; border-radius: 10px; text-align: center;">
        <h4 style="color: #1f4e79; margin-top: 0;">How to Use This System</h4>
        <div style="display: flex; justify-content: space-around; flex-wrap: wrap; margin-top: 1rem;">
            <div style="flex: 1; min-width: 200px; margin: 0.5rem;">
                <h5>📅 Step 1: Choose Week</h5>
                <p>Select current week or next week in the sidebar</p>
            </div>
            <div style="flex: 1; min-width: 200px; margin: 0.5rem;">
                <h5>📝 Step 2: Submit Preferences</h5>
                <p>Fill out team room or Oasis desk preferences</p>
            </div>
            <div style="flex: 1; min-width: 200px; margin: 0.5rem;">
                <h5>🎯 Step 3: Run Allocation</h5>
                <p>Administrators run allocation to assign spots</p>
            </div>
        </div>
        <hr style="margin: 2rem 0; border: none; border-top: 1px solid #dee2e6;">
        <p style="color: #666; margin: 0;">
            <strong>Best Practice:</strong> Submit preferences Wednesday-Friday for the following week
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
