#!/usr/bin/env python3
"""Test script to check imports."""

try:
    import streamlit as st
    print("✓ Streamlit imported successfully")
except ImportError as e:
    print(f"✗ Streamlit import failed: {e}")

try:
    import psycopg2
    print("✓ psycopg2 imported successfully")
except ImportError as e:
    print(f"✗ psycopg2 import failed: {e}")

try:
    import pandas as pd
    print("✓ pandas imported successfully")
except ImportError as e:
    print(f"✗ pandas import failed: {e}")

try:
    import pytz
    print("✓ pytz imported successfully")
except ImportError as e:
    print(f"✗ pytz import failed: {e}")

# Test local imports
try:
    import config
    print("✓ config imported successfully")
except ImportError as e:
    print(f"✗ config import failed: {e}")

try:
    from src.week_management import get_current_week
    print("✓ week_management imported successfully")
except ImportError as e:
    print(f"✗ week_management import failed: {e}")

try:
    from src.display import show_current_allocations, show_oasis_allocations
    print("✓ display imported successfully")
except ImportError as e:
    print(f"✗ display import failed: {e}")

try:
    from src.forms import submit_team_preference, submit_oasis_preference
    print("✓ forms imported successfully")
except ImportError as e:
    print(f"✗ forms import failed: {e}")

try:
    from src.admin import admin_controls
    print("✓ admin imported successfully")
except ImportError as e:
    print(f"✗ admin import failed: {e}")

try:
    from src.allocate_rooms import run_allocation
    print("✓ allocate_rooms imported successfully")
except ImportError as e:
    print(f"✗ allocate_rooms import failed: {e}")

print("\nImport test completed!")
