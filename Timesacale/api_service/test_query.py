import database
from datetime import datetime

conn = database.get_db_connection()
cursor = conn.cursor()
query = """
    SELECT time, metrics->>'shackleClosed' as shackle
    FROM elock_telemetry
    WHERE device_id = '675080192168'
    ORDER BY time DESC
    LIMIT 20;
"""
cursor.execute(query)
rows = cursor.fetchall()
print("Recent rows for 675080192168:")
for r in rows:
    print(r)
