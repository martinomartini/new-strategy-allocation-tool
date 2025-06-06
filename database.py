"""
Database connection and query operations for the Room Allocation System.
"""
import streamlit as st
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
from config import DATABASE_URL

# -----------------------------------------------------
# Database Connection Pool
# -----------------------------------------------------
@st.cache_resource
def get_db_connection_pool():
    """Create and cache database connection pool."""
    if not DATABASE_URL:
        st.error("Database URL not configured.")
        return None
    
    try:
        return psycopg2.pool.SimpleConnectionPool(
            1, 20,
            DATABASE_URL,
            cursor_factory=RealDictCursor
        )
    except Exception as e:
        st.error(f"Failed to create database connection pool: {e}")
        return None

# -----------------------------------------------------
# Database Operations
# -----------------------------------------------------
def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """Execute database query with proper connection handling."""
    pool = get_db_connection_pool()
    if not pool:
        return None
    
    conn = None
    try:
        conn = pool.getconn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            
            if fetch_one:
                result = cur.fetchone()
            elif fetch_all:
                result = cur.fetchall()
            else:
                result = True
            
            conn.commit()
            return result
            
    except Exception as e:
        if conn:
            conn.rollback()
        st.error(f"Database error: {e}")
        return None
    finally:
        if conn:
            pool.putconn(conn)

def create_archive_tables():
    """Create archive tables for historical data."""
    archive_tables = [
        """
        CREATE TABLE IF NOT EXISTS weekly_archive (
            id SERIAL PRIMARY KEY,
            week_monday DATE NOT NULL,
            team_name VARCHAR(255) NOT NULL,
            contact_person VARCHAR(255),
            team_size INT,
            preferred_days VARCHAR(255),
            submission_time TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS oasis_archive (
            id SERIAL PRIMARY KEY,
            week_monday DATE NOT NULL,
            person_name VARCHAR(255) NOT NULL,
            preferred_day_1 VARCHAR(50),
            preferred_day_2 VARCHAR(50),
            preferred_day_3 VARCHAR(50),
            preferred_day_4 VARCHAR(50),
            preferred_day_5 VARCHAR(50),
            submission_time TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    ]
    for query in archive_tables:
        execute_query(query)

def create_admin_settings_table():
    """Ensure admin_settings table exists."""
    create_table_query = """
        CREATE TABLE IF NOT EXISTS admin_settings (
            setting_key VARCHAR(255) PRIMARY KEY,
            setting_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    execute_query(create_table_query)
