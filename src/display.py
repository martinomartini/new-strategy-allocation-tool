"""
Display functions for the Room Allocation System.
"""
import streamlit as st
import pandas as pd
from datetime import timedelta
from .database import execute_query
from .week_management import get_current_week
from config import PROJECT_ROOMS

def show_current_allocations():
    """Display current room allocations."""
    st.subheader("📅 Current Room Allocations")
    
    current_week_monday = get_current_week()
    
    # Show week info
    week_end = current_week_monday + timedelta(days=6)
    st.info(f"**Week of:** {current_week_monday.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}")
    
    # Create date mapping for the week
    day_mapping = {
        current_week_monday + timedelta(days=i): day 
        for i, day in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday"])
    }
    
    # Initialize grid with project rooms
    room_names = [r["name"] for r in PROJECT_ROOMS]
    grid = {room: {"Room": room, **{day: "Vacant" for day in day_mapping.values()}} for room in room_names}
    
    # Get allocations from database
    query = """
        SELECT wa.team_name, wa.room_name, wa.date, wp.contact_person 
        FROM weekly_allocations wa
        LEFT JOIN weekly_preferences wp ON wa.team_name = wp.team_name
        WHERE wa.room_name != 'Oasis' AND wa.date >= %s AND wa.date <= %s
    """
    start_date = current_week_monday
    end_date = current_week_monday + timedelta(days=3)
    
    allocations = execute_query(query, (start_date, end_date), fetch_all=True)
    
    if allocations:
        for allocation in allocations:
            date = allocation["date"]
            if date in day_mapping:
                day_name = day_mapping[date]
                room_name = allocation["room_name"]
                team_name = allocation["team_name"]
                contact = allocation.get("contact_person", "")
                
                if room_name in grid:
                    display_text = f"{team_name}"
                    if contact:
                        display_text += f"\n({contact})"
                    grid[room_name][day_name] = display_text
    
    # Display as DataFrame
    df = pd.DataFrame(grid.values())
    st.dataframe(df, use_container_width=True, hide_index=True)

def show_oasis_allocations():
    """Display current Oasis allocations."""
    st.subheader("🌴 Oasis Desk Allocations")
    
    current_week_monday = get_current_week()
    
    query = """
        SELECT person_name, date 
        FROM oasis_allocations 
        WHERE date >= %s AND date <= %s
        ORDER BY date, person_name
    """
    start_date = current_week_monday
    end_date = current_week_monday + timedelta(days=4)  # Include Friday
    
    allocations = execute_query(query, (start_date, end_date), fetch_all=True)
    
    if allocations:
        # Group by date
        daily_allocations = {}
        for row in allocations:
            date_val = row["date"]
            person = row["person_name"]
            day_name = date_val.strftime("%A")
            
            if day_name not in daily_allocations:
                daily_allocations[day_name] = []
            daily_allocations[day_name].append(person)
        
        # Display in columns
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        cols = st.columns(5)
        
        for i, day in enumerate(days):
            with cols[i]:
                st.write(f"**{day}**")
                if day in daily_allocations:
                    for person in daily_allocations[day]:
                        st.write(f"• {person}")
                else:
                    st.write("No bookings")
    else:
        st.info("No Oasis bookings for this week.")
