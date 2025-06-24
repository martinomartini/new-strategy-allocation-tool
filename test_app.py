#!/usr/bin/env python3
"""Test script to verify app can run."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

try:
    print("Testing basic app functionality...")
    
    # Test config import
    from config import PROJECT_ROOMS, OASIS_CONFIG, DATABASE_URL
    print(f"✓ Config imported successfully")
    print(f"  - PROJECT_ROOMS: {len(PROJECT_ROOMS)} rooms")
    print(f"  - OASIS_CONFIG: {OASIS_CONFIG}")
    print(f"  - DATABASE_URL: {'✓ Set' if DATABASE_URL else '✗ Not set'}")
    
    # Test all module imports
    from src.week_management import get_current_week
    from src.display import show_current_allocations, show_oasis_allocations
    from src.forms import submit_team_preference, submit_oasis_preference
    from src.admin import admin_controls
    from src.allocate_rooms import run_allocation
    print("✓ All modules imported successfully")
    
    # Test basic functionality
    current_week = get_current_week()
    print(f"✓ Current week: {current_week}")
    
    print("\n🎉 App is ready to run!")
    print("To start the app, run: streamlit run app.py")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
