import os
import json
import logging
import datetime
import time
import boto3

try:
    import psycopg2
    from psycopg2.extras import Json
except ImportError:
    psycopg2 = None

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS Secrets Manager
_sm = boto3.client("secretsmanager")

# DB config from env
DB_HOST     = os.environ.get("DB_HOST")
DB_PORT     = os.environ.get("DB_PORT", "5432")
DB_NAME     = os.environ.get("DB_NAME")
DB_USER     = os.environ.get("DB_USER")
DEVICE_MODEL = os.environ.get("DEVICE_MODEL", "VL149")   # GT06 device model = VL149

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
                logger.exception(f"Could not fetch secret: {e}")
                _db_password_cache["value"] = os.environ.get("DB_PASSWORD")
        else:
            _db_password_cache["value"] = os.environ.get("DB_PASSWORD")
        if not _db_password_cache["value"]:
            logger.error("No database password configured.")
    return _db_password_cache["value"]


def build_generic_metrics(event: dict) -> dict:
    """
    Build a GENERIC metrics dictionary that matches the FMC125/FMC650 schema.
    GT06 fields that do not exist are stored as 0 to maintain a consistent
    structure across all device types in the database.
    """
    def _f(key, default=0):
        """Safely get a float value from the event, or return default."""
        val = event.get(key)
        try:
            return float(val) if val is not None else float(default)
        except (TypeError, ValueError):
            return float(default)

    return {
        # ── Fields that GT06 DOES provide ──────────────────────────────────
        "speed":                    _f("speed"),
        "angle":                    _f("angle"),
        "satellites":               _f("sat_cnt"),
        "ignition":                 _f("ignition"),
        "movement":                 _f("movement"),          # derived from speed > 0 in GT06.py
        "battery_voltage":          _f("battery_voltage"),
        "battery_level":            _f("battery_level"),
        "external_voltage":         _f("external_voltage"),
        "gsm_signal":               _f("gsm_signal"),
        "charging":                 _f("charging"),

        # ── Fields that FMC125 has but GT06 does NOT — stored as 0 ─────────
        "altitude":                 0,
        "priority":                 0,
        "data_mode":                0,
        "sleep_mode":               0,
        "gnss_status":              0,
        "gnss_pdop":                0,
        "gnss_hdop":                0,
        "gsm_cell_id":              0,
        "gsm_area_code":            0,
        "active_gsm_operator":      0,
        "network_type":             0,
        "trip_odometer":            0,
        "total_odometer":           0,
        "digital_input_1":          0,
        "digital_input_2":          0,
        "digital_output_1":         0,
        "analog_input_1":           0,
        "pulse_counter_din1":       0,
        "sd_status":                0,
        "eco_score":                0,
        "ibutton":                  0,
        "rfid":                     0,
        "user_id":                  0,
        "bt_status":                0,
        "fuel_used_gps":            0,
        "fuel_rate_gps":            0,
        # LLS Fuel sensors (not available on GT06)
        "lls1_fuel_level":          0,
        "lls1_temperature":         0,
        "lls2_fuel_level":          0,
        "lls2_temperature":         0,
        "lls3_fuel_level":          0,
        "lls3_temperature":         0,
        "lls4_fuel_level":          0,
        "lls4_temperature":         0,
        "lls5_fuel_level":          0,
        "lls5_temperature":         0,
        # Dallas Temperature sensors (not available on GT06)
        "dallas_temperature_1":     0,
        "dallas_temperature_2":     0,
        "dallas_temperature_3":     0,
        "dallas_temperature_4":     0,
        # Engine / CAN data (not available on GT06)
        "engine_rpm":               0,
        "engine_coolant_temperature": 0,
    }


def write_to_postgres(event: dict) -> bool:
    if not psycopg2:
        logger.error("psycopg2 is not installed.")
        return False

    try:
        # Parse timestamp
        fix_time = event.get("fix_time")
        if fix_time:
            try:
                timestamp = datetime.datetime.fromisoformat(fix_time)
            except ValueError:
                timestamp = datetime.datetime.fromtimestamp(
                    int(fix_time) / 1000.0, tz=datetime.timezone.utc
                )
        else:
            timestamp = datetime.datetime.fromtimestamp(
                time.time(), tz=datetime.timezone.utc
            )

        imei     = str(event.get("imei", ""))
        lat      = float(event.get("latitude", 0))
        lon      = float(event.get("longitude", 0))
        metrics  = build_generic_metrics(event)
        model    = event.get("device_model") or DEVICE_MODEL

        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=_get_db_password(), connect_timeout=10
        )
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gps_telemetry (
                time         TIMESTAMPTZ NOT NULL,
                device_id    TEXT NOT NULL,
                device_model TEXT,
                latitude     DOUBLE PRECISION,
                longitude    DOUBLE PRECISION,
                metrics      JSONB
            );
        """)

        cursor.execute("""
            INSERT INTO gps_telemetry
                (time, device_id, device_model, latitude, longitude, metrics)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (timestamp, imei, model, lat, lon, Json(metrics)))

        conn.commit()
        cursor.close()
        conn.close()

        logger.info("Written to PostgreSQL: imei=%s model=%s", imei, model)
        return True

    except Exception as e:
        logger.exception("Failed to write to PostgreSQL: %s", e)
        return False


def lambda_handler(event, context):
    try:
        logger.info("Received: %s", json.dumps(event))

        # Support both raw event and body-wrapped (API Gateway)
        payload = json.loads(event["body"]) if "body" in event else event

        success = write_to_postgres(payload)

        return {
            "statusCode": 200 if success else 500,
            "body": json.dumps({
                "message": "Success" if success else "Failed",
                "imei": payload.get("imei"),
                "device_model": payload.get("device_model", DEVICE_MODEL),
            }),
        }
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal Server Error", "error": str(e)}),
        }
