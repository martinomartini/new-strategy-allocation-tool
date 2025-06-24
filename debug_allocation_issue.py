#!/usr/bin/env python3
"""
Debug script to investigate the allocation issue where teams submitted for Tue/Thu get allocated to other days.
"""

import psycopg2
import json
import os
from datetime import datetime, timedelta, date
from psycopg2.extras import RealDictCursor

# Database connection
DATABASE_URL = "postgresql://postgres.orrpkvjajaslmsqpaecu:KPMGtrainee123!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

def debug_allocation_issue():
    """Debug the allocation issue by checking all data."""
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=== DEBUGGING ALLOCATION ISSUE ===\n")
        
        # 1. Check current week setting
        print("1. CURRENT WEEK SETTING:")
        cur.execute("SELECT setting_value FROM admin_settings WHERE setting_key = 'current_week_monday'")
        week_result = cur.fetchone()
        if week_result:
            current_week = week_result['setting_value']
            current_week_date = datetime.strptime(current_week, '%Y-%m-%d').date()
            print(f"   Current week Monday: {current_week_date}")
            
            # Calculate actual dates for the week
            tue_date = current_week_date + timedelta(days=1)
            wed_date = current_week_date + timedelta(days=2) 
            thu_date = current_week_date + timedelta(days=3)
            print(f"   Tuesday: {tue_date}")
            print(f"   Wednesday: {wed_date}")
            print(f"   Thursday: {thu_date}")
        else:
            print("   No current week set!")
            current_week_date = None
        
        print()
        
        # 2. Check team preferences 
        print("2. TEAM PREFERENCES:")
        cur.execute("SELECT team_name, contact_person, team_size, preferred_days, submission_time FROM weekly_preferences ORDER BY submission_time DESC")
        preferences = cur.fetchall()
        
        if preferences:
            for pref in preferences:
                print(f"   Team: {pref['team_name']}")
                print(f"   Contact: {pref['contact_person']}")
                print(f"   Size: {pref['team_size']}")
                print(f"   Preferred Days: '{pref['preferred_days']}'")
                print(f"   Submitted: {pref['submission_time']}")
                print()
        else:
            print("   No team preferences found!")
        
        print()
        
        # 3. Check current allocations
        print("3. CURRENT ALLOCATIONS:")
        if current_week_date:
            start_date = current_week_date
            end_date = current_week_date + timedelta(days=6)
            
            cur.execute("""
                SELECT wa.team_name, wa.room_name, wa.date, wp.preferred_days
                FROM weekly_allocations wa
                LEFT JOIN weekly_preferences wp ON wa.team_name = wp.team_name
                WHERE wa.date >= %s AND wa.date <= %s AND wa.room_name != 'Oasis'
                ORDER BY wa.team_name, wa.date
            """, (start_date, end_date))
            
            allocations = cur.fetchall()
            
            if allocations:
                current_team = None
                for alloc in allocations:
                    if alloc['team_name'] != current_team:
                        if current_team:
                            print()
                        print(f"   Team: {alloc['team_name']}")
                        print(f"   Preferred Days: {alloc['preferred_days']}")
                        current_team = alloc['team_name']
                    
                    day_name = alloc['date'].strftime('%A')
                    print(f"   Allocated: {alloc['room_name']} on {day_name} ({alloc['date']})")
            else:
                print("   No allocations found!")
        else:
            print("   Cannot check allocations - no current week set!")
        
        print()
        
        # 4. Check rooms configuration
        print("4. ROOMS CONFIGURATION:")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        rooms_file = os.path.join(base_dir, 'rooms.json')
        
        try:
            with open(rooms_file, 'r') as f:
                rooms_config = json.load(f)
            
            project_rooms = [r for r in rooms_config if r.get("name") != "Oasis" and "capacity" in r and "name" in r]
            print(f"   Total rooms available: {len(project_rooms)}")
            for room in project_rooms:
                print(f"   - {room['name']} (capacity: {room['capacity']})")
        except Exception as e:
            print(f"   Error reading rooms.json: {e}")
        
        print()
        
        # 5. Analyze the specific issue
        print("5. ISSUE ANALYSIS:")
        if preferences and allocations:
            for pref in preferences:
                team_name = pref['team_name']
                preferred_days = pref['preferred_days']
                
                # Find allocations for this team
                team_allocations = [a for a in allocations if a['team_name'] == team_name]
                
                if team_allocations:
                    allocated_days = [a['date'].strftime('%A') for a in team_allocations]
                    print(f"   Team '{team_name}':")
                    print(f"     Preferred: {preferred_days}")
                    print(f"     Allocated: {allocated_days}")
                    
                    # Check if preferences match allocations
                    if preferred_days == "Tuesday,Thursday":
                        if not all(day in ['Tuesday', 'Thursday'] for day in allocated_days):
                            print(f"     ❌ MISMATCH! Team preferred Tue/Thu but got {allocated_days}")
                        else:
                            print(f"     ✅ Correct allocation")
                    elif preferred_days == "Monday,Wednesday":
                        if not all(day in ['Monday', 'Wednesday'] for day in allocated_days):
                            print(f"     ❌ MISMATCH! Team preferred Mon/Wed but got {allocated_days}")
                        else:
                            print(f"     ✅ Correct allocation")
                    print()
        
    except Exception as e:
        print(f"Error during debugging: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    debug_allocation_issue()
