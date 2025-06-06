#!/usr/bin/env python3
"""
Debug script to check team preferences vs allocations
"""
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection
DATABASE_URL = "postgresql://postgres.orrpkvjajaslmsqpaecu:KPMGtrainee123!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

def debug_allocation_issue():
    """Check what teams submitted vs what they got allocated."""
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            print("=== TEAM PREFERENCES ===")
            cur.execute("SELECT team_name, preferred_days, submission_time FROM weekly_preferences ORDER BY submission_time")
            preferences = cur.fetchall()
            
            for pref in preferences:
                print(f"Team: {pref['team_name']}")
                print(f"  Preferred: {pref['preferred_days']}")
                print(f"  Submitted: {pref['submission_time']}")
                print()
            
            print("=== TEAM ALLOCATIONS ===")
            cur.execute("""
                SELECT wa.team_name, wa.room_name, wa.date, 
                       TO_CHAR(wa.date, 'Day') as day_name
                FROM weekly_allocations wa 
                WHERE wa.room_name != 'Oasis'
                ORDER BY wa.team_name, wa.date
            """)
            allocations = cur.fetchall()
            
            # Group by team
            team_allocations = {}
            for alloc in allocations:
                team = alloc['team_name']
                if team not in team_allocations:
                    team_allocations[team] = []
                team_allocations[team].append({
                    'date': alloc['date'],
                    'day': alloc['day_name'].strip(),
                    'room': alloc['room_name']
                })
            
            for team, allocs in team_allocations.items():
                print(f"Team: {team}")
                days_allocated = [a['day'] for a in allocs]
                print(f"  Allocated days: {', '.join(days_allocated)}")
                for alloc in allocs:
                    print(f"    {alloc['day']} ({alloc['date']}) - Room: {alloc['room']}")
                print()
            
            print("=== PREFERENCE VS ALLOCATION COMPARISON ===")
            for pref in preferences:
                team_name = pref['team_name']
                preferred_days = pref['preferred_days']
                
                if team_name in team_allocations:
                    allocated_days = [a['day'] for a in team_allocations[team_name]]
                    print(f"Team: {team_name}")
                    print(f"  WANTED: {preferred_days}")
                    print(f"  GOT: {', '.join(allocated_days)}")
                    
                    # Check if allocation matches preference
                    if preferred_days == "Monday,Wednesday":
                        expected = ["Monday", "Wednesday"]
                    elif preferred_days == "Tuesday,Thursday":
                        expected = ["Tuesday", "Thursday"]
                    else:
                        expected = ["Unknown preference format"]
                    
                    matches = set(allocated_days) == set(expected)
                    print(f"  MATCHES: {'✅ YES' if matches else '❌ NO'}")
                    print()
                else:
                    print(f"Team: {team_name} - NO ALLOCATION FOUND")
                    print()
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    debug_allocation_issue()
