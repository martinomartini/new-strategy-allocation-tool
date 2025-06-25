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

def show_week_allocations(target_week, is_next_week=False):
    """Display allocations for a specific week."""
    week_label = "Next Week" if is_next_week else "Current Week" 
    st.subheader(f"📅 {week_label} Room Allocations")
    
    # Room allocations
    show_room_allocations_for_week(target_week)
    
    st.divider()
    
    # Oasis allocations
    show_oasis_allocations_for_week(target_week)

def show_room_allocations_for_week(target_week):
    """Display room allocations for a specific week."""
    # Create date mapping for the week
    day_mapping = {
        target_week + timedelta(days=i): day 
        for i, day in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday"])
    }
    
    # Initialize grid with project rooms
    room_names = [r["name"] for r in PROJECT_ROOMS]
    grid = {room: {"Room": room, **{day: "🟦 Available" for day in day_mapping.values()}} for room in room_names}
    
    # Get allocations from database
    query = """
        SELECT wa.team_name, wa.room_name, wa.date, wp.contact_person 
        FROM weekly_allocations wa
        LEFT JOIN weekly_preferences wp ON wa.team_name = wp.team_name AND wp.week_monday = wa.week_monday
        WHERE wa.room_name != 'Oasis' AND wa.date >= %s AND wa.date <= %s AND wa.week_monday = %s
    """
    start_date = target_week
    end_date = target_week + timedelta(days=3)
    
    allocations = execute_query(query, (start_date, end_date, target_week), fetch_all=True)
    
    if allocations:
        for allocation in allocations:
            date = allocation["date"]
            if date in day_mapping:
                day_name = day_mapping[date]
                room_name = allocation["room_name"]
                team_name = allocation["team_name"]
                contact = allocation.get("contact_person", "")
                
                if room_name in grid:
                    display_text = f"🏢 {team_name}"
                    if contact:
                        display_text += f"\n👤 {contact}"
                    grid[room_name][day_name] = display_text
    
    # Display grid with enhanced styling
    if grid:
        df = pd.DataFrame(list(grid.values()))
        
        # Style the dataframe for better presentation
        st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Room": st.column_config.TextColumn("Room", help="Meeting room name"),
                "Monday": st.column_config.TextColumn("Monday", help="Monday allocation"),
                "Tuesday": st.column_config.TextColumn("Tuesday", help="Tuesday allocation"),
                "Wednesday": st.column_config.TextColumn("Wednesday", help="Wednesday allocation"),
                "Thursday": st.column_config.TextColumn("Thursday", help="Thursday allocation"),
            }
        )
        
        # Add legend
        st.markdown("""
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-top: 1rem;">
            <strong>Legend:</strong> 
            🟦 Available | 🏢 Team Allocated | 👤 Contact Person
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("📭 No room allocations found for this week.")

def show_oasis_allocations_for_week(target_week):
    """Display Oasis allocations for a specific week."""
    st.markdown("#### 🌴 Oasis Desk Allocations")
    
    # Get Oasis allocations
    query = """
        SELECT person_name, date 
        FROM weekly_allocations 
        WHERE room_name = 'Oasis' AND date >= %s AND date <= %s AND week_monday = %s
        ORDER BY date, person_name
    """
    start_date = target_week
    end_date = target_week + timedelta(days=4)  # Include Friday
    
    oasis_allocations = execute_query(query, (start_date, end_date, target_week), fetch_all=True)
    
    if oasis_allocations:
        # Group by day
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        day_mapping = {target_week + timedelta(days=i): day for i, day in enumerate(days)}
        
        allocations_by_day = {day: [] for day in days}
        
        for allocation in oasis_allocations:
            date = allocation["date"]
            if date in day_mapping:
                day_name = day_mapping[date]
                allocations_by_day[day_name].append(allocation["person_name"])
        
        # Display in an enhanced format
        cols = st.columns(5)
        day_emojis = ["📅", "📅", "📅", "📅", "📅"]
        
        for i, (day, emoji) in enumerate(zip(days, day_emojis)):
            with cols[i]:
                st.markdown(f"**{emoji} {day}**")
                
                if allocations_by_day[day]:
                    # Create a nice card for each person
                    for j, person in enumerate(allocations_by_day[day]):
                        st.markdown(f"""
                        <div style="background: #e8f5e8; padding: 0.5rem; margin: 0.25rem 0; border-radius: 6px; border-left: 3px solid #4caf50;">
                            👤 {person}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Show count
                    count = len(allocations_by_day[day])
                    st.caption(f"Total: {count} person{'s' if count != 1 else ''}")
                else:
                    st.markdown("""
                    <div style="background: #f5f5f5; padding: 1rem; border-radius: 6px; text-align: center; color: #666;">
                        🟦 Available
                    </div>
                    """, unsafe_allow_html=True)
        
        # Summary statistics
        total_bookings = sum(len(allocations_by_day[day]) for day in days)
        st.markdown(f"""
        <div style="background: #f0f8ff; padding: 1rem; border-radius: 8px; margin-top: 1rem; text-align: center;">
            <strong>📊 Total Oasis Bookings This Week: {total_bookings}</strong>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: #f8f9fa; padding: 2rem; border-radius: 8px; text-align: center;">
            <h4>🌴 No Oasis Allocations Yet</h4>
            <p style="color: #666; margin: 0;">Submit your preferences to get started!</p>
        </div>
        """, unsafe_allow_html=True)
