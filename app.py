import streamlit as st
import psycopg2
import psycopg2.pool
import json
import os
from datetime import datetime, timedelta, date
import pytz
import pandas as pd
from psycopg2.extras import RealDictCursor
from allocate_rooms import run_allocation

# Configure page (MUST BE FIRST STREAMLIT COMMAND)
st.set_page_config(
    page_title="Office Room & Oasis Booking",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------
# Configuration and Global Constants
# -----------------------------------------------------
# Temporarily use hardcoded connection string for debugging
DATABASE_URL = "postgresql://postgres.orrpkvjajaslmsqpaecu:KPMGtrainee123!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"
# DATABASE_URL = st.secrets.get("SUPABASE_DB_URI", os.environ.get("SUPABASE_DB_URI"))
OFFICE_TIMEZONE_STR = st.secrets.get("OFFICE_TIMEZONE", os.environ.get("OFFICE_TIMEZONE", "UTC"))
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin123")

try:
    OFFICE_TIMEZONE = pytz.timezone(OFFICE_TIMEZONE_STR)
except pytz.UnknownTimeZoneError:
    st.error(f"Invalid Timezone: '{OFFICE_TIMEZONE_STR}', defaulting to UTC.")
    OFFICE_TIMEZONE = pytz.utc

# Load room configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOMS_FILE = os.path.join(BASE_DIR, 'rooms.json')
try:
    with open(ROOMS_FILE, 'r') as f:
        AVAILABLE_ROOMS = json.load(f)
except FileNotFoundError:
    st.error(f"Error: {ROOMS_FILE} not found.")
    AVAILABLE_ROOMS = []

# Get room configurations
project_rooms = [r for r in AVAILABLE_ROOMS if r.get("name") != "Oasis" and "capacity" in r and "name" in r]
oasis_config = next((r for r in AVAILABLE_ROOMS if r.get("name") == "Oasis"), {"name": "Oasis", "capacity": 15})

# Week Management - Dynamic week handling
def get_current_week():
    """Get current active week from database or default."""
    query = "SELECT setting_value FROM admin_settings WHERE setting_key = 'current_week_monday'"
    result = execute_query(query, fetch_one=True)
    
    if result and result['setting_value']:
        return datetime.strptime(result['setting_value'], '%Y-%m-%d').date()
    else:
        # Default to next Monday if no week is set
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:  # Today is Monday
            default_week = today
        else:
            default_week = today + timedelta(days=days_until_monday)
        set_current_week(default_week)
        return default_week

def get_next_monday():
    """Get the next Monday after current week."""
    current_week = get_current_week()
    return current_week + timedelta(days=7)

def prepare_next_week():
    """Advance to next week and archive current data."""
    next_week = get_next_monday()
    
    # Create archive tables if they don't exist
    create_archive_tables()
    
    # Archive current week's data (for historical tracking)
    archive_query = """
        INSERT INTO weekly_archive (week_monday, team_name, contact_person, team_size, preferred_days, submission_time)
        SELECT %s, team_name, contact_person, team_size, preferred_days, submission_time 
        FROM weekly_preferences
    """
    execute_query(archive_query, (get_current_week(),))
    
    # Archive Oasis preferences
    archive_oasis_query = """
        INSERT INTO oasis_archive (week_monday, person_name, preferred_day_1, preferred_day_2, preferred_day_3, preferred_day_4, preferred_day_5, submission_time)
        SELECT %s, person_name, preferred_day_1, preferred_day_2, preferred_day_3, preferred_day_4, preferred_day_5, submission_time 
        FROM oasis_preferences
    """
    execute_query(archive_oasis_query, (get_current_week(),))
    
    # Clear current preferences and allocations
    clear_queries = [
        "DELETE FROM weekly_allocations",
        "DELETE FROM oasis_allocations", 
        "DELETE FROM weekly_preferences",
        "DELETE FROM oasis_preferences"
    ]
    for query in clear_queries:
        execute_query(query)
    
    # Set next week as current
    set_current_week(next_week)
    
    return next_week

def create_archive_tables():
    """Create archive tables for historical data."""
    archive_tables = [
        """
        CREATE TABLE IF NOT EXISTS weekly_archive (
            id SERIAL PRIMARY KEY,
            week_monday DATE NOT NULL,
            team_name VARCHAR(255) NOT NULL,
            contact_person VARCHAR(255),
            team_size INT,
            preferred_days VARCHAR(255),
            submission_time TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS oasis_archive (
            id SERIAL PRIMARY KEY,
            week_monday DATE NOT NULL,
            person_name VARCHAR(255) NOT NULL,
            preferred_day_1 VARCHAR(50),
            preferred_day_2 VARCHAR(50),
            preferred_day_3 VARCHAR(50),
            preferred_day_4 VARCHAR(50),
            preferred_day_5 VARCHAR(50),
            submission_time TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    ]
    for query in archive_tables:
        execute_query(query)

def set_current_week(week_monday):
    """Set the current active week in database."""
    # Ensure admin_settings table exists
    create_table_query = """
        CREATE TABLE IF NOT EXISTS admin_settings (
            setting_key VARCHAR(255) PRIMARY KEY,
            setting_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    execute_query(create_table_query)
    
    # Set the current week
    query = """
        INSERT INTO admin_settings (setting_key, setting_value, updated_at) 
        VALUES ('current_week_monday', %s, CURRENT_TIMESTAMP)
        ON CONFLICT (setting_key) 
        DO UPDATE SET setting_value = EXCLUDED.setting_value, updated_at = CURRENT_TIMESTAMP
    """
    execute_query(query, (week_monday.isoformat(),))

def get_submission_status():
    """Check if submissions are currently allowed."""
    now = datetime.now(OFFICE_TIMEZONE)
    current_weekday = now.weekday()  # 0 = Monday, 6 = Sunday
    current_hour = now.hour
    
    # Allow submissions Tuesday (1) through Thursday (3) until 16:00
    if current_weekday == 1:  # Tuesday
        return True, "✅ Submissions open (Tuesday)"
    elif current_weekday == 2:  # Wednesday  
        return True, "✅ Submissions open (Wednesday)"
    elif current_weekday == 3 and current_hour < 16:  # Thursday before 16:00
        return True, "✅ Submissions open (Thursday until 16:00)"
    elif current_weekday == 3 and current_hour >= 16:  # Thursday after 16:00
        return False, "🔒 Submissions closed (Thursday 16:00 passed - allocation time!)"
    else:
        return False, f"🔒 Submissions closed (Open Tuesday-Thursday 16:00)"

# -----------------------------------------------------
# Database Connection Pool
# -----------------------------------------------------
@st.cache_resource
def get_db_connection_pool():
    if not DATABASE_URL:
        st.error("Database URL is not configured. Please set SUPABASE_DB_URI.")
        return None
    try:
        return psycopg2.pool.SimpleConnectionPool(1, 10, dsn=DATABASE_URL)
    except Exception as e:
        st.error(f"Failed to create database connection pool: {e}")
        return None

# -----------------------------------------------------
# Database Operations
# -----------------------------------------------------
def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """Execute database query with proper connection handling."""
    pool = get_db_connection_pool()
    if not pool:
        return None
    
    conn = None
    try:
        conn = pool.getconn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch_one:
                return cur.fetchone()
            elif fetch_all:
                return cur.fetchall()
            else:
                conn.commit()
                return True
    except Exception as e:
        if conn:
            conn.rollback()
        st.error(f"Database error: {e}")
        return None
    finally:
        if conn:
            pool.putconn(conn)

# -----------------------------------------------------
# Display Functions
# -----------------------------------------------------
def show_current_allocations():
    """Display current room allocations."""
    st.subheader("📅 Current Room Allocations")
    
    current_week_monday = get_current_week()
    
    # Show week info
    week_end = current_week_monday + timedelta(days=6)
    st.info(f"**Week of:** {current_week_monday.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}")
    
    # Create date mapping for the week
    day_mapping = {
        current_week_monday + timedelta(days=i): day 
        for i, day in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday"])
    }
    
    # Initialize grid with project rooms
    room_names = [r["name"] for r in project_rooms]
    grid = {room: {"Room": room, **{day: "Vacant" for day in day_mapping.values()}} for room in room_names}
    
    # Get allocations from database
    query = """
        SELECT wa.team_name, wa.room_name, wa.date, wp.contact_person 
        FROM weekly_allocations wa
        LEFT JOIN weekly_preferences wp ON wa.team_name = wp.team_name
        WHERE wa.room_name != 'Oasis' AND wa.date >= %s AND wa.date <= %s
    """
    start_date = current_week_monday
    end_date = current_week_monday + timedelta(days=3)
    
    allocations = execute_query(query, (start_date, end_date), fetch_all=True)
    
    if allocations:
        for row in allocations:
            team = row["team_name"]
            room = row["room_name"]
            date_val = row["date"]
            contact = row["contact_person"]
            
            day = day_mapping.get(date_val)
            if room in grid and day:
                display_text = f"{team} ({contact})" if contact else team
                grid[room][day] = display_text
    
    # Display as DataFrame
    df = pd.DataFrame(grid.values())
    st.dataframe(df, use_container_width=True, hide_index=True)

def show_oasis_allocations():
    """Display current Oasis allocations."""
    st.subheader("🌴 Oasis Desk Allocations")
    
    current_week_monday = get_current_week()
    
    query = """
        SELECT person_name, date 
        FROM oasis_allocations 
        WHERE date >= %s AND date <= %s
        ORDER BY date, person_name
    """
    start_date = current_week_monday
    end_date = current_week_monday + timedelta(days=4)  # Include Friday
    
    allocations = execute_query(query, (start_date, end_date), fetch_all=True)
    
    if allocations:
        # Group by date
        daily_allocations = {}
        for row in allocations:
            date_val = row["date"]
            person = row["person_name"]
            day_name = date_val.strftime("%A")
            
            if day_name not in daily_allocations:
                daily_allocations[day_name] = []
            daily_allocations[day_name].append(person)
        
        # Display in columns
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        cols = st.columns(5)
        
        for i, day in enumerate(days):
            with cols[i]:
                st.write(f"**{day}**")
                if day in daily_allocations:
                    for person in daily_allocations[day]:
                        st.write(f"• {person}")
                else:
                    st.write("No bookings")
    else:
        st.info("No Oasis bookings for this week.")

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
        
        # Get submission counts
        team_count_query = "SELECT COUNT(*) as count FROM weekly_preferences"
        oasis_count_query = "SELECT COUNT(*) as count FROM oasis_preferences"
        
        team_count = execute_query(team_count_query, fetch_one=True)
        oasis_count = execute_query(oasis_count_query, fetch_one=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Team Preferences", team_count['count'] if team_count else 0)
        with col2:
            st.metric("Oasis Preferences", oasis_count['count'] if oasis_count else 0)
        
        st.divider()
          # Weekly Management
        st.subheader("📅 Weekly Management")
        
        # Allocation Buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎯 Run Project Room Allocation", help="Allocate project rooms only", type="primary"):
                try:
                    allocation_result = run_allocation(DATABASE_URL, only="project", base_monday_date=current_week)
                    if allocation_result:
                        st.success("✅ Project room allocation completed!")
                        st.rerun()
                    else:
                        st.error("❌ Project room allocation failed.")
                except Exception as e:
                    st.error(f"Project allocation error: {e}")
        
        with col2:
            if st.button("🌴 Run Oasis Allocation", help="Allocate Oasis desks only", type="secondary"):
                try:
                    allocation_result = run_allocation(DATABASE_URL, only="oasis", base_monday_date=current_week)
                    if allocation_result:
                        st.success("✅ Oasis allocation completed!")
                        st.rerun()
                    else:
                        st.error("❌ Oasis allocation failed.")
                except Exception as e:
                    st.error(f"Oasis allocation error: {e}")
        
        # Combined allocation for convenience
        if st.button("⚡ Run Both Allocations", help="Run both project and Oasis allocations together"):
            try:
                allocation_result = run_allocation(DATABASE_URL, base_monday_date=current_week)
                if allocation_result:
                    st.success("✅ Both allocations completed successfully!")
                    st.rerun()
                else:
                    st.error("❌ Allocation failed.")
            except Exception as e:
                st.error(f"Allocation error: {e}")
        
        st.divider()
        
        # Quick Actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Streamlined weekly advancement with confirmation in expander
            with st.expander("📈 Prepare Next Week"):
                st.warning("⚠️ This will archive current data and advance to next week")
                if st.button("✅ Confirm: Advance to Next Week", type="primary"):
                    try:
                        new_week = prepare_next_week()
                        st.success(f"✅ Advanced to week of {new_week.strftime('%B %d, %Y')}")
                        st.success("📦 Previous week's data has been archived")
                        st.success("🗑️ Current preferences cleared for new submissions")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error preparing next week: {e}")
        
        with col2:
            # Quick clear with confirmation
            with st.expander("🗑️ Clear Current Data"):
                st.warning("⚠️ This will remove current preferences and allocations")
                if st.button("✅ Confirm: Clear Data", type="primary"):
                    clear_queries = [
                        "DELETE FROM weekly_allocations",
                        "DELETE FROM oasis_allocations", 
                        "DELETE FROM weekly_preferences",
                        "DELETE FROM oasis_preferences"                    ]
                    for query in clear_queries:
                        execute_query(query)
                    st.success("Current data cleared!")
                    st.rerun()
        
        with col3:
            st.write("**Manual Override**")
            new_date = st.date_input("Set Week Monday", value=current_week)
            if st.button("Set Week", help="Manually set the current week"):
                set_current_week(new_date)
                st.success(f"Week set to {new_date.strftime('%B %d, %Y')}")
                st.rerun()
        
        st.divider()
        
        # Archives and Data Management
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 View Archives", help="Show archived data"):
                # Show archived data summary
                archive_query = """
                    SELECT week_monday, COUNT(*) as team_count 
                    FROM weekly_archive 
                    GROUP BY week_monday 
                    ORDER BY week_monday DESC 
                    LIMIT 10
                """
                archives = execute_query(archive_query, fetch_all=True)
                
                if archives:
                    st.write("**Recent Archived Weeks:**")
                    for archive in archives:
                        week = archive['week_monday']
                        count = archive['team_count']
                        st.write(f"• {week.strftime('%B %d, %Y')}: {count} team preferences")
                else:
                    st.info("No archived data found.")
        
        with col2:
            # Quick logout
            if st.button("🚪 Logout"):
                st.session_state.admin_logged_in = False
                st.rerun()

# -----------------------------------------------------
# Main Application
# -----------------------------------------------------
def main():
    # Header
    st.title("🏢 Office Room & Oasis Booking System")
    
    # Show current time and submission status
    now_local = datetime.now(OFFICE_TIMEZONE)
    submissions_allowed, status_message = get_submission_status()
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info(f"⏰ Current Time: **{now_local.strftime('%Y-%m-%d %H:%M:%S')}** ({OFFICE_TIMEZONE_STR})")
    with col2:
        if submissions_allowed:
            st.success(status_message)
        else:
            st.warning(status_message)
    
    # Always show current allocations at the top
    show_current_allocations()
    st.divider()
    show_oasis_allocations()
    st.divider()
    
    # Submission forms
    col1, col2 = st.columns(2)
    
    with col1:
        submit_team_preference()
    
    with col2:
        submit_oasis_preference()
    
    st.divider()
    
    # Admin section
    with st.expander("🔧 Admin Controls", expanded=False):
        admin_controls()

if __name__ == "__main__":
    main()
