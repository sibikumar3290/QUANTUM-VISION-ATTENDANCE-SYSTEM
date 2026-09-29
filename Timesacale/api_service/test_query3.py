import database
import json

conn = database.get_db_connection()
cursor = conn.cursor()
query = """
    SELECT metrics
    FROM elock_telemetry
    WHERE device_id = '675080192168' 
    ORDER BY time DESC
    LIMIT 2;
"""
cursor.execute(query)
rows = cursor.fetchall()
print("Metrics for 675080192168:")
for r in rows:
    print(json.dumps(r[0], indent=2))
