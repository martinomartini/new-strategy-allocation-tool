#!/usr/bin/env python3
"""
Test script to validate the enhanced room allocation system functionality.
This script tests the core functions without running the full Streamlit app.
"""

import os
import sys
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules import correctly."""
    print("🔍 Testing imports...")
    try:
        import app
        import allocate_rooms
        print("✅ All modules import successfully")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_week_management():
    """Test week management functions."""
    print("\n🔍 Testing week management functions...")
    try:
        from app import get_next_monday
        
        # Test get_next_monday with a known date
        test_date = date(2025, 6, 9)  # A Monday
        with patch('app.get_current_week', return_value=test_date):
            next_monday = get_next_monday()
            expected = test_date + timedelta(days=7)
            assert next_monday == expected, f"Expected {expected}, got {next_monday}"
            print(f"✅ get_next_monday works correctly: {test_date} -> {next_monday}")
        
        return True
    except Exception as e:
        print(f"❌ Week management error: {e}")
        return False

def test_submission_time_windows():
    """Test submission time window logic."""
    print("\n🔍 Testing submission time windows...")
    try:
        from app import get_submission_status
        
        # Mock different days and times
        test_cases = [
            (1, 10, True, "Tuesday morning"),  # Tuesday 10:00
            (2, 14, True, "Wednesday afternoon"),  # Wednesday 14:00  
            (3, 15, True, "Thursday before 16:00"),  # Thursday 15:00
            (3, 17, False, "Thursday after 16:00"),  # Thursday 17:00
            (0, 10, False, "Monday"),  # Monday
            (4, 10, False, "Friday"),  # Friday
        ]
        
        for weekday, hour, expected_allowed, description in test_cases:
            mock_datetime = MagicMock()
            mock_datetime.now().weekday.return_value = weekday
            mock_datetime.now().hour = hour
            
            with patch('app.datetime', mock_datetime):
                allowed, message = get_submission_status()
                assert allowed == expected_allowed, f"Failed for {description}: expected {expected_allowed}, got {allowed}"
                print(f"✅ {description}: {'Allowed' if allowed else 'Blocked'} - {message}")
        
        return True
    except Exception as e:
        print(f"❌ Submission time window error: {e}")
        return False

def test_allocation_randomness():
    """Test that allocation functions preserve randomness."""
    print("\n🔍 Testing allocation randomness...")
    try:
        import allocate_rooms
        
        # Check that random.shuffle is used in allocation
        with open('allocate_rooms.py', 'r') as f:
            content = f.read()
            shuffle_count = content.count('random.shuffle')
            print(f"✅ Found {shuffle_count} random.shuffle() calls in allocation logic")
            assert shuffle_count >= 4, f"Expected at least 4 shuffle calls, found {shuffle_count}"
        
        return True
    except Exception as e:
        print(f"❌ Randomness test error: {e}")
        return False

def test_admin_controls_structure():
    """Test that admin controls are properly structured."""
    print("\n🔍 Testing admin controls structure...")
    try:
        with open('app.py', 'r') as f:
            content = f.read()
            
        # Check for separate allocation buttons
        assert 'Run Project Room Allocation' in content, "Missing project allocation button"
        assert 'Run Oasis Allocation' in content, "Missing Oasis allocation button"
        assert 'Run Both Allocations' in content, "Missing combined allocation button"
        print("✅ Separate allocation buttons found")
        
        # Check for streamlined workflow
        assert 'st.expander("📈 Prepare Next Week")' in content, "Missing expandable prepare next week"
        assert 'st.expander("🗑️ Clear Current Data")' in content, "Missing expandable clear data"
        print("✅ Streamlined workflow with expandable sections found")
        
        # Check for allocation parameters
        assert 'only="project"' in content, "Missing project-only allocation parameter"
        assert 'only="oasis"' in content, "Missing oasis-only allocation parameter"
        print("✅ Allocation parameters properly configured")
        
        return True
    except Exception as e:
        print(f"❌ Admin controls structure error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Room Allocation System Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_week_management,
        test_submission_time_windows,
        test_allocation_randomness,
        test_admin_controls_structure,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready for use.")
        return True
    else:
        print("⚠️ Some tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
