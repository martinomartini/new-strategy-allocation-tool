#!/usr/bin/env python3
import psycopg2

DATABASE_URL = "postgresql://postgres.orrpkvjajaslmsqpaecu:KPMGtrainee123!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

print("Testing Supabase connection...")
try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT 1")
    result = cur.fetchone()
    print(f"✅ Success: {result}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Failed: {e}")
