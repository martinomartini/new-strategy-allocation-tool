"""
Analytics and statistics functions for the Room Allocation System.
"""
from datetime import timedelta
from .database import execute_query
from .week_management import get_current_week
from config import PROJECT_ROOMS, OASIS_CONFIG

def get_weekly_usage_stats():
    """Get comprehensive usage statistics for the current week."""
    current_week = get_current_week()
    
    # Room usage statistics
    room_usage_query = """
        SELECT 
            wa.room_name,
            COUNT(*) as bookings,
            COUNT(DISTINCT wa.team_name) as unique_teams,
            STRING_AGG(DISTINCT wa.team_name, ', ') as teams
        FROM weekly_allocations wa
        WHERE wa.date >= %s AND wa.date <= %s AND wa.room_name != 'Oasis'
        GROUP BY wa.room_name
        ORDER BY bookings DESC
    """
    start_date = current_week
    end_date = current_week + timedelta(days=4)
    
    room_stats = execute_query(room_usage_query, (start_date, end_date), fetch_all=True)
    
    # Oasis usage statistics
    oasis_usage_query = """
        SELECT 
            DATE_PART('dow', oa.date) as day_of_week,
            TO_CHAR(oa.date, 'Day') as day_name,
            COUNT(*) as bookings,
            COUNT(DISTINCT oa.person_name) as unique_people,
            STRING_AGG(oa.person_name, ', ') as people
        FROM oasis_allocations oa
        WHERE oa.date >= %s AND oa.date <= %s
        GROUP BY DATE_PART('dow', oa.date), TO_CHAR(oa.date, 'Day'), oa.date
        ORDER BY oa.date
    """
    
    oasis_stats = execute_query(oasis_usage_query, (start_date, end_date), fetch_all=True)
    
    # Overall capacity utilization
    total_room_capacity = sum(room['capacity'] for room in PROJECT_ROOMS) * 4  # 4 days
    total_oasis_capacity = OASIS_CONFIG['capacity'] * 5  # 5 days
    
    total_room_bookings = sum(stat['bookings'] for stat in room_stats) if room_stats else 0
    total_oasis_bookings = sum(stat['bookings'] for stat in oasis_stats) if oasis_stats else 0
    
    return {
        'room_stats': room_stats,
        'oasis_stats': oasis_stats,
        'room_utilization': (total_room_bookings / total_room_capacity * 100) if total_room_capacity > 0 else 0,
        'oasis_utilization': (total_oasis_bookings / total_oasis_capacity * 100) if total_oasis_capacity > 0 else 0,
        'total_room_bookings': total_room_bookings,
        'total_oasis_bookings': total_oasis_bookings
    }

def get_all_time_usage_stats():
    """Get comprehensive usage statistics across all time periods."""
    # Room usage statistics - all time
    room_usage_query = """
        SELECT 
            wa.room_name,
            COUNT(*) as total_bookings,
            COUNT(DISTINCT wa.team_name) as unique_teams,
            COUNT(DISTINCT DATE_TRUNC('week', wa.date)) as weeks_used,
            MIN(wa.date) as first_booking,
            MAX(wa.date) as last_booking
        FROM weekly_allocations wa
        WHERE wa.room_name != 'Oasis'
        GROUP BY wa.room_name
        ORDER BY total_bookings DESC
    """
    
    room_stats = execute_query(room_usage_query, fetch_all=True)
    
    # Oasis usage statistics - all time
    oasis_usage_query = """
        SELECT 
            COUNT(*) as total_bookings,
            COUNT(DISTINCT oa.person_name) as unique_people,
            COUNT(DISTINCT DATE_TRUNC('week', oa.date)) as weeks_used,
            MIN(oa.date) as first_booking,
            MAX(oa.date) as last_booking,
            COUNT(DISTINCT CASE WHEN DATE_PART('dow', oa.date) = 1 THEN oa.date END) as monday_bookings,
            COUNT(DISTINCT CASE WHEN DATE_PART('dow', oa.date) = 2 THEN oa.date END) as tuesday_bookings,
            COUNT(DISTINCT CASE WHEN DATE_PART('dow', oa.date) = 3 THEN oa.date END) as wednesday_bookings,
            COUNT(DISTINCT CASE WHEN DATE_PART('dow', oa.date) = 4 THEN oa.date END) as thursday_bookings,
            COUNT(DISTINCT CASE WHEN DATE_PART('dow', oa.date) = 5 THEN oa.date END) as friday_bookings
        FROM oasis_allocations oa
    """
    
    oasis_stats = execute_query(oasis_usage_query, fetch_one=True)
    
    # Weekly trends
    weekly_trends_query = """
        SELECT 
            DATE_TRUNC('week', combined.date) as week_start,
            SUM(CASE WHEN combined.type = 'room' THEN 1 ELSE 0 END) as room_bookings,
            SUM(CASE WHEN combined.type = 'oasis' THEN 1 ELSE 0 END) as oasis_bookings
        FROM (
            SELECT date, 'room' as type FROM weekly_allocations WHERE room_name != 'Oasis'
            UNION ALL
            SELECT date, 'oasis' as type FROM oasis_allocations
        ) combined
        GROUP BY DATE_TRUNC('week', combined.date)
        ORDER BY week_start DESC
        LIMIT 10
    """
    
    weekly_trends = execute_query(weekly_trends_query, fetch_all=True)
    
    return {
        'room_stats': room_stats,
        'oasis_stats': oasis_stats,
        'weekly_trends': weekly_trends
    }

def get_user_analytics():
    """Get individual user analytics across all weeks."""
    # Team/Contact person analytics for room bookings
    team_analytics_query = """
        SELECT 
            wp.contact_person,
            wp.team_name,
            COUNT(DISTINCT wa.date) as total_room_days,
            COUNT(DISTINCT DATE_TRUNC('week', wa.date)) as total_weeks_with_rooms,
            STRING_AGG(DISTINCT wa.room_name, ', ') as rooms_used,
            MIN(wa.date) as first_booking,
            MAX(wa.date) as last_booking
        FROM weekly_preferences wp
        LEFT JOIN weekly_allocations wa ON wp.team_name = wa.team_name
        WHERE wa.room_name != 'Oasis' OR wa.room_name IS NULL
        GROUP BY wp.contact_person, wp.team_name
        ORDER BY total_room_days DESC NULLS LAST
    """
    
    team_analytics = execute_query(team_analytics_query, fetch_all=True)
    
    # Individual Oasis analytics
    oasis_analytics_query = """
        SELECT 
            op.person_name,
            COUNT(DISTINCT oa.date) as total_oasis_days,
            COUNT(DISTINCT DATE_TRUNC('week', oa.date)) as total_weeks_with_oasis,
            MIN(oa.date) as first_oasis_booking,
            MAX(oa.date) as last_oasis_booking,
            COUNT(DISTINCT CASE WHEN DATE_PART('dow', oa.date) = 1 THEN oa.date END) as monday_bookings,
            COUNT(DISTINCT CASE WHEN DATE_PART('dow', oa.date) = 2 THEN oa.date END) as tuesday_bookings,
            COUNT(DISTINCT CASE WHEN DATE_PART('dow', oa.date) = 3 THEN oa.date END) as wednesday_bookings,
            COUNT(DISTINCT CASE WHEN DATE_PART('dow', oa.date) = 4 THEN oa.date END) as thursday_bookings,
            COUNT(DISTINCT CASE WHEN DATE_PART('dow', oa.date) = 5 THEN oa.date END) as friday_bookings
        FROM oasis_preferences op
        LEFT JOIN oasis_allocations oa ON op.person_name = oa.person_name
        GROUP BY op.person_name
        ORDER BY total_oasis_days DESC NULLS LAST
    """
    
    oasis_analytics = execute_query(oasis_analytics_query, fetch_all=True)
    
    # Combined analytics - people who use both services
    combined_analytics_query = """
        SELECT 
            COALESCE(team_data.contact_person, oasis_data.person_name) as person_name,
            COALESCE(team_data.total_room_days, 0) as room_days,
            COALESCE(oasis_data.total_oasis_days, 0) as oasis_days,
            COALESCE(team_data.total_weeks_with_rooms, 0) as room_weeks,
            COALESCE(oasis_data.total_weeks_with_oasis, 0) as oasis_weeks,
            CASE 
                WHEN team_data.contact_person IS NOT NULL AND oasis_data.person_name IS NOT NULL THEN 'Both'
                WHEN team_data.contact_person IS NOT NULL THEN 'Rooms Only'
                ELSE 'Oasis Only'
            END as usage_type
        FROM (
            SELECT 
                wp.contact_person,
                COUNT(DISTINCT wa.date) as total_room_days,
                COUNT(DISTINCT DATE_TRUNC('week', wa.date)) as total_weeks_with_rooms
            FROM weekly_preferences wp
            LEFT JOIN weekly_allocations wa ON wp.team_name = wa.team_name
            WHERE wa.room_name != 'Oasis' OR wa.room_name IS NULL
            GROUP BY wp.contact_person
        ) team_data
        FULL OUTER JOIN (
            SELECT 
                op.person_name,
                COUNT(DISTINCT oa.date) as total_oasis_days,
                COUNT(DISTINCT DATE_TRUNC('week', oa.date)) as total_weeks_with_oasis
            FROM oasis_preferences op
            LEFT JOIN oasis_allocations oa ON op.person_name = oa.person_name
            GROUP BY op.person_name
        ) oasis_data ON team_data.contact_person = oasis_data.person_name
        ORDER BY (COALESCE(team_data.total_room_days, 0) + COALESCE(oasis_data.total_oasis_days, 0)) DESC
    """
    
    combined_analytics = execute_query(combined_analytics_query, fetch_all=True)
    return {
        'team_analytics': team_analytics,
        'oasis_analytics': oasis_analytics,
        'combined_analytics': combined_analytics
    }
