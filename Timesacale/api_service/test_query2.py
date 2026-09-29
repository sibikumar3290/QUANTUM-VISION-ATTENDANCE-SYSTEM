import database

conn = database.get_db_connection()
cursor = conn.cursor()
query = """
    SELECT time, (metrics->>'shackleClosed')::boolean as shackle_closed
    FROM elock_telemetry
    WHERE device_id = '675080192168' 
      AND (metrics->>'shackleClosed')::boolean = false
    ORDER BY time DESC
    LIMIT 10;
"""
cursor.execute(query)
rows = cursor.fetchall()
print("Rows where shackle is FALSE (opened):")
for r in rows:
    print(r)
