#!/usr/bin/env python3
"""
Simple Supabase Connection Test
"""

import psycopg2
import streamlit as st
from datetime import date

# Load configuration
try:
    DATABASE_URL = st.secrets["SUPABASE_DB_URI"]
    print(f"✅ Loaded database URL from secrets")
except Exception as e:
    print(f"❌ Error loading secrets: {e}")
    DATABASE_URL = "postgresql://postgres.orrpkvjajaslmsqpaecu:KPMGtrainee123!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"
    print(f"📝 Using hardcoded database URL")

def test_connection():
    """Test basic database connectivity"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version();")
        result = cursor.fetchone()
        print(f"✅ Database connection successful!")
        print(f"📊 PostgreSQL version: {result[0]}")
        
        # Check if our tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('weekly_preferences', 'oasis_preferences', 'weekly_allocations', 'oasis_allocations', 'admin_settings');
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\n📋 Existing tables: {existing_tables}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def create_schema():
    """Create database schema"""
    schema_sql = """
    -- Weekly desk preferences table
    CREATE TABLE IF NOT EXISTS weekly_preferences (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        week_of DATE NOT NULL,
        preferences TEXT[] NOT NULL,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Oasis desk preferences table  
    CREATE TABLE IF NOT EXISTS oasis_preferences (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        week_of DATE NOT NULL,
        preference VARCHAR(50) NOT NULL,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Weekly allocations table
    CREATE TABLE IF NOT EXISTS weekly_allocations (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        week_of DATE NOT NULL,
        allocated_room VARCHAR(255),
        allocation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Oasis allocations table
    CREATE TABLE IF NOT EXISTS oasis_allocations (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        week_of DATE NOT NULL,
        allocated_desk VARCHAR(255),
        allocation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Admin settings table
    CREATE TABLE IF NOT EXISTS admin_settings (
        id SERIAL PRIMARY KEY,
        setting_name VARCHAR(100) UNIQUE NOT NULL,
        setting_value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Weekly archive table
    CREATE TABLE IF NOT EXISTS weekly_archive (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        week_of DATE NOT NULL,
        preferences TEXT[],
        allocated_room VARCHAR(255),
        archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Oasis archive table
    CREATE TABLE IF NOT EXISTS oasis_archive (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        week_of DATE NOT NULL,
        preference VARCHAR(50),
        allocated_desk VARCHAR(255),
        archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Insert initial admin settings
    INSERT INTO admin_settings (setting_name, setting_value) 
    VALUES ('current_week_monday', '2025-01-06') 
    ON CONFLICT (setting_name) DO NOTHING;

    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_weekly_preferences_week ON weekly_preferences(week_of);
    CREATE INDEX IF NOT EXISTS idx_oasis_preferences_week ON oasis_preferences(week_of);
    CREATE INDEX IF NOT EXISTS idx_weekly_allocations_week ON weekly_allocations(week_of);
    CREATE INDEX IF NOT EXISTS idx_oasis_allocations_week ON oasis_allocations(week_of);
    CREATE INDEX IF NOT EXISTS idx_weekly_archive_week ON weekly_archive(week_of);
    CREATE INDEX IF NOT EXISTS idx_oasis_archive_week ON oasis_archive(week_of);
    """
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("🏗️  Creating database schema...")
        cursor.execute(schema_sql)
        conn.commit()
        
        print("✅ Database schema created successfully!")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('weekly_preferences', 'oasis_preferences', 'weekly_allocations', 'oasis_allocations', 'admin_settings', 'weekly_archive', 'oasis_archive');
        """)
        created_tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Created tables: {created_tables}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating schema: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Supabase setup test...\n")
    
    # Test connection
    if test_connection():
        print("\n🏗️  Creating database schema...")
        if create_schema():
            print("\n✅ Setup complete! Database is ready for the application.")
        else:
            print("\n❌ Schema creation failed!")
    else:
        print("\n❌ Connection test failed!")
