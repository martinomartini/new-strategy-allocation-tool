import psycopg2
import sys

url = "postgresql://postgres.orrpkvjajaslmsqpaecu:KPMGtrainee123!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

try:
    conn = psycopg2.connect(url)
    print("SUCCESS")
    conn.close()
except Exception as e:
    print("FAILED")
    print(str(e))
    sys.exit(1)
