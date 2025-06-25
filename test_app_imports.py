#!/usr/bin/env python3
"""Test imports for app_clean.py to identify issues."""

print("Testing imports for app_clean.py...")

try:
    import streamlit as st
    print("✓ streamlit imported")
except Exception as e:
    print(f"✗ streamlit failed: {e}")

try:
    from datetime import timedelta, date
    print("✓ datetime imported")
except Exception as e:
    print(f"✗ datetime failed: {e}")

try:
    from config import PROJECT_ROOMS, OASIS_CONFIG
    print("✓ config imported")
    print(f"  PROJECT_ROOMS: {len(PROJECT_ROOMS) if PROJECT_ROOMS else 0} rooms")
    print(f"  OASIS_CONFIG: {OASIS_CONFIG}")
except Exception as e:
    print(f"✗ config failed: {e}")

try:
    from week_management import get_current_week, get_next_week
    print("✓ week_management imported")
except Exception as e:
    print(f"✗ week_management failed: {e}")

try:
    from display import show_current_allocations, show_oasis_allocations, show_week_allocations
    print("✓ display imported")
except Exception as e:
    print(f"✗ display failed: {e}")

try:
    from forms import submit_team_preference, submit_oasis_preference, submit_advance_team_preference, submit_advance_oasis_preference
    print("✓ forms imported")
except Exception as e:
    print(f"✗ forms failed: {e}")

try:
    from admin import admin_controls
    print("✓ admin imported")
except Exception as e:
    print(f"✗ admin failed: {e}")

try:
    from allocate_rooms import run_allocation
    print("✓ allocate_rooms imported")
except Exception as e:
    print(f"✗ allocate_rooms failed: {e}")

print("\nAll imports completed!")
