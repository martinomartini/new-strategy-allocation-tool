"""
Form submission functions for the Room Allocation System.
"""
import streamlit as st
from datetime import timedelta, datetime
from .database import execute_query
from .week_management import get_current_week, get_submission_status

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

def submit_advance_team_preference(target_week):
    """Form for submitting team preferences for next week."""
    st.subheader("🏢 Submit Team Room Preference")
    
    # Show submission window and week info
    week_end = target_week + timedelta(days=6)
    st.write(f"**Booking for week:** {target_week.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}")
    
    # Check if booking window is open (allow booking from Wednesday to Friday for next week)
    current_date = datetime.now().date()
    current_weekday = current_date.weekday()  # 0=Monday, 6=Sunday
    
    # Allow booking Wednesday (2) through Sunday (6) for next week
    booking_allowed = current_weekday >= 2
    
    if not booking_allowed:
        st.warning("⏰ Advance booking opens on Wednesday for the following week.")
        return
    
    st.success("✅ Advance booking is now open!")
    
    with st.form(f"advance_team_preference_form_{target_week.isoformat()}"):
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
            
            # Check if team already exists for this week
            check_query = "SELECT 1 FROM weekly_preferences WHERE team_name = %s AND week_monday = %s"
            existing = execute_query(check_query, (team_name, target_week), fetch_one=True)
            
            if existing:
                st.error(f"Team '{team_name}' has already submitted a preference for this week.")
                return
            
            # Insert preference with week_monday
            insert_query = """
                INSERT INTO weekly_preferences (team_name, contact_person, team_size, preferred_days, week_monday, submission_time) 
                VALUES (%s, %s, %s, %s, %s, NOW() AT TIME ZONE 'UTC')
            """
            success = execute_query(insert_query, (team_name, contact_person, team_size, preferred_days, target_week))
            
            if success:
                st.success(f"✅ Preference submitted successfully for {team_name}!")
                st.rerun()
            else:
                st.error("Failed to submit preference. Please try again.")

def submit_advance_oasis_preference(target_week):
    """Form for submitting Oasis preferences for next week."""
    st.subheader("🌴 Submit Oasis Desk Preference")
    
    # Show submission window and week info
    week_end = target_week + timedelta(days=6)
    st.write(f"**Booking for week:** {target_week.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}")
    
    # Check if booking window is open
    current_date = datetime.now().date()
    current_weekday = current_date.weekday()
    
    booking_allowed = current_weekday >= 2
    
    if not booking_allowed:
        st.warning("⏰ Advance booking opens on Wednesday for the following week.")
        return
    
    st.success("✅ Advance booking is now open!")
    
    with st.form(f"advance_oasis_preference_form_{target_week.isoformat()}"):
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
            if not person_name:
                st.error("Please enter your name.")
                return
            
            if not selected_days:
                st.error("Please select at least one day.")
                return
            
            # Check if person already exists for this week
            check_query = "SELECT 1 FROM oasis_preferences WHERE person_name = %s AND week_monday = %s"
            existing = execute_query(check_query, (person_name, target_week), fetch_one=True)
            
            if existing:
                st.error("You have already submitted a preference for this week.")
                return
            
            # Pad days to 5 elements
            padded_days = selected_days + [None] * (5 - len(selected_days))
            # Insert preference with week_monday
            insert_query = """
                INSERT INTO oasis_preferences 
                (person_name, preferred_day_1, preferred_day_2, preferred_day_3, preferred_day_4, preferred_day_5, week_monday, submission_time) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW() AT TIME ZONE 'UTC')
            """
            success = execute_query(insert_query, (person_name.strip(), *padded_days, target_week))
            
            if success:
                st.success(f"✅ Oasis preference submitted successfully for {person_name}!")
                st.rerun()
            else:
                st.error("Failed to submit preference. Please try again.")
