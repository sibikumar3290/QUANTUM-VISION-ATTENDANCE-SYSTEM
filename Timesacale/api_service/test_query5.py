import database
from datetime import datetime, date, time

conn = database.get_db_connection()
cursor = conn.cursor()
query = """
    SELECT time, (metrics->>'sealed')::boolean as sealed, (metrics->>'shackleClosed')::boolean as shackle_closed
    FROM elock_telemetry
    WHERE device_id = '675080192168'
      AND time >= '2026-09-29 00:00:00'
    ORDER BY time DESC
    LIMIT 30;
"""
cursor.execute(query)
rows = cursor.fetchall()
for r in rows:
    print(r)
