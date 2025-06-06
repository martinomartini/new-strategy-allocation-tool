"""
Admin control functions for the Room Allocation System.
"""
import streamlit as st
import pandas as pd
from datetime import timedelta
from database import execute_query
from week_management import get_current_week, get_next_monday, prepare_next_week, force_open_submissions
from analytics import get_weekly_usage_stats, get_all_time_usage_stats, get_user_analytics
from allocate_rooms import run_allocation
from config import ADMIN_PASSWORD

def view_current_submissions():
    """Display and allow editing of current week submissions."""
    st.subheader("📋 Current Submissions")
    
    # Team submissions
    team_query = """
        SELECT team_name, contact_person, team_size, preferred_days, submission_time 
        FROM weekly_preferences 
        ORDER BY submission_time DESC
    """
    team_submissions = execute_query(team_query, fetch_all=True)
    
    if team_submissions:
        st.write("**🏢 Team Room Preferences:**")
        team_df = pd.DataFrame(team_submissions)
        
        # Make it editable
        edited_teams = st.data_editor(
            team_df,
            use_container_width=True,
            num_rows="dynamic",
            key="team_submissions_editor"
        )
        
        if st.button("💾 Save Team Changes"):
            # Clear existing and insert updated data
            execute_query("DELETE FROM weekly_preferences")
            for _, row in edited_teams.iterrows():
                insert_query = """
                    INSERT INTO weekly_preferences (team_name, contact_person, team_size, preferred_days, submission_time) 
                    VALUES (%s, %s, %s, %s, %s)
                """
                execute_query(insert_query, (
                    row['team_name'], row['contact_person'], 
                    row['team_size'], row['preferred_days'], row['submission_time']
                ))
            st.success("Team preferences updated!")
            st.rerun()
    else:
        st.info("No team submissions yet.")
    
    st.divider()
    
    # Oasis submissions
    oasis_query = """
        SELECT person_name, preferred_day_1, preferred_day_2, preferred_day_3, 
               preferred_day_4, preferred_day_5, submission_time 
        FROM oasis_preferences 
        ORDER BY submission_time DESC
    """
    oasis_submissions = execute_query(oasis_query, fetch_all=True)
    
    if oasis_submissions:
        st.write("**🌴 Oasis Desk Preferences:**")
        oasis_df = pd.DataFrame(oasis_submissions)
        
        # Make it editable
        edited_oasis = st.data_editor(
            oasis_df,
            use_container_width=True,
            num_rows="dynamic",
            key="oasis_submissions_editor"
        )
        
        if st.button("💾 Save Oasis Changes"):
            # Clear existing and insert updated data
            execute_query("DELETE FROM oasis_preferences")
            for _, row in edited_oasis.iterrows():
                insert_query = """
                    INSERT INTO oasis_preferences 
                    (person_name, preferred_day_1, preferred_day_2, preferred_day_3, preferred_day_4, preferred_day_5, submission_time) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                execute_query(insert_query, (
                    row['person_name'], row['preferred_day_1'], row['preferred_day_2'],
                    row['preferred_day_3'], row['preferred_day_4'], row['preferred_day_5'], 
                    row['submission_time']
                ))
            st.success("Oasis preferences updated!")
            st.rerun()
    else:
        st.info("No Oasis submissions yet.")

def view_current_allocations_admin():
    """Display and allow editing of current allocations."""
    st.subheader("🎯 Current Allocations")
    
    current_week = get_current_week()
    
    # Room allocations
    room_alloc_query = """
        SELECT team_name, room_name, date 
        FROM weekly_allocations 
        WHERE date >= %s AND date <= %s AND room_name != 'Oasis'
        ORDER BY date, room_name
    """
    start_date = current_week
    end_date = current_week + timedelta(days=3)
    
    room_allocations = execute_query(room_alloc_query, (start_date, end_date), fetch_all=True)
    
    if room_allocations:
        st.write("**🏢 Room Allocations:**")
        room_alloc_df = pd.DataFrame(room_allocations)
        
        # Make it editable
        edited_rooms = st.data_editor(
            room_alloc_df,
            use_container_width=True,
            num_rows="dynamic",
            key="room_allocations_editor"
        )
        
        if st.button("💾 Save Room Allocation Changes"):
            # Clear existing room allocations and insert updated data
            execute_query("DELETE FROM weekly_allocations WHERE room_name != 'Oasis'")
            for _, row in edited_rooms.iterrows():
                insert_query = """
                    INSERT INTO weekly_allocations (team_name, room_name, date) 
                    VALUES (%s, %s, %s)
                """
                execute_query(insert_query, (row['team_name'], row['room_name'], row['date']))
            st.success("Room allocations updated!")
            st.rerun()
    else:
        st.info("No room allocations yet.")
    
    st.divider()
    
    # Oasis allocations
    oasis_alloc_query = """
        SELECT person_name, date 
        FROM oasis_allocations 
        WHERE date >= %s AND date <= %s
        ORDER BY date, person_name
    """
    oasis_end_date = current_week + timedelta(days=4)  # Include Friday
    
    oasis_allocations = execute_query(oasis_alloc_query, (start_date, oasis_end_date), fetch_all=True)
    
    if oasis_allocations:
        st.write("**🌴 Oasis Allocations:**")
        oasis_alloc_df = pd.DataFrame(oasis_allocations)
        
        # Make it editable
        edited_oasis_alloc = st.data_editor(
            oasis_alloc_df,
            use_container_width=True,
            num_rows="dynamic",
            key="oasis_allocations_editor"
        )
        
        if st.button("💾 Save Oasis Allocation Changes"):
            # Clear existing Oasis allocations and insert updated data
            execute_query("DELETE FROM oasis_allocations")
            for _, row in edited_oasis_alloc.iterrows():
                insert_query = """
                    INSERT INTO oasis_allocations (person_name, date) 
                    VALUES (%s, %s)
                """
                execute_query(insert_query, (row['person_name'], row['date']))
            st.success("Oasis allocations updated!")
            st.rerun()
    else:
        st.info("No Oasis allocations yet.")

def admin_controls():
    """Enhanced admin controls with weekly management."""
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False
    
    if not st.session_state.admin_logged_in:
        with st.form("admin_login"):
            password = st.text_input("Admin Password", type="password")
            login = st.form_submit_button("Login")
            
            if login:
                if password == ADMIN_PASSWORD:
                    st.session_state.admin_logged_in = True
                    st.success("Admin access granted!")
                    st.rerun()
                else:
                    st.error("Invalid password.")
    else:
        st.success("👨‍💼 Admin Controls")
        
        # Show current week info
        current_week = get_current_week()
        next_week = get_next_monday()
        st.info(f"**Current Week:** {current_week.strftime('%B %d, %Y')} | **Next Week:** {next_week.strftime('%B %d, %Y')}")
        
        # Admin sections in columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⏰ Submission Control")
            if st.button("🔓 Force Open Submissions", help="Allow submissions regardless of time restrictions"):
                force_open_submissions(True)
                st.success("✅ Submissions forced open!")
                st.rerun()
            
            if st.button("🔒 Restore Normal Schedule", help="Return to normal submission schedule"):
                force_open_submissions(False)
                st.success("✅ Normal submission schedule restored!")
                st.rerun()
            
            st.divider()
            
            st.subheader("🗓️ Week Management")
            if st.button("➡️ Advance to Next Week", help="Archive current data and move to next week"):
                new_week = prepare_next_week()
                st.success(f"✅ Advanced to week of {new_week.strftime('%B %d, %Y')}")
                st.rerun()
            
            new_week_date = st.date_input("Set Custom Week Start (Monday):", value=current_week)
            if st.button("📅 Set Week"):
                if new_week_date.weekday() == 0:  # Monday
                    from week_management import set_current_week
                    set_current_week(new_week_date)
                    st.success(f"✅ Week set to {new_week_date.strftime('%B %d, %Y')}")
                    st.rerun()
                else:
                    st.error("Please select a Monday.")
        
        with col2:
            st.subheader("🎯 Room Allocation")
            if st.button("🔄 Run Room Allocation", help="Execute room allocation algorithm"):
                try:
                    result = run_allocation()
                    if result:
                        st.success("✅ Room allocation completed successfully!")
                    else:
                        st.error("❌ Room allocation failed!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Allocation error: {str(e)}")
            
            if st.button("📊 Show Current Week Analytics"):
                stats = get_weekly_usage_stats()
                st.json(stats)
            
            if st.button("📈 Show All-Time Analytics"):
                all_time_stats = get_all_time_usage_stats()
                user_stats = get_user_analytics()
                
                st.subheader("📊 All-Time Usage Statistics")
                
                # Room statistics
                if all_time_stats['room_stats']:
                    st.write("**🏢 Room Usage (All Time):**")
                    room_df = pd.DataFrame(all_time_stats['room_stats'])
                    st.dataframe(room_df, use_container_width=True)
                
                # Oasis statistics
                if all_time_stats['oasis_stats']:
                    st.write("**🌴 Oasis Usage (All Time):**")
                    oasis_df = pd.DataFrame([all_time_stats['oasis_stats']])
                    st.dataframe(oasis_df, use_container_width=True)
                
                # Weekly trends
                if all_time_stats['weekly_trends']:
                    st.write("**📈 Weekly Trends:**")
                    trends_df = pd.DataFrame(all_time_stats['weekly_trends'])
                    st.line_chart(trends_df.set_index('week_start'))
                
                # User analytics
                if user_stats['combined_analytics']:
                    st.write("**👥 Individual User Analytics:**")
                    users_df = pd.DataFrame(user_stats['combined_analytics'])
                    st.dataframe(users_df, use_container_width=True)
        
        st.divider()
        
        # Data Management Section
        st.subheader("📋 Data Management")
        col3, col4 = st.columns(2)
        
        with col3:
            if st.button("📝 View & Edit Submissions"):
                view_current_submissions()
        
        with col4:
            if st.button("🎯 View & Edit Allocations"):
                view_current_allocations_admin()
        
        st.divider()
        
        if st.button("🚪 Admin Logout"):
            st.session_state.admin_logged_in = False
            st.rerun()
