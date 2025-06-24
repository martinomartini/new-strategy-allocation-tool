#!/usr/bin/env python3
"""
Database schema update script for advance booking functionality.
"""

from src.database import execute_query

def update_database_schema():
    """Update database tables to support advance booking."""
    
    print("Updating database schema for advance booking...")
    
    # Update weekly_preferences table to include week_monday
    update_weekly_preferences = """
        ALTER TABLE weekly_preferences 
        ADD COLUMN IF NOT EXISTS week_monday DATE;
    """
    
    # Update oasis_preferences table to include week_monday
    update_oasis_preferences = """
        ALTER TABLE oasis_preferences 
        ADD COLUMN IF NOT EXISTS week_monday DATE;
    """
    
    # Update weekly_allocations table to include week_monday (if not exists)
    update_weekly_allocations = """
        ALTER TABLE weekly_allocations 
        ADD COLUMN IF NOT EXISTS week_monday DATE;
    """
    
    # Update oasis_allocations table to include week_monday (if not exists)
    update_oasis_allocations = """
        ALTER TABLE oasis_allocations 
        ADD COLUMN IF NOT EXISTS week_monday DATE;
    """
    
    # Create indexes for better performance
    create_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_weekly_preferences_week ON weekly_preferences(week_monday);",
        "CREATE INDEX IF NOT EXISTS idx_oasis_preferences_week ON oasis_preferences(week_monday);",
        "CREATE INDEX IF NOT EXISTS idx_weekly_allocations_week ON weekly_allocations(week_monday);",
        "CREATE INDEX IF NOT EXISTS idx_oasis_allocations_week ON oasis_allocations(week_monday);"
    ]
    
    # Execute schema updates
    updates = [
        update_weekly_preferences,
        update_oasis_preferences, 
        update_weekly_allocations,
        update_oasis_allocations
    ]
    
    for update in updates:
        result = execute_query(update)
        if result:
            print(f"✓ Schema update successful")
        else:
            print(f"✗ Schema update failed")
    
    # Create indexes
    for index in create_indexes:
        result = execute_query(index)
        if result:
            print(f"✓ Index created successfully")
        else:
            print(f"✗ Index creation failed")
    
    print("\nDatabase schema update completed!")

if __name__ == "__main__":
    update_database_schema()
