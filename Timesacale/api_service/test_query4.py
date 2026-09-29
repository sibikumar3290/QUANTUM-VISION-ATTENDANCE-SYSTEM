import database

conn = database.get_db_connection()
cursor = conn.cursor()
query = """
    SELECT time, metrics->>'statusHex', (metrics->>'shackleClosed')::boolean
    FROM elock_telemetry
    WHERE device_id = '675080192168' 
      AND (metrics->>'shackleClosed')::boolean = false
    ORDER BY time DESC
    LIMIT 1;
"""
cursor.execute(query)
print(cursor.fetchall())
