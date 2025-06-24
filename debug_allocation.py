import psycopg2

DATABASE_URL = 'postgresql://postgres.orrpkvjajaslmsqpaecu:KPMGtrainee123!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print('=== CHECKING TABLES ===')
cur.execute("SELECT COUNT(*) FROM weekly_preferences")
print(f'Weekly preferences count: {cur.fetchone()[0]}')

cur.execute("SELECT COUNT(*) FROM weekly_allocations")
print(f'Weekly allocations count: {cur.fetchone()[0]}')

print('\n=== CURRENT WEEK SETTING ===')
cur.execute("SELECT setting_value FROM admin_settings WHERE setting_key = 'current_week_monday'")
result = cur.fetchone()
if result:
    print(f'Current week Monday: {result[0]}')
else:
    print('No current week set')

print('\n=== ALL TEAM PREFERENCES ===')
cur.execute('SELECT team_name, preferred_days, submission_time FROM weekly_preferences ORDER BY submission_time DESC')
prefs = cur.fetchall()
if prefs:
    for row in prefs:
        print(f'Team: {row[0]}, Preferred Days: {row[1]}, Submitted: {row[2]}')
else:
    print('No team preferences found')

print('\n=== ALL ALLOCATIONS ===')
cur.execute('SELECT team_name, room_name, date FROM weekly_allocations ORDER BY date, team_name')
allocs = cur.fetchall()
if allocs:
    for row in allocs:
        print(f'Team: {row[0]}, Room: {row[1]}, Date: {row[2]} ({row[2].strftime("%A")})')
else:
    print('No allocations found')

conn.close()
