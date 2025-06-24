#!/usr/bin/env python3
"""
Debug script to check what's happening with Streamlit secrets
"""

import streamlit as st
import os

print("🔍 Debugging Streamlit secrets loading...")

# Check what Streamlit can see
try:
    st.set_page_config(page_title="Debug", layout="wide")
    
    print("✅ Streamlit imported successfully")
    
    # Check if secrets are loaded
    print(f"📁 Secrets available: {hasattr(st, 'secrets')}")
    
    if hasattr(st, 'secrets'):
        print(f"🔑 All secrets keys: {list(st.secrets.keys())}")
        
        # Check specific key
        if 'SUPABASE_DB_URI' in st.secrets:
            db_uri = st.secrets["SUPABASE_DB_URI"]
            print(f"✅ SUPABASE_DB_URI found: {db_uri[:50]}...")  # First 50 chars only
        else:
            print("❌ SUPABASE_DB_URI not found in secrets")
            
        # Check other keys
        for key in ['ADMIN_PASSWORD', 'OFFICE_TIMEZONE']:
            if key in st.secrets:
                print(f"✅ {key}: {st.secrets[key]}")
            else:
                print(f"❌ {key} not found")
    
    # Check environment variables
    print(f"\n🌍 Environment variables:")
    env_keys = ['SUPABASE_DB_URI', 'ADMIN_PASSWORD', 'OFFICE_TIMEZONE']
    for key in env_keys:
        value = os.environ.get(key)
        if value:
            if 'URI' in key:
                print(f"  {key}: {value[:50]}...")
            else:
                print(f"  {key}: {value}")
        else:
            print(f"  {key}: Not set")
            
except Exception as e:
    print(f"❌ Error: {e}")

print("\n🏁 Debug complete")
