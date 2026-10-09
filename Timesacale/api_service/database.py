import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime, date, time

load_dotenv()
logger = logging.getLogger("api_db")

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

def get_db_connection():
    """
    Establish and return a connection to TimescaleDB.
    Uses psycopg2 to open a TCP connection to the PostgreSQL server.
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=10 # Prevents the API from hanging forever if the DB is unreachable
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise e

def build_history_query(table_name, imei=None, start_time=None, end_time=None, last_24_hours=False, limit=1000):
    """
    Dynamically builds the SQL query based on provided filters.
    Instead of writing multiple different SQL queries for every combination of filters, 
    this function constructs the WHERE clause dynamically based on what the user requested.
    """
    query = f"SELECT time, device_id, device_model, latitude, longitude, metrics FROM {table_name} WHERE 1=1"
    params = []
    
    if imei:
        query += " AND device_id = %s"
        params.append(imei)
        
    if last_24_hours:
        query += " AND time >= NOW() - INTERVAL '24 HOURS'"
    else:
        if start_time:
            query += " AND time >= %s"
            params.append(start_time)
        if end_time:
            query += " AND time <= %s"
            params.append(end_time)
            
    query += " ORDER BY time DESC LIMIT %s;"
    params.append(limit)
    return query, params

def fetch_latest(table_name: str, imei: str = None, merge_tpms: bool = False):
    """
    Fetches the latest recorded point for each device.
    If merge_tpms is True, it fetches the latest GPS ping AND the latest TPMS sensor pings, 
    and merges them together into a single JSON object.
    """
    conn = get_db_connection()
    try:
        # RealDictCursor ensures that rows are returned as Python dictionaries instead of plain tuples
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if merge_tpms:
                # 1. Fetch exact latest GPS row per device using PostgreSQL's DISTINCT ON
                query_base = f"""
                    SELECT DISTINCT ON (device_id) 
                        time, device_id, device_model, latitude, longitude, metrics
                    FROM {table_name}
                """
                params = []
                if imei:
                    query_base += " WHERE device_id = %s"
                    params.append(imei)
                # ORDER BY device_id, time DESC ensures DISTINCT ON picks the absolute newest row per device
                query_base += " ORDER BY device_id, time DESC;"
                cursor.execute(query_base, tuple(params))
                base_rows = cursor.fetchall()
                
                # 2. Fetch latest TPMS sensor states from the last 24 hours
                # Because TPMS sensors ping randomly (only when pressure changes), we have to look back 
                # 24 hours to find their last known state, unpacking the nested JSON array.
                query_tpms = f"""
                    SELECT DISTINCT ON (device_id, tpms_obj->>'sensor_id')
                        device_id,
                        tpms_obj as tpms_data,
                        time
                    FROM (
                        SELECT device_id, time, jsonb_array_elements(metrics->'tpms') as tpms_obj
                        FROM {table_name}
                        WHERE time >= NOW() - INTERVAL '30 DAYS'
                          AND metrics ? 'tpms'
                          {"AND device_id = %s" if imei else ""}
                        ORDER BY time DESC
                    ) sub
                    ORDER BY device_id, tpms_obj->>'sensor_id', time DESC;
                """
                cursor.execute(query_tpms, tuple(params))
                tpms_rows = cursor.fetchall()
                
                # 3. Group TPMS by device
                device_tpms = {}
                for tr in tpms_rows:
                    did = tr["device_id"]
                    tdata = tr["tpms_data"]
                    # Inject the exact timestamp when this specific sensor last reported
                    tdata["timestamp"] = tr["time"].isoformat() if hasattr(tr["time"], "isoformat") else str(tr["time"])
                    if did not in device_tpms:
                        device_tpms[did] = []
                    device_tpms[did].append(tdata)
                    
                # 4. Merge TPMS data into base GPS rows
                for row in base_rows:
                    did = row["device_id"]
                    if not row.get("metrics"):
                        row["metrics"] = {}
                        
                    # If TPMS history was found, inject it
                    if did in device_tpms:
                        row["metrics"]["tpms"] = device_tpms[did]
                        
                    # Postgres JSONB destroys key order. To ensure "tpms" appears at the 
                    # very bottom of the API response, we pop and re-insert it.
                    if "tpms" in row["metrics"]:
                        tpms_val = row["metrics"].pop("tpms")
                        row["metrics"]["tpms"] = tpms_val
                        
                return base_rows
            else:
                # Simple exact latest row for E-Locks and Alarms
                query = f"""
                    SELECT DISTINCT ON (device_id) 
                        time, device_id, device_model, latitude, longitude, active_alarms, metrics
                    FROM {table_name}
                """
                # Handle tables that don't have active_alarms column (like elock_telemetry)
                if table_name != "elock_alarms":
                    query = query.replace(", active_alarms", "")
                    
                params = []
                if imei:
                    query += " WHERE device_id = %s"
                    params.append(imei)
                    
                query += " ORDER BY device_id, time DESC;"
                cursor.execute(query, tuple(params))
                return cursor.fetchall()
    finally:
        conn.close()

def fetch_lock_events(imei: str, target_date: date):
    """Calculates open/close state transitions for a given day."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            from datetime import datetime, time
            start_time = datetime.combine(target_date, time.min)
            end_time = datetime.combine(target_date, time.max)
            
            query = """
                SELECT time, latitude, longitude, 
                       (metrics->>'sealed')::boolean as sealed_status,
                       (metrics->>'shackleClosed')::boolean as shackle_closed
                FROM elock_telemetry
                WHERE device_id = %s AND time >= %s AND time <= %s
                ORDER BY time ASC;
            """
            cursor.execute(query, (imei, start_time, end_time))
            rows = cursor.fetchall()
            
            events = []
            prev_closed = None
            
            for row in rows:
                sealed = row["sealed_status"]
                shackle = row["shackle_closed"]
                
                # If both are missing, we skip
                if sealed is None and shackle is None:
                    continue
                    
                # The lock is considered CLOSED only if BOTH are true (or if one is missing, the other is true)
                # If either is explicitly False, the lock is OPENED.
                is_closed = (sealed is not False) and (shackle is not False)
                    
                # Initialize state on first row
                if prev_closed is None:
                    prev_closed = is_closed
                    continue
                    
                # Detect state change
                if is_closed != prev_closed:
                    events.append({
                        "time": row["time"].isoformat() if hasattr(row["time"], "isoformat") else str(row["time"]),
                        "event": "CLOSED" if is_closed else "OPENED",
                        "latitude": row["latitude"],
                        "longitude": row["longitude"]
                    })
                    prev_closed = is_closed
                    
            return events
    finally:
        conn.close()

def fetch_history(table_name: str, imei: str = None, start_time: str = None, end_time: str = None, last_24_hours: bool = False, limit: int = 1000):
    """Fetches historical data with filtering."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query, params = build_history_query(table_name, imei, start_time, end_time, last_24_hours, limit)
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            
            # Ensure "tpms" is at the very bottom of the metrics dictionary in historical data as well
            for row in rows:
                if row.get("metrics") and "tpms" in row["metrics"]:
                    tpms_val = row["metrics"].pop("tpms")
                    row["metrics"]["tpms"] = tpms_val
                    
            return rows
    finally:
        conn.close()
