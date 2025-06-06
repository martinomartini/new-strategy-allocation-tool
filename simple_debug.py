#!/usr/bin/env python3
"""
Simple debug script to check database contents
"""
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection
DATABASE_URL = "postgresql://postgres.orrpkvjajaslmsqpaecu:KPMGtrainee123!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

def check_data():
    """Check what's in the database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check preferences
            cur.execute("SELECT COUNT(*) as count FROM weekly_preferences")
            pref_count = cur.fetchone()['count']
            print(f"Weekly preferences count: {pref_count}")
            
            if pref_count > 0:
                cur.execute("SELECT * FROM weekly_preferences LIMIT 3")
                prefs = cur.fetchall()
                print("Sample preferences:")
                for p in prefs:
                    print(f"  {p}")
                print()
            
            # Check allocations  
            cur.execute("SELECT COUNT(*) as count FROM weekly_allocations WHERE room_name != 'Oasis'")
            alloc_count = cur.fetchone()['count']
            print(f"Room allocations count: {alloc_count}")
            
            if alloc_count > 0:
                cur.execute("SELECT * FROM weekly_allocations WHERE room_name != 'Oasis' LIMIT 3")
                allocs = cur.fetchall()
                print("Sample allocations:")
                for a in allocs:
                    print(f"  {a}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_data()
