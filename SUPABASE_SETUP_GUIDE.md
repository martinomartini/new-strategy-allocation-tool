# 🚀 Supabase Setup Guide for Room Allocation System

This guide will walk you through setting up Supabase for your office room and Oasis booking system.

## 📋 Table of Contents
1. [Create Supabase Project](#1-create-supabase-project)
2. [Database Schema Setup](#2-database-schema-setup)
3. [Streamlit Configuration](#3-streamlit-configuration)
4. [Security & Authentication](#4-security--authentication)
5. [Testing the Connection](#5-testing-the-connection)
6. [Deployment Configuration](#6-deployment-configuration)

---

## 1. Create Supabase Project

### Step 1: Sign up for Supabase
1. Go to [supabase.com](https://supabase.com)
2. Click "Start your project" → Sign up with GitHub/Google
3. Create a new organization (or use existing)

### Step 2: Create New Project
1. Click "New Project"
2. Choose your organization
3. Fill in project details:
   - **Name**: `office-room-allocator`
   - **Database Password**: Generate a strong password ⚠️ **SAVE THIS PASSWORD**
   - **Region**: Choose closest to your location
   - **Pricing Plan**: Free tier is sufficient for testing

### Step 3: Wait for Project Setup
- This takes 2-3 minutes
- You'll see a "Setting up your project..." screen

---

## 2. Database Schema Setup

### Step 1: Access SQL Editor
1. In your Supabase dashboard, click **"SQL Editor"** in the left sidebar
2. Click **"New Query"**

### Step 2: Create Main Tables
Copy and paste this SQL script to create all required tables:

```sql
-- Main preferences tables
CREATE TABLE weekly_preferences (
    id SERIAL PRIMARY KEY,
    team_name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    team_size INT NOT NULL,
    preferred_days VARCHAR(255) NOT NULL,
    submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE oasis_preferences (
    id SERIAL PRIMARY KEY,
    person_name VARCHAR(255) NOT NULL,
    preferred_day_1 VARCHAR(50),
    preferred_day_2 VARCHAR(50),
    preferred_day_3 VARCHAR(50),
    preferred_day_4 VARCHAR(50),
    preferred_day_5 VARCHAR(50),
    submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Allocation tables
CREATE TABLE weekly_allocations (
    id SERIAL PRIMARY KEY,
    team_name VARCHAR(255) NOT NULL,
    room_name VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE oasis_allocations (
    id SERIAL PRIMARY KEY,
    person_name VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admin settings table for week management
CREATE TABLE admin_settings (
    setting_key VARCHAR(255) PRIMARY KEY,
    setting_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Archive tables for historical data
CREATE TABLE weekly_archive (
    id SERIAL PRIMARY KEY,
    week_monday DATE NOT NULL,
    team_name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    team_size INT,
    preferred_days VARCHAR(255),
    submission_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE oasis_archive (
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
);
```

### Step 3: Run the Script
1. Click **"Run"** to execute the SQL
2. You should see "Success" messages for each table creation
3. Verify in the **"Table Editor"** that all 7 tables were created

### Step 4: Set Initial Week (Optional)
```sql
-- Set the current week (change the date to your desired Monday)
INSERT INTO admin_settings (setting_key, setting_value) 
VALUES ('current_week_monday', '2025-06-09');
```

---

## 3. Streamlit Configuration

### Step 1: Get Connection Details
1. In Supabase dashboard, go to **"Settings"** → **"Database"**
2. Scroll down to **"Connection string"**
3. Copy the **"URI"** format connection string:
   ```
   postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-eu-west-1.pooler.supabase.com:6543/postgres
   ```

### Step 2: Create Streamlit Secrets File
Create `.streamlit/secrets.toml` in your project directory:

```toml
# .streamlit/secrets.toml
SUPABASE_DB_URI = "postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"
ADMIN_PASSWORD = "your_admin_password_here"
OFFICE_TIMEZONE = "Europe/Amsterdam"
```

⚠️ **Important**: 
- Replace `[YOUR-PASSWORD]` with your actual database password
- Replace `xxxxx` with your project reference
- Choose your admin password
- Set your timezone

### Step 3: Add to .gitignore
```gitignore
# Add to .gitignore
.streamlit/secrets.toml
```

---

## 4. Security & Authentication

### Step 1: Database Security
Your app uses direct PostgreSQL connections, so:
1. Go to **"Settings"** → **"Database"**
2. Under **"Connection pooling"**, ensure:
   - **Pool Mode**: Transaction
   - **Connection limit**: Default (15)

### Step 2: Row Level Security (Optional)
For production, you may want to enable RLS:
```sql
-- Enable RLS on tables (optional for internal apps)
ALTER TABLE weekly_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE oasis_preferences ENABLE ROW LEVEL SECURITY;
-- etc.
```

### Step 3: API Access (Not needed for this app)
Your app doesn't use Supabase's API features, only direct PostgreSQL access.

---

## 5. Testing the Connection

### Step 1: Test Script
Create a test file `test_supabase_connection.py`:

```python
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = "your_connection_string_here"

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Test connection
    cur.execute("SELECT 1")
    result = cur.fetchone()
    print("✅ Connection successful!", result)
    
    # Test tables exist
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cur.fetchall()
    print("📋 Tables found:", [t[0] for t in tables])
    
    conn.close()
    
except Exception as e:
    print("❌ Connection failed:", e)
```

### Step 2: Run Test
```bash
python test_supabase_connection.py
```

Expected output:
```
✅ Connection successful! (1,)
📋 Tables found: ['weekly_preferences', 'oasis_preferences', 'weekly_allocations', 'oasis_allocations', 'admin_settings', 'weekly_archive', 'oasis_archive']
```

---

## 6. Deployment Configuration

### For Streamlit Cloud:
1. Push your code to GitHub
2. Connect to Streamlit Cloud
3. In **"Advanced settings"** → **"Secrets"**, add:
   ```toml
   SUPABASE_DB_URI = "your_connection_string"
   ADMIN_PASSWORD = "your_admin_password"
   OFFICE_TIMEZONE = "Europe/Amsterdam"
   ```

### For Other Platforms:
Set environment variables:
```bash
export SUPABASE_DB_URI="your_connection_string"
export ADMIN_PASSWORD="your_admin_password"  
export OFFICE_TIMEZONE="Europe/Amsterdam"
```

---

## 🎯 Quick Start Checklist

- [ ] Create Supabase project
- [ ] Save database password securely
- [ ] Run SQL schema creation script
- [ ] Get connection string from Settings → Database  
- [ ] Create `.streamlit/secrets.toml` with connection details
- [ ] Test connection with test script
- [ ] Run your Streamlit app: `streamlit run app.py`
- [ ] Test admin login and basic functionality

---

## 🔧 Troubleshooting

### Connection Issues:
- **"password authentication failed"**: Check password in connection string
- **"connection timeout"**: Check internet connection and Supabase status
- **"database does not exist"**: Use the correct database name (usually `postgres`)

### Permission Issues:
- Ensure your IP is allowed (Supabase allows all by default)
- Check if you're using the correct connection string format

### Table Issues:
- Run the schema script again if tables are missing
- Check table names match exactly (case-sensitive)

---

## 📞 Support

- **Supabase Docs**: [docs.supabase.com](https://docs.supabase.com)
- **Supabase Discord**: Join their community for help
- **PostgreSQL Docs**: For database-specific questions

---

**🎉 You're now ready to run your room allocation system with Supabase!**
