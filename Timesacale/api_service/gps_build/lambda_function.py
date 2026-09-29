"""
GPS Bad Data Detection Lambda
==============================
Validates GPS telemetry records based on:
  - India geographic bounds (lat/lon)
  - GSM signal range (1-5)
  - Speed jump between consecutive pings (> 250 km/h = GPS jump)
  - Ignition value (must be 0 or 1)

Triggered by: AWS IoT Core Rule (per incoming ping)
Writes:       bad_data_alerts table in TimescaleDB
"""

import json
import logging
import os
import datetime
import time
import math
import boto3

try:
    import psycopg2
    from psycopg2.extras import Json
except ImportError:
    psycopg2 = None

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_sm = boto3.client("secretsmanager")

# ── DB Config ────────────────────────────────────────────────────────────────
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")

_db_password_cache = {"value": None}

def _get_db_password() -> str:
    if _db_password_cache["value"] is None:
        secret_id = os.environ.get("WRITER_SECRET_ID")
        if secret_id:
            try:
                raw = _sm.get_secret_value(SecretId=secret_id)["SecretString"]
                try:
                    _db_password_cache["value"] = json.loads(raw)["password"]
                except (json.JSONDecodeError, KeyError):
                    _db_password_cache["value"] = raw
            except Exception as e:
                logger.exception(f"Secret fetch failed: {e}")
                _db_password_cache["value"] = os.environ.get("DB_PASSWORD")
        else:
            _db_password_cache["value"] = os.environ.get("DB_PASSWORD")
    return _db_password_cache["value"]

def _connect():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=_get_db_password(), connect_timeout=10
    )


# ── India Geographic Bounds ──────────────────────────────────────────────────
INDIA_LAT_MIN =  6.75
INDIA_LAT_MAX = 37.10
INDIA_LON_MIN = 68.12
INDIA_LON_MAX = 97.42

# ── Validation Thresholds ────────────────────────────────────────────────────
GSM_MIN        = 1
GSM_MAX        = 5
SPEED_JUMP_KMH = 250.0   # Max physically possible speed jump between 2 pings


# ── Haversine Distance ────────────────────────────────────────────────────────
def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Calculate the great-circle distance in km between two GPS points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ── Fetch Previous Ping ───────────────────────────────────────────────────────
def _get_previous_ping(conn, device_id: str, current_time: datetime.datetime):
    """Fetch the last known valid ping for speed-jump comparison."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT time, latitude, longitude
            FROM gps_telemetry
            WHERE device_id = %s
              AND time < %s
              AND latitude IS NOT NULL
              AND longitude IS NOT NULL
            ORDER BY time DESC
            LIMIT 1;
        """, (device_id, current_time))
        row = cur.fetchone()
    return row  # (time, lat, lon) or None


# ── Write Alert ───────────────────────────────────────────────────────────────
def _write_alert(conn, device_id: str, device_model: str,
                 detected_at: datetime.datetime, field: str,
                 bad_value, reason: str):
    """Insert a bad data alert record into the bad_data_alerts table."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bad_data_alerts (
                id            SERIAL,
                detected_at   TIMESTAMPTZ NOT NULL,
                device_id     TEXT NOT NULL,
                device_model  TEXT,
                detection_type TEXT,        -- 'GPS' | 'FUEL'
                field         TEXT,
                bad_value     TEXT,
                reason        TEXT
            );
        """)
        cur.execute("""
            INSERT INTO bad_data_alerts
                (detected_at, device_id, device_model, detection_type, field, bad_value, reason)
            VALUES (%s, %s, %s, 'GPS', %s, %s, %s);
        """, (detected_at, device_id, device_model,
              field, str(bad_value), reason))
    conn.commit()
    logger.warning("BAD GPS DATA | device=%s field=%s value=%s reason=%s",
                   device_id, field, bad_value, reason)


# ── Core Validation ───────────────────────────────────────────────────────────
def validate_gps(event: dict, conn) -> list:
    """
    Run all GPS bad-data checks.
    Returns a list of detected issues (empty = all valid).
    """
    issues = []
    device_id    = str(event.get("imei", ""))
    device_model = str(event.get("device_model", ""))
    ts_str       = event.get("fix_time") or event.get("time")

    try:
        detected_at = datetime.datetime.fromisoformat(ts_str)
    except Exception:
        detected_at = datetime.datetime.now(tz=datetime.timezone.utc)

    # ── 1. Latitude / Longitude (India bounds) ─────────────────────────────
    lat = event.get("latitude")
    lon = event.get("longitude")

    if lat is None or lon is None:
        issues.append(("lat_lon", None, "Missing latitude or longitude"))
        _write_alert(conn, device_id, device_model, detected_at, "lat_lon", None,
                     "Missing latitude or longitude")
    else:
        lat = float(lat)
        lon = float(lon)

        if lat == 0.0 and lon == 0.0:
            issues.append(("lat_lon", f"{lat},{lon}", "Null Island (0,0) - GPS lost fix"))
            _write_alert(conn, device_id, device_model, detected_at, "lat_lon",
                         f"{lat},{lon}", "Null Island (0,0) - GPS lost satellite fix")

        elif not (INDIA_LAT_MIN <= lat <= INDIA_LAT_MAX):
            issues.append(("latitude", lat, f"Outside India bounds ({INDIA_LAT_MIN}-{INDIA_LAT_MAX})"))
            _write_alert(conn, device_id, device_model, detected_at, "latitude",
                         lat, f"Latitude {lat} outside India range {INDIA_LAT_MIN}-{INDIA_LAT_MAX}")

        elif not (INDIA_LON_MIN <= lon <= INDIA_LON_MAX):
            issues.append(("longitude", lon, f"Outside India bounds ({INDIA_LON_MIN}-{INDIA_LON_MAX})"))
            _write_alert(conn, device_id, device_model, detected_at, "longitude",
                         lon, f"Longitude {lon} outside India range {INDIA_LON_MIN}-{INDIA_LON_MAX}")

        else:
            # ── Speed Jump check (requires previous ping) ──────────────────
            prev = _get_previous_ping(conn, device_id, detected_at)
            if prev:
                prev_time, prev_lat, prev_lon = prev
                time_diff_hr = max(
                    (detected_at - prev_time.replace(tzinfo=datetime.timezone.utc)).total_seconds() / 3600.0,
                    0.0001
                )
                dist_km   = _haversine_km(prev_lat, prev_lon, lat, lon)
                speed_kmh = dist_km / time_diff_hr

                if speed_kmh > SPEED_JUMP_KMH:
                    issues.append(("speed_jump", speed_kmh,
                                   f"GPS teleportation: {speed_kmh:.0f} km/h jump detected"))
                    _write_alert(conn, device_id, device_model, detected_at,
                                 "speed_jump", f"{speed_kmh:.0f} km/h",
                                 f"GPS jump: {dist_km:.1f} km in {time_diff_hr*60:.1f} min")

    # ── 2. GSM Signal (must be 1-5) ────────────────────────────────────────
    gsm = event.get("gsm_signal")
    if gsm is None:
        issues.append(("gsm_signal", None, "GSM signal missing"))
        _write_alert(conn, device_id, device_model, detected_at,
                     "gsm_signal", None, "GSM signal value is missing")
    else:
        gsm = float(gsm)
        if not (GSM_MIN <= gsm <= GSM_MAX):
            issues.append(("gsm_signal", gsm, f"GSM out of range (must be {GSM_MIN}-{GSM_MAX})"))
            _write_alert(conn, device_id, device_model, detected_at,
                         "gsm_signal", gsm,
                         f"GSM value {gsm} out of valid range {GSM_MIN}-{GSM_MAX}")

    # ── 3. Ignition (must be 0 or 1) ──────────────────────────────────────
    ignition = event.get("ignition")
    if ignition is None:
        issues.append(("ignition", None, "Ignition value missing"))
        _write_alert(conn, device_id, device_model, detected_at,
                     "ignition", None, "Ignition value is missing")
    else:
        try:
            ign_val = int(float(ignition))
            if ign_val not in (0, 1):
                issues.append(("ignition", ign_val, f"Invalid ignition value {ign_val} (must be 0 or 1)"))
                _write_alert(conn, device_id, device_model, detected_at,
                             "ignition", ign_val,
                             f"Ignition value {ign_val} is invalid. Only 0 (OFF) or 1 (ON) allowed.")
        except (TypeError, ValueError):
            issues.append(("ignition", ignition, "Non-numeric ignition value"))
            _write_alert(conn, device_id, device_model, detected_at,
                         "ignition", ignition, "Non-numeric ignition value received")

    return issues


# ── Lambda Handler ────────────────────────────────────────────────────────────
def lambda_handler(event, context):
    if not psycopg2:
        logger.error("psycopg2 is not installed.")
        return {"statusCode": 500, "body": "psycopg2 not available"}

    try:
        logger.info("GPS Bad Data Detection - Received: %s", json.dumps(event))
        payload = json.loads(event["body"]) if "body" in event else event

        conn   = _connect()
        issues = validate_gps(payload, conn)
        conn.close()

        status = "BAD_DATA" if issues else "VALID"
        logger.info("GPS validation result: %s | issues: %d", status, len(issues))

        return {
            "statusCode": 200,
            "body": json.dumps({
                "status":    status,
                "imei":      payload.get("imei"),
                "issues":    [{"field": f, "value": str(v), "reason": r} for f, v, r in issues],
                "is_valid":  len(issues) == 0
            })
        }

    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
