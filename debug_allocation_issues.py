#!/usr/bin/env python3
"""
Debug script to investigate allocation issues
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date, timedelta

# Database connection
DATABASE_URL = "postgresql://postgres.orrpkvjajaslmsqpaecu:KPMGtrainee123!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

def get_db_connection():
    """Get database connection"""
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def execute_query(query, params=None):
    """Execute query and return results"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()
    except Exception as e:
        print(f"Query error: {e}")
        return None
    finally:
        conn.close()

def check_current_week():
    """Check what the current week is set to"""
    print("=== CURRENT WEEK SETTING ===")
    query = "SELECT setting_value FROM admin_settings WHERE setting_key = 'current_week_monday'"
    result = execute_query(query)
    
    if result:
        current_week = result[0]['setting_value']
        print(f"Current week Monday: {current_week}")
        return datetime.strptime(current_week, '%Y-%m-%d').date()
    else:
        print("No current week set in database")
        return None

def check_team_preferences():
    """Check team preferences submitted"""
    print("\n=== TEAM PREFERENCES ===")
    query = """
        SELECT team_name, contact_person, team_size, preferred_days, submission_time 
        FROM weekly_preferences 
        ORDER BY submission_time DESC
    """
    preferences = execute_query(query)
    
    if preferences:
        for pref in preferences:
            print(f"Team: {pref['team_name']} | Contact: {pref['contact_person']} | Days: {pref['preferred_days']} | Submitted: {pref['submission_time']}")
    else:
        print("No team preferences found")
    
    return preferences

def check_oasis_preferences():
    """Check Oasis preferences submitted"""
    print("\n=== OASIS PREFERENCES ===")
    query = """
        SELECT person_name, preferred_day_1, preferred_day_2, preferred_day_3, 
               preferred_day_4, preferred_day_5, submission_time 
        FROM oasis_preferences 
        ORDER BY submission_time DESC
    """
    preferences = execute_query(query)
    
    if preferences:
        for pref in preferences:
            days = [pref[f'preferred_day_{i}'] for i in range(1, 6) if pref[f'preferred_day_{i}']]
            print(f"Person: {pref['person_name']} | Days: {', '.join(days)} | Submitted: {pref['submission_time']}")
    else:
        print("No Oasis preferences found")
    
    return preferences

def check_room_allocations():
    """Check current room allocations"""
    print("\n=== ROOM ALLOCATIONS ===")
    current_week = check_current_week()
    
    if not current_week:
        print("Cannot check allocations - no current week set")
        return
    
    start_date = current_week
    end_date = current_week + timedelta(days=3)
    
    query = """
        SELECT wa.team_name, wa.room_name, wa.date, wp.preferred_days 
        FROM weekly_allocations wa
        LEFT JOIN weekly_preferences wp ON wa.team_name = wp.team_name
        WHERE wa.date >= %s AND wa.date <= %s AND wa.room_name != 'Oasis'
        ORDER BY wa.date, wa.room_name
    """
    allocations = execute_query(query, (start_date, end_date))
    
    if allocations:
        for alloc in allocations:
            day_name = alloc['date'].strftime('%A')
            print(f"Team: {alloc['team_name']} | Room: {alloc['room_name']} | Date: {alloc['date']} ({day_name}) | Preferred: {alloc['preferred_days']}")
            
            # Check if allocation matches preference
            preferred_days = alloc['preferred_days']
            if preferred_days:
                if day_name in preferred_days:
                    print(f"  ✅ CORRECT: {day_name} is in preferred days ({preferred_days})")
                else:
                    print(f"  ❌ WRONG: {day_name} is NOT in preferred days ({preferred_days})")
    else:
        print("No room allocations found")

def check_oasis_allocations():
    """Check current Oasis allocations"""
    print("\n=== OASIS ALLOCATIONS ===")
    current_week = check_current_week()
    
    if not current_week:
        print("Cannot check allocations - no current week set")
        return
    
    start_date = current_week
    end_date = current_week + timedelta(days=4)  # Include Friday
    
    query = """
        SELECT oa.person_name, oa.date, 
               op.preferred_day_1, op.preferred_day_2, op.preferred_day_3, op.preferred_day_4, op.preferred_day_5
        FROM oasis_allocations oa
        LEFT JOIN oasis_preferences op ON oa.person_name = op.person_name
        WHERE oa.date >= %s AND oa.date <= %s
        ORDER BY oa.date, oa.person_name
    """
    allocations = execute_query(query, (start_date, end_date))
    
    if allocations:
        for alloc in allocations:
            day_name = alloc['date'].strftime('%A')
            preferred_days = [alloc[f'preferred_day_{i}'] for i in range(1, 6) if alloc[f'preferred_day_{i}']]
            print(f"Person: {alloc['person_name']} | Date: {alloc['date']} ({day_name}) | Preferred: {', '.join(preferred_days)}")
            
            # Check if allocation matches preference
            if day_name in preferred_days:
                print(f"  ✅ CORRECT: {day_name} is in preferred days")
            else:
                print(f"  ❌ WRONG: {day_name} is NOT in preferred days")
    else:
        print("No Oasis allocations found")

def check_tables_exist():
    """Check if all required tables exist"""
    print("\n=== TABLE EXISTENCE CHECK ===")
    tables = ['weekly_preferences', 'oasis_preferences', 'weekly_allocations', 'oasis_allocations', 'admin_settings']
    
    for table in tables:
        query = f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"
        result = execute_query(query)
        exists = result[0]['exists'] if result else False
        status = "✅ EXISTS" if exists else "❌ MISSING"
        print(f"{table}: {status}")

if __name__ == "__main__":
    print("🔍 DEBUGGING ALLOCATION ISSUES")
    print("=" * 50)
    
    # Check table existence
    check_tables_exist()
    
    # Check current week setting
    current_week = check_current_week()
    
    # Check what preferences were submitted
    team_prefs = check_team_preferences()
    oasis_prefs = check_oasis_preferences()
    
    # Check what allocations were made
    check_room_allocations()
    check_oasis_allocations()
    
    print("\n" + "=" * 50)
    print("🔍 DEBUG COMPLETE")
