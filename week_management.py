"""
Week management functions for the Room Allocation System.
"""
from datetime import datetime, timedelta, date
from database import execute_query, create_archive_tables, create_admin_settings_table
from config import OFFICE_TIMEZONE

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

def set_current_week(week_monday):
    """Set the current active week in database."""
    # Ensure admin_settings table exists
    create_admin_settings_table()
    
    # Set the current week
    query = """
        INSERT INTO admin_settings (setting_key, setting_value, updated_at) 
        VALUES ('current_week_monday', %s, CURRENT_TIMESTAMP)
        ON CONFLICT (setting_key) 
        DO UPDATE SET setting_value = EXCLUDED.setting_value, updated_at = CURRENT_TIMESTAMP
    """
    execute_query(query, (week_monday.isoformat(),))

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
    create_admin_settings_table()
    
    # Set the force submission setting
    query = """
        INSERT INTO admin_settings (setting_key, setting_value, updated_at) 
        VALUES ('force_submissions_open', %s, CURRENT_TIMESTAMP)
        ON CONFLICT (setting_key) 
        DO UPDATE SET setting_value = EXCLUDED.setting_value, updated_at = CURRENT_TIMESTAMP
    """
    execute_query(query, ('true' if enable else 'false',))
