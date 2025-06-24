#!/usr/bin/env python3
"""Database setup and test script."""

from src.database import execute_query, create_archive_tables, create_admin_settings_table

def create_main_tables():
    """Create the main application tables."""
    
    # Create team preferences table
    team_table = """
        CREATE TABLE IF NOT EXISTS team_preferences (
            id SERIAL PRIMARY KEY,
            team_name VARCHAR(255) NOT NULL,
            contact_person VARCHAR(255),
            team_size INT,
            preferred_days VARCHAR(255),
            submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    
    # Create oasis preferences table
    oasis_table = """
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
    """
    
    # Create room allocations table
    room_allocations_table = """
        CREATE TABLE IF NOT EXISTS room_allocations (
            id SERIAL PRIMARY KEY,
            room_name VARCHAR(255) NOT NULL,
            team_name VARCHAR(255) NOT NULL,
            allocation_day VARCHAR(50) NOT NULL,
            week_monday DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    
    # Create oasis allocations table
    oasis_allocations_table = """
        CREATE TABLE IF NOT EXISTS oasis_allocations (
            id SERIAL PRIMARY KEY,
            person_name VARCHAR(255) NOT NULL,
            allocation_day VARCHAR(50) NOT NULL,
            week_monday DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    
    tables = [team_table, oasis_table, room_allocations_table, oasis_allocations_table]
    
    for table_query in tables:
        result = execute_query(table_query)
        if result:
            print(f"✓ Table created/verified successfully")
        else:
            print(f"✗ Failed to create table")

def test_database_connection():
    """Test database connectivity."""
    try:
        result = execute_query("SELECT 1 as test", fetch_one=True)
        if result and result.get('test') == 1:
            print("✓ Database connection successful")
            return True
        else:
            print("✗ Database connection failed")
            return False
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False

if __name__ == "__main__":
    print("Testing database connection...")
    if test_database_connection():
        print("\nCreating database tables...")
        create_main_tables()
        create_admin_settings_table()
        create_archive_tables()
        print("\nDatabase setup completed!")
    else:
        print("\nDatabase setup failed - connection issues")
