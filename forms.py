"""
Form submission functions for the Room Allocation System.
"""
import streamlit as st
from datetime import timedelta
from database import execute_query
from week_management import get_current_week, get_submission_status

def submit_team_preference():
    """Form for submitting team preferences."""
    st.subheader("🏢 Submit Team Room Preference")
    
    # Check submission window
    submissions_allowed, status_message = get_submission_status()
    st.info(status_message)
    
    if not submissions_allowed:
        st.warning("⏰ Submissions are currently closed. Please submit your preferences Tuesday-Thursday until 16:00.")
        return
    
    current_week_monday = get_current_week()
    week_end = current_week_monday + timedelta(days=6)
    st.write(f"**Submitting for week:** {current_week_monday.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}")
    
    with st.form("team_preference_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            team_name = st.text_input("Team Name*", help="Enter your team name")
            contact_person = st.text_input("Contact Person*", help="Primary contact for the team")
        
        with col2:
            team_size = st.number_input("Team Size*", min_value=1, max_value=10, value=4)
            
            # Day preference selection
            st.write("**Preferred Days*** (Select one pair)")
            mw_selected = st.checkbox("Monday & Wednesday")
            tt_selected = st.checkbox("Tuesday & Thursday")
        
        submitted = st.form_submit_button("Submit Team Preference", type="primary")
        
        if submitted:
            # Double-check submission window
            submissions_allowed, _ = get_submission_status()
            if not submissions_allowed:
                st.error("⏰ Submission window has closed while you were filling the form. Please try again during the allowed time.")
                return
            
            # Validation
            if not team_name or not contact_person:
                st.error("Please fill in all required fields.")
                return
            
            # Check day selection
            if mw_selected and tt_selected:
                st.error("Please select only one day pair.")
                return
            if not mw_selected and not tt_selected:
                st.error("Please select a day pair.")
                return
            
            preferred_days = "Monday,Wednesday" if mw_selected else "Tuesday,Thursday"
            
            # Check if team already exists
            check_query = "SELECT 1 FROM weekly_preferences WHERE team_name = %s"
            existing = execute_query(check_query, (team_name,), fetch_one=True)
            
            if existing:
                st.error(f"Team '{team_name}' has already submitted a preference.")
                return
            
            # Insert preference
            insert_query = """
                INSERT INTO weekly_preferences (team_name, contact_person, team_size, preferred_days, submission_time) 
                VALUES (%s, %s, %s, %s, NOW() AT TIME ZONE 'UTC')
            """
            success = execute_query(insert_query, (team_name, contact_person, team_size, preferred_days))
            
            if success:
                st.success(f"✅ Preference submitted successfully for {team_name}!")
                st.rerun()
            else:
                st.error("Failed to submit preference. Please try again.")

def submit_oasis_preference():
    """Form for submitting Oasis preferences."""
    st.subheader("🌴 Submit Oasis Desk Preference")
    
    # Check submission window
    submissions_allowed, status_message = get_submission_status()
    st.info(status_message)
    
    if not submissions_allowed:
        st.warning("⏰ Submissions are currently closed. Please submit your preferences Tuesday-Thursday until 16:00.")
        return
    
    current_week_monday = get_current_week()
    week_end = current_week_monday + timedelta(days=6)
    st.write(f"**Submitting for week:** {current_week_monday.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}")
    
    with st.form("oasis_preference_form"):
        person_name = st.text_input("Your Name*", help="Enter your full name")
        st.write("**Select your preferred days** (up to 5 days)")
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        selected_days = []
        
        cols = st.columns(5)
        for i, day in enumerate(days):
            with cols[i]:
                if st.checkbox(day):
                    selected_days.append(day)
        
        submitted = st.form_submit_button("Submit Oasis Preference", type="primary")
        
        if submitted:
            # Double-check submission window
            submissions_allowed, _ = get_submission_status()
            if not submissions_allowed:
                st.error("⏰ Submission window has closed while you were filling the form. Please try again during the allowed time.")
                return
            
            if not person_name:
                st.error("Please enter your name.")
                return
            
            if not selected_days:
                st.error("Please select at least one day.")
                return
            
            # Check if person already exists
            check_query = "SELECT 1 FROM oasis_preferences WHERE person_name = %s"
            existing = execute_query(check_query, (person_name,), fetch_one=True)
            
            if existing:
                st.error("You have already submitted a preference.")
                return
            
            # Pad days to 5 elements
            padded_days = selected_days + [None] * (5 - len(selected_days))
            # Insert preference
            insert_query = """
                INSERT INTO oasis_preferences 
                (person_name, preferred_day_1, preferred_day_2, preferred_day_3, preferred_day_4, preferred_day_5, submission_time) 
                VALUES (%s, %s, %s, %s, %s, %s, NOW() AT TIME ZONE 'UTC')
            """
            success = execute_query(insert_query, (person_name.strip(), *padded_days))
            
            if success:
                st.success(f"✅ Oasis preference submitted successfully for {person_name}!")
                st.rerun()
            else:
                st.error("Failed to submit preference. Please try again.")
