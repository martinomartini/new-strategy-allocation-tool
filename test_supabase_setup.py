#!/usr/bin/env python3
"""
Test script to verify Supabase connection and create database schema
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# Your Supabase connection string
DATABASE_URL = "postgresql://postgres.orrpkvjajaslmsqpaecu:KPMGtrainee123!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

def test_connection():
    """Test basic database connection"""
    try:
        print("🔗 Testing Supabase connection...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Test connection
        cur.execute("SELECT 1")
        result = cur.fetchone()
        print("✅ Connection successful!", result)
        
        # Test tables exist
        cur.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cur.fetchall()
        existing_tables = [t[0] for t in tables]
        print(f"📋 Existing tables ({len(existing_tables)}): {existing_tables}")
        
        cur.close()
        conn.close()
        return True, existing_tables
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False, []

def create_schema():
    """Create all required database tables"""
    
    schema_queries = [
        """
        CREATE TABLE IF NOT EXISTS weekly_preferences (
            id SERIAL PRIMARY KEY,
            team_name VARCHAR(255) NOT NULL,
            contact_person VARCHAR(255),
            team_size INT NOT NULL,
            preferred_days VARCHAR(255) NOT NULL,
            submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS oasis_preferences (
            id SERIAL PRIMARY KEY,
            person_name VARCHAR(255) NOT NULL,
            preferred_day_1 VARCHAR(50),
            preferred_day_2 VARCHAR(50),
            preferred_day_3 VARCHAR(50),
            preferred_day_4 VARCHAR(50),
            preferred_day_5 VARCHAR(50),
            submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS weekly_allocations (
            id SERIAL PRIMARY KEY,
            team_name VARCHAR(255) NOT NULL,
            room_name VARCHAR(255) NOT NULL,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS oasis_allocations (
            id SERIAL PRIMARY KEY,
            person_name VARCHAR(255) NOT NULL,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS admin_settings (
            setting_key VARCHAR(255) PRIMARY KEY,
            setting_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
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
    
    try:
        print("\n🏗️ Creating database schema...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        for i, query in enumerate(schema_queries, 1):
            cur.execute(query)
            table_name = query.split("CREATE TABLE IF NOT EXISTS ")[1].split(" (")[0]
            print(f"  ✅ Table {i}/7: {table_name}")
        
        # Set initial week if not exists
        cur.execute("""
            INSERT INTO admin_settings (setting_key, setting_value) 
            VALUES ('current_week_monday', '2025-06-09')
            ON CONFLICT (setting_key) DO NOTHING
        """)
        print("  ✅ Initial week setting added")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("🎉 Database schema created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Schema creation failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def test_app_functionality():
    """Test basic app functionality"""
    try:
        print("\n🧪 Testing app functionality...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Test getting current week
        cur.execute("SELECT setting_value FROM admin_settings WHERE setting_key = 'current_week_monday'")
        result = cur.fetchone()
        if result:
            print(f"  ✅ Current week setting: {result['setting_value']}")
        else:
            print("  ⚠️ No current week setting found")
        
        # Test table row counts
        tables = ['weekly_preferences', 'oasis_preferences', 'weekly_allocations', 'oasis_allocations']
        for table in tables:
            cur.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cur.fetchone()['count']
            print(f"  📊 {table}: {count} records")
        
        cur.close()
        conn.close()
        print("✅ App functionality test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Supabase Setup & Test Script")
    print("=" * 50)
    
    # Test connection
    success, tables = test_connection()
    if not success:
        print("❌ Cannot proceed - fix connection issues first!")
        exit(1)
    
    # Create schema if needed
    required_tables = {
        'weekly_preferences', 'oasis_preferences', 'weekly_allocations', 
        'oasis_allocations', 'admin_settings', 'weekly_archive', 'oasis_archive'
    }
    
    missing_tables = required_tables - set(tables)
    if missing_tables:
        print(f"\n⚠️ Missing tables: {missing_tables}")
        create_schema()
    else:
        print("\n✅ All required tables already exist!")
    
    # Test functionality
    test_app_functionality()
    
    print("\n🎯 Next Steps:")
    print("1. Run: streamlit run app.py")
    print("2. Test the admin controls")
    print("3. Submit some test preferences")
    print("4. Run the allocation buttons")
    print("\n🎉 Setup complete!")
