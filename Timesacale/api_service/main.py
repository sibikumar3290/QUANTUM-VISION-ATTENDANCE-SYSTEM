from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from datetime import datetime, date, time
import database
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_main")

app = FastAPI(
    title="IoT Telemetry API",
    description="API for retrieving GPS and E-Lock telemetry data from TimescaleDB with advanced filtering.",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "IoT Telemetry API is running. Access /docs for the Swagger UI."}

# ==========================================
# GPS ENDPOINTS
# ==========================================

@app.get("/gps/latest", tags=["GPS Data"])
def get_latest_gps_data(imei: Optional[str] = Query(None, description="Filter by a specific device IMEI")):
    """Returns the most recent location and status for active GPS devices."""
    try:
        records = database.fetch_latest("gps_telemetry", imei, merge_tpms=True)
        if not records and imei:
            raise HTTPException(status_code=404, detail="Device not found.")
        return {"status": "success", "count": len(records), "data": records}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest GPS: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

@app.get("/gps/history", tags=["GPS Data"])
def get_gps_history(
    imei: Optional[str] = Query(None, description="Filter by a specific device IMEI"),
    start_time: Optional[datetime] = Query(None, description="Start date/time (e.g. 2026-08-01T00:00:00Z)"),
    end_time: Optional[datetime] = Query(None, description="End date/time (e.g. 2026-08-30T23:59:59Z)"),
    last_24_hours: bool = Query(False, description="Quick toggle to fetch only the last 24 hours of data"),
    limit: int = Query(1000, description="Maximum number of records to return (to prevent crashing)")
):
    """Returns historical GPS data with optional filters for IMEI and date ranges."""
    try:
        records = database.fetch_history("gps_telemetry", imei, start_time, end_time, last_24_hours, limit)
        if not records and imei:
            raise HTTPException(status_code=404, detail="No data found for the given filters.")
        return {"status": "success", "count": len(records), "data": records}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching GPS history: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")



# ==========================================
# E-LOCK ENDPOINTS
# ==========================================

@app.get("/elock/latest", tags=["E-Lock Data"])
def get_latest_elock_data(imei: Optional[str] = Query(None, description="Filter by a specific device IMEI")):
    """Returns the most recent status for active E-Locks."""
    try:
        records = database.fetch_latest("elock_telemetry", imei)
        if not records and imei:
            raise HTTPException(status_code=404, detail="Device not found.")
        return {"status": "success", "count": len(records), "data": records}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest E-Lock data: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

@app.get("/elock/history", tags=["E-Lock Data"])
def get_elock_history(
    imei: Optional[str] = Query(None, description="Filter by a specific device IMEI"),
    start_time: Optional[datetime] = Query(None, description="Start date/time (e.g. 2026-08-01T00:00:00Z)"),
    end_time: Optional[datetime] = Query(None, description="End date/time (e.g. 2026-08-30T23:59:59Z)"),
    last_24_hours: bool = Query(False, description="Quick toggle to fetch only the last 24 hours of data"),
    limit: int = Query(1000, description="Maximum number of records to return")
):
    """Returns historical E-Lock data with optional filters for IMEI and date ranges."""
    try:
        records = database.fetch_history("elock_telemetry", imei, start_time, end_time, last_24_hours, limit)
        if not records and imei:
            raise HTTPException(status_code=404, detail="No data found for the given filters.")
        return {"status": "success", "count": len(records), "data": records}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching E-Lock history: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")



@app.get("/elock/alarms", tags=["E-Lock Data"])
def get_elock_alarms(
    imei: Optional[str] = Query(None, description="Filter by a specific device IMEI"),
    start_time: Optional[datetime] = Query(None, description="Start date/time (e.g. 2026-08-01T00:00:00Z)"),
    end_time: Optional[datetime] = Query(None, description="End date/time (e.g. 2026-08-30T23:59:59Z)"),
    last_24_hours: bool = Query(False, description="Quick toggle to fetch only the last 24 hours of data"),
    limit: int = Query(1000, description="Maximum number of records to return")
):
    """Returns a history of exclusively E-Lock alarms (security alerts, low battery, etc.)."""
    try:
        records = database.fetch_history("elock_alarms", imei, start_time, end_time, last_24_hours, limit)
        if not records and imei:
            raise HTTPException(status_code=404, detail="No alarms found for the given filters.")
        return {"status": "success", "count": len(records), "data": records}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching E-Lock alarms: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

@app.get("/elock/alarms/latest", tags=["E-Lock Data"])
def get_latest_elock_alarms(imei: Optional[str] = Query(None, description="Filter by a specific device IMEI")):
    """Returns the single most recent alarm for active E-Locks."""
    try:
        records = database.fetch_latest("elock_alarms", imei)
        if not records and imei:
            raise HTTPException(status_code=404, detail="No alarms found.")
        return {"status": "success", "count": len(records), "data": records}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest E-Lock alarms: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

@app.get("/elock/lock-events/daily", tags=["E-Lock Data"])
def get_lock_events_daily(
    imei: str = Query(..., description="The device IMEI to get lock events for"),
    target_date: date = Query(..., description="The exact date to fetch events for (YYYY-MM-DD)")
):
    """Calculates exactly when the E-Lock was OPENED and CLOSED throughout the day."""
    try:
        events = database.fetch_lock_events(imei, target_date)
        if not events:
            raise HTTPException(status_code=404, detail="No lock events found for this device on this date (or lock state never changed).")
        return {"status": "success", "count": len(events), "data": events}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching lock events: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

if __name__ == "__main__":
    import uvicorn
    # To run locally: python main.py
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
