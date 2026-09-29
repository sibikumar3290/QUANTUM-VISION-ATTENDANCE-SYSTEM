"""
Fuel Bad Data Detection Lambda
================================
Validates fuel sensor telemetry records based on:
  - Fuel RAW value range:  Valid = 1 to 4094
  - Sensor disconnected:   RAW = -4  (cable cut / unplugged)
  - Sensor fault:          RAW = 4095 (hardware max / short circuit)
  - Liquid slosh:          Fuel drop > 30% between consecutive pings

Triggered by: AWS IoT Core Rule (per incoming ping)
Writes:       bad_data_alerts table in TimescaleDB
"""

import json
import logging
import os
import datetime
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


# ── Fuel Validation Constants ─────────────────────────────────────────────────
FUEL_RAW_MIN          = 1       # Minimum valid RAW value
FUEL_RAW_MAX          = 4094    # Maximum valid RAW value
FUEL_RAW_FAULT        = 4095    # Hardware short circuit / sensor fault
FUEL_DISCONNECTED     = -4      # Sensor cable cut / unplugged
FUEL_TEMP_DISCONNECT  = -128    # Temperature probe disconnected
SLOSH_DROP_PERCENT    = 30.0    # Max allowed % fuel drop between 2 pings

# LLS fuel sensor fields to validate (matches our generic metrics schema)
FUEL_LEVEL_FIELDS = [
    "lls1_fuel_level",
    "lls2_fuel_level",
    "lls3_fuel_level",
    "lls4_fuel_level",
    "lls5_fuel_level",
]

FUEL_TEMP_FIELDS = [
    "lls1_temperature",
    "lls2_temperature",
    "lls3_temperature",
    "lls4_temperature",
    "lls5_temperature",
]


# ── Write Alert ───────────────────────────────────────────────────────────────
def _write_alert(conn, device_id: str, device_model: str,
                 detected_at: datetime.datetime, field: str,
                 bad_value, reason: str):
    """Insert a bad data alert into the bad_data_alerts table."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bad_data_alerts (
                id            SERIAL,
                detected_at   TIMESTAMPTZ NOT NULL,
                device_id     TEXT NOT NULL,
                device_model  TEXT,
                detection_type TEXT,
                field         TEXT,
                bad_value     TEXT,
                reason        TEXT
            );
        """)
        cur.execute("""
            INSERT INTO bad_data_alerts
                (detected_at, device_id, device_model, detection_type, field, bad_value, reason)
            VALUES (%s, %s, %s, 'FUEL', %s, %s, %s);
        """, (detected_at, device_id, device_model,
              field, str(bad_value), reason))
    conn.commit()
    logger.warning("BAD FUEL DATA | device=%s field=%s value=%s reason=%s",
                   device_id, field, bad_value, reason)


# ── Fetch Previous Fuel Ping ──────────────────────────────────────────────────
def _get_previous_fuel(conn, device_id: str, field: str,
                       current_time: datetime.datetime):
    """
    Fetch the last valid fuel RAW value for liquid slosh comparison.
    Looks inside the metrics JSONB column.
    """
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT time, (metrics->>%s)::FLOAT AS fuel_raw
            FROM gps_telemetry
            WHERE device_id = %s
              AND time < %s
              AND metrics ? %s
              AND (metrics->>%s)::FLOAT BETWEEN %s AND %s
            ORDER BY time DESC
            LIMIT 1;
        """, (field, device_id, current_time, field, field,
              FUEL_RAW_MIN, FUEL_RAW_MAX))
        return cur.fetchone()  # (time, fuel_raw) or None


# ── Core Validation ───────────────────────────────────────────────────────────
def validate_fuel(event: dict, conn) -> list:
    """
    Run all fuel bad-data checks.
    Returns a list of detected issues (empty = all valid).
    """
    issues = []
    device_id    = str(event.get("imei", ""))
    device_model = str(event.get("device_model", ""))
    ts_str       = event.get("fix_time") or event.get("time")
    metrics      = event.get("metrics", event)  # Support both flat and nested

    try:
        detected_at = datetime.datetime.fromisoformat(ts_str)
    except Exception:
        detected_at = datetime.datetime.now(tz=datetime.timezone.utc)

    # ── Validate each LLS fuel level sensor ───────────────────────────────
    for field in FUEL_LEVEL_FIELDS:
        raw_val = metrics.get(field)
        if raw_val is None:
            continue  # Sensor not present on this device - skip

        try:
            raw = float(raw_val)
        except (TypeError, ValueError):
            issues.append((field, raw_val, "Non-numeric fuel RAW value"))
            _write_alert(conn, device_id, device_model, detected_at,
                         field, raw_val, "Non-numeric fuel RAW value received")
            continue

        # ── Rule 1: Sensor Disconnected (cable cut) ────────────────────────
        if raw == FUEL_DISCONNECTED:
            issues.append((field, raw, "Sensor disconnected (cable cut/unplugged). RAW = -4"))
            _write_alert(conn, device_id, device_model, detected_at,
                         field, raw,
                         "Fuel sensor disconnected. RAW value = -4 indicates cable cut or unplugged sensor.")
            continue

        # ── Rule 2: Hardware Fault (short circuit) ─────────────────────────
        if raw == FUEL_RAW_FAULT:
            issues.append((field, raw, "Sensor hardware fault (short circuit). RAW = 4095"))
            _write_alert(conn, device_id, device_model, detected_at,
                         field, raw,
                         "Fuel sensor hardware fault. RAW = 4095 indicates sensor short circuit or diagnostic mode.")
            continue

        # ── Rule 3: Out of valid range ─────────────────────────────────────
        if raw < FUEL_RAW_MIN or raw > FUEL_RAW_MAX:
            issues.append((field, raw,
                           f"RAW value {raw} outside valid range ({FUEL_RAW_MIN}-{FUEL_RAW_MAX})"))
            _write_alert(conn, device_id, device_model, detected_at,
                         field, raw,
                         f"Fuel RAW value {raw} is outside valid range {FUEL_RAW_MIN}-{FUEL_RAW_MAX}. "
                         f"Do NOT use for fuel calculation.")
            continue

        # ── Rule 4: Liquid Slosh (>30% drop between consecutive pings) ─────
        prev = _get_previous_fuel(conn, device_id, field, detected_at)
        if prev:
            _, prev_raw = prev
            if prev_raw and prev_raw > 0:
                drop_pct = ((prev_raw - raw) / prev_raw) * 100.0
                if drop_pct > SLOSH_DROP_PERCENT:
                    issues.append((field, raw,
                                   f"Impossible liquid slosh: {drop_pct:.1f}% drop in one ping"))
                    _write_alert(conn, device_id, device_model, detected_at,
                                 field, raw,
                                 f"Impossible fuel drop: {drop_pct:.1f}% between consecutive pings. "
                                 f"Previous RAW={prev_raw:.0f}, Current RAW={raw:.0f}. "
                                 f"Likely sensor float failure, not actual theft.")

    # ── Validate each LLS temperature sensor ──────────────────────────────
    for field in FUEL_TEMP_FIELDS:
        raw_val = metrics.get(field)
        if raw_val is None:
            continue

        try:
            temp = float(raw_val)
        except (TypeError, ValueError):
            continue

        # ── Rule: Temperature probe disconnected ───────────────────────────
        if temp == FUEL_TEMP_DISCONNECT:
            issues.append((field, temp,
                           "Temperature probe disconnected. Value = -128"))
            _write_alert(conn, device_id, device_model, detected_at,
                         field, temp,
                         "LLS temperature probe disconnected. "
                         "Value -128 indicates probe wire is broken or unplugged.")

    return issues


# ── Lambda Handler ────────────────────────────────────────────────────────────
def lambda_handler(event, context):
    if not psycopg2:
        logger.error("psycopg2 is not installed.")
        return {"statusCode": 500, "body": "psycopg2 not available"}

    try:
        logger.info("Fuel Bad Data Detection - Received: %s", json.dumps(event))
        payload = json.loads(event["body"]) if "body" in event else event

        conn   = _connect()
        issues = validate_fuel(payload, conn)
        conn.close()

        status = "BAD_DATA" if issues else "VALID"
        logger.info("Fuel validation result: %s | issues: %d", status, len(issues))

        return {
            "statusCode": 200,
            "body": json.dumps({
                "status":   status,
                "imei":     payload.get("imei"),
                "issues":   [{"field": f, "value": str(v), "reason": r} for f, v, r in issues],
                "is_valid": len(issues) == 0
            })
        }

    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
