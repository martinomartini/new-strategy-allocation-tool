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
    # Check if admin has forced submissions open
    force_open_query = "SELECT setting_value FROM admin_settings WHERE setting_key = 'force_submissions_open'"
    force_open_result = execute_query(force_open_query, fetch_one=True)
    
    if force_open_result and force_open_result['setting_value'] == 'true':
        return True, "✅ Submissions FORCED OPEN by admin"
    
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

def force_open_submissions(enable=True):
    """Force submissions to be open or closed regardless of time."""
    # Ensure admin_settings table exists
    create_table_query = """
        CREATE TABLE IF NOT EXISTS admin_settings (
            setting_key VARCHAR(255) PRIMARY KEY,
            setting_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    execute_query(create_table_query)
    
    # Set the force submission setting
    query = """
        INSERT INTO admin_settings (setting_key, setting_value, updated_at) 
        VALUES ('force_submissions_open', %s, CURRENT_TIMESTAMP)
        ON CONFLICT (setting_key) 
        DO UPDATE SET setting_value = EXCLUDED.setting_value, updated_at = CURRENT_TIMESTAMP
    """
    execute_query(query, ('true' if enable else 'false',))

def get_weekly_usage_stats():
    """Get comprehensive usage statistics for the current week."""
    current_week = get_current_week()
    
    # Room usage statistics
    room_usage_query = """
        SELECT 
            wa.room_name,
            COUNT(*) as bookings,
            COUNT(DISTINCT wa.team_name) as unique_teams,
            STRING_AGG(DISTINCT wa.team_name, ', ') as teams
        FROM weekly_allocations wa
        WHERE wa.date >= %s AND wa.date <= %s AND wa.room_name != 'Oasis'
        GROUP BY wa.room_name
        ORDER BY bookings DESC
    """
    start_date = current_week
    end_date = current_week + timedelta(days=4)
    
    room_stats = execute_query(room_usage_query, (start_date, end_date), fetch_all=True)
    
    # Oasis usage statistics
    oasis_usage_query = """
        SELECT 
            DATE_PART('dow', oa.date) as day_of_week,
            TO_CHAR(oa.date, 'Day') as day_name,
            COUNT(*) as bookings,
            COUNT(DISTINCT oa.person_name) as unique_people,
            STRING_AGG(oa.person_name, ', ') as people
        FROM oasis_allocations oa
        WHERE oa.date >= %s AND oa.date <= %s
        GROUP BY DATE_PART('dow', oa.date), TO_CHAR(oa.date, 'Day'), oa.date
        ORDER BY oa.date
    """
    
    oasis_stats = execute_query(oasis_usage_query, (start_date, end_date), fetch_all=True)
    
    # Overall capacity utilization
    total_room_capacity = sum(room['capacity'] for room in project_rooms) * 4  # 4 days
    total_oasis_capacity = oasis_config['capacity'] * 5  # 5 days
    
    total_room_bookings = sum(stat['bookings'] for stat in room_stats) if room_stats else 0
    total_oasis_bookings = sum(stat['bookings'] for stat in oasis_stats) if oasis_stats else 0
    
    return {
        'room_stats': room_stats,
        'oasis_stats': oasis_stats,
        'room_utilization': (total_room_bookings / total_room_capacity * 100) if total_room_capacity > 0 else 0,
        'oasis_utilization': (total_oasis_bookings / total_oasis_capacity * 100) if total_oasis_capacity > 0 else 0,
        'total_room_bookings': total_room_bookings,
        'total_oasis_bookings': total_oasis_bookings
    }

def get_all_time_usage_stats():
    """Get comprehensive usage statistics across all time periods."""
    # Room usage statistics - all time
    room_usage_query = """
        SELECT 
            wa.room_name,
            COUNT(*) as total_bookings,
            COUNT(DISTINCT wa.team_name) as unique_teams,
            COUNT(DISTINCT DATE_TRUNC('week', wa.date)) as weeks_used,
            MIN(wa.date) as first_booking,
            MAX(wa.date) as last_booking
        FROM weekly_allocations wa
        WHERE wa.room_name != 'Oasis'
        GROUP BY wa.room_name
        ORDER BY total_bookings DESC
    """
    
    room_stats = execute_query(room_usage_query, fetch_all=True)
    
    # Oasis usage statistics - all time
    oasis_usage_query = """
        SELECT 
            COUNT(*) as total_bookings,
            COUNT(DISTINCT oa.person_name) as unique_people,
            COUNT(DISTINCT DATE_TRUNC('week', oa.date)) as weeks_used,
            MIN(oa.date) as first_booking,
            MAX(oa.date) as last_booking,
            COUNT(DISTINCT CASE WHEN DATE_PART('dow', oa.date) = 1 THEN oa.date END) as monday_bookings,
            COUNT(DISTINCT CASE WHEN DATE_PART('dow', oa.date) = 2 THEN oa.date END) as tuesday_bookings,
            COUNT(DISTINCT CASE WHEN DATE_PART('dow', oa.date) = 3 THEN oa.date END) as wednesday_bookings,
            COUNT(DISTINCT CASE WHEN DATE_PART('dow', oa.date) = 4 THEN oa.date END) as thursday_bookings,
            COUNT(DISTINCT CASE WHEN DATE_PART('dow', oa.date) = 5 THEN oa.date END) as friday_bookings
        FROM oasis_allocations oa
    """
    
    oasis_stats = execute_query(oasis_usage_query, fetch_one=True)
    
    # Weekly trends
    weekly_trends_query = """
        SELECT 
            DATE_TRUNC('week', combined.date) as week_start,
            SUM(CASE WHEN combined.type = 'room' THEN 1 ELSE 0 END) as room_bookings,
            SUM(CASE WHEN combined.type = 'oasis' THEN 1 ELSE 0 END) as oasis_bookings
        FROM (
            SELECT date, 'room' as type FROM weekly_allocations WHERE room_name != 'Oasis'
            UNION ALL
            SELECT date, 'oasis' as type FROM oasis_allocations
        ) combined
        GROUP BY DATE_TRUNC('week', combined.date)
        ORDER BY week_start DESC
        LIMIT 10
    """
    
    weekly_trends = execute_query(weekly_trends_query, fetch_all=True)
    
    return {
        'room_stats': room_stats,
        'oasis_stats': oasis_stats,
        'weekly_trends': weekly_trends
    }

def get_user_analytics():
    """Get individual user analytics across all weeks."""
    # Team/Contact person analytics for room bookings
    team_analytics_query = """
        SELECT 
            wp.contact_person,
            wp.team_name,
            COUNT(DISTINCT wa.date) as total_room_days,
            COUNT(DISTINCT DATE_TRUNC('week', wa.date)) as total_weeks_with_rooms,
            STRING_AGG(DISTINCT wa.room_name, ', ') as rooms_used,
            MIN(wa.date) as first_booking,
            MAX(wa.date) as last_booking
        FROM weekly_preferences wp
        LEFT JOIN weekly_allocations wa ON wp.team_name = wa.team_name
        WHERE wa.room_name != 'Oasis' OR wa.room_name IS NULL
        GROUP BY wp.contact_person, wp.team_name
        ORDER BY total_room_days DESC NULLS LAST
    """
    
    team_analytics = execute_query(team_analytics_query, fetch_all=True)
    
    # Individual Oasis analytics
    oasis_analytics_query = """
        SELECT 
            op.person_name,
            COUNT(DISTINCT oa.date) as total_oasis_days,
            COUNT(DISTINCT DATE_TRUNC('week', oa.date)) as total_weeks_with_oasis,
            MIN(oa.date) as first_oasis_booking,
            MAX(oa.date) as last_oasis_booking,
            COUNT(DISTINCT CASE WHEN DATE_PART('dow', oa.date) = 1 THEN oa.date END) as monday_bookings,
            COUNT(DISTINCT CASE WHEN DATE_PART('dow', oa.date) = 2 THEN oa.date END) as tuesday_bookings,
            COUNT(DISTINCT CASE WHEN DATE_PART('dow', oa.date) = 3 THEN oa.date END) as wednesday_bookings,
            COUNT(DISTINCT CASE WHEN DATE_PART('dow', oa.date) = 4 THEN oa.date END) as thursday_bookings,
            COUNT(DISTINCT CASE WHEN DATE_PART('dow', oa.date) = 5 THEN oa.date END) as friday_bookings
        FROM oasis_preferences op
        LEFT JOIN oasis_allocations oa ON op.person_name = oa.person_name
        GROUP BY op.person_name
        ORDER BY total_oasis_days DESC NULLS LAST
    """
    
    oasis_analytics = execute_query(oasis_analytics_query, fetch_all=True)
    
    # Combined analytics - people who use both services
    combined_analytics_query = """
        SELECT 
            COALESCE(team_data.contact_person, oasis_data.person_name) as person_name,
            COALESCE(team_data.total_room_days, 0) as room_days,
            COALESCE(oasis_data.total_oasis_days, 0) as oasis_days,
            COALESCE(team_data.total_weeks_with_rooms, 0) as room_weeks,
            COALESCE(oasis_data.total_weeks_with_oasis, 0) as oasis_weeks,
            CASE 
                WHEN team_data.contact_person IS NOT NULL AND oasis_data.person_name IS NOT NULL THEN 'Both'
                WHEN team_data.contact_person IS NOT NULL THEN 'Rooms Only'
                ELSE 'Oasis Only'
            END as usage_type
        FROM (
            SELECT 
                wp.contact_person,
                COUNT(DISTINCT wa.date) as total_room_days,
                COUNT(DISTINCT DATE_TRUNC('week', wa.date)) as total_weeks_with_rooms
            FROM weekly_preferences wp
            LEFT JOIN weekly_allocations wa ON wp.team_name = wa.team_name
            WHERE wa.room_name != 'Oasis' OR wa.room_name IS NULL
            GROUP BY wp.contact_person
        ) team_data
        FULL OUTER JOIN (
            SELECT 
                op.person_name,
                COUNT(DISTINCT oa.date) as total_oasis_days,
                COUNT(DISTINCT DATE_TRUNC('week', oa.date)) as total_weeks_with_oasis
            FROM oasis_preferences op
            LEFT JOIN oasis_allocations oa ON op.person_name = oa.person_name
            GROUP BY op.person_name
        ) oasis_data ON team_data.contact_person = oasis_data.person_name
        ORDER BY (COALESCE(team_data.total_room_days, 0) + COALESCE(oasis_data.total_oasis_days, 0)) DESC
    """
    
    combined_analytics = execute_query(combined_analytics_query, fetch_all=True)
      return {
        'team_analytics': team_analytics,
        'oasis_analytics': oasis_analytics,
        'combined_analytics': combined_analytics
    }

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
        
        # Submission Control
        st.subheader("🔓 Submission Control")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔓 Force Open Submissions", help="Allow submissions regardless of time restrictions", type="secondary"):
                force_open_submissions(True)
                st.success("✅ Submissions are now FORCED OPEN!")
                st.rerun()
        
        with col2:
            if st.button("🔒 Restore Normal Schedule", help="Return to normal time-based submission rules"):
                force_open_submissions(False)
                st.success("✅ Submissions returned to normal schedule!")
                st.rerun()
        
        st.divider()
        
        # Usage Analytics
        st.subheader("📊 Usage Analytics")
        
        if st.button("📈 Show Weekly Usage Stats", help="Current week room and Oasis utilization"):
            usage_stats = get_weekly_usage_stats()
            
            # Overall utilization metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Room Utilization", f"{usage_stats['room_utilization']:.1f}%")
            with col2:
                st.metric("Oasis Utilization", f"{usage_stats['oasis_utilization']:.1f}%")
            with col3:
                st.metric("Total Room Bookings", usage_stats['total_room_bookings'])
            with col4:
                st.metric("Total Oasis Bookings", usage_stats['total_oasis_bookings'])
            
            # Room usage breakdown
            if usage_stats['room_stats']:
                st.write("**📅 Room Usage This Week:**")
                room_df = pd.DataFrame(usage_stats['room_stats'])
                st.dataframe(room_df, use_container_width=True)
            
            # Oasis usage breakdown
            if usage_stats['oasis_stats']:
                st.write("**🌴 Oasis Usage This Week:**")
                oasis_df = pd.DataFrame(usage_stats['oasis_stats'])
                # Clean up the day name
                oasis_df['day_name'] = oasis_df['day_name'].str.strip()
                st.dataframe(oasis_df[['day_name', 'bookings', 'unique_people', 'people']], use_container_width=True)
        
        if st.button("👥 Show User Analytics", help="Individual usage patterns across all weeks"):
            analytics = get_user_analytics()
            
            # Combined usage overview
            st.write("**📊 Overall User Patterns:**")
            if analytics['combined_analytics']:
                combined_df = pd.DataFrame(analytics['combined_analytics'])
                st.dataframe(combined_df, use_container_width=True)
            
            # Detailed breakdowns in tabs
            tab1, tab2, tab3 = st.tabs(["🏢 Team Analytics", "🌴 Oasis Analytics", "📈 Usage Trends"])
            
            with tab1:
                if analytics['team_analytics']:
                    team_df = pd.DataFrame(analytics['team_analytics'])
                    st.dataframe(team_df, use_container_width=True)
                else:
                    st.info("No team booking data available.")
            
            with tab2:
                if analytics['oasis_analytics']:
                    oasis_df = pd.DataFrame(analytics['oasis_analytics'])
                    st.dataframe(oasis_df, use_container_width=True)
                    
                    # Day preference chart
                    if len(oasis_df) > 0:
                        st.write("**Day Preference Summary:**")
                        day_totals = {
                            'Monday': oasis_df['monday_bookings'].sum(),
                            'Tuesday': oasis_df['tuesday_bookings'].sum(),
                            'Wednesday': oasis_df['wednesday_bookings'].sum(),
                            'Thursday': oasis_df['thursday_bookings'].sum(),
                            'Friday': oasis_df['friday_bookings'].sum()
                        }
                        st.bar_chart(day_totals)
                else:
                    st.info("No Oasis booking data available.")
            
            with tab3:
                if analytics['combined_analytics']:
                    combined_df = pd.DataFrame(analytics['combined_analytics'])
                    usage_type_counts = combined_df['usage_type'].value_counts()
                    st.write("**Service Usage Distribution:**")
                    st.bar_chart(usage_type_counts)
                    
                    # Top users
                    combined_df['total_days'] = combined_df['room_days'] + combined_df['oasis_days']
                    top_users = combined_df.nlargest(10, 'total_days')[['person_name', 'total_days', 'usage_type']]
                    st.write("**Top 10 Most Active Users:**")
                    st.dataframe(top_users, use_container_width=True)
        
        st.divider()
        
        # Quick Actions - Using expandable sections without nesting in columns
        
        # Streamlined weekly advancement with confirmation in expander
        with st.expander("📈 Prepare Next Week"):
            st.warning("⚠️ This will archive current data and advance to next week")
            if st.button("✅ Confirm: Advance to Next Week", type="primary", key="advance_week"):
                try:
                    new_week = prepare_next_week()
                    st.success(f"✅ Advanced to week of {new_week.strftime('%B %d, %Y')}")
                    st.success("📦 Previous week's data has been archived")
                    st.success("🗑️ Current preferences cleared for new submissions")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error preparing next week: {e}")
        
        # Quick clear with confirmation
        with st.expander("🗑️ Clear Current Data"):
            st.warning("⚠️ This will remove current preferences and allocations")
            if st.button("✅ Confirm: Clear Data", type="primary"):
                clear_queries = [
                    "DELETE FROM weekly_allocations",
                    "DELETE FROM oasis_allocations", 
                    "DELETE FROM weekly_preferences",
                    "DELETE FROM oasis_preferences"
                ]
                for query in clear_queries:
                    execute_query(query)
                st.success("Current data cleared!")
                st.rerun()
        
        # Manual Override section
        st.subheader("⚙️ Manual Override")
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
    admin_controls()

if __name__ == "__main__":
    main()
