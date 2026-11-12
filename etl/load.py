"""STEP 3 - LOAD: save clean data into PostgreSQL without creating duplicates."""
import logging
 
from psycopg2.extras import execute_values
 
import config
 
log = logging.getLogger(__name__)
 
# If a row for the same city + hour already exists, update it (no duplicates).
UPSERT_WEATHER_SQL = """
    INSERT INTO weather_hourly
        (city_id, observed_at, temperature_c, humidity_pct,
         precipitation_mm, wind_speed_kmh)
    VALUES %s
    ON CONFLICT (city_id, observed_at) DO UPDATE SET
        temperature_c    = EXCLUDED.temperature_c,
        humidity_pct     = EXCLUDED.humidity_pct,
        precipitation_mm = EXCLUDED.precipitation_mm,
        wind_speed_kmh   = EXCLUDED.wind_speed_kmh,
        loaded_at        = CURRENT_TIMESTAMP
"""
 
 
def upsert_cities(conn):
    """Make sure every city in config.py exists in the cities table.
 
    Returns a dict like {"Coimbatore": 1, "Chennai": 2, ...}
    """
    city_ids = {}
    with conn, conn.cursor() as cur:
        for city in config.CITIES:
            cur.execute(
                """
                INSERT INTO cities (city_name, latitude, longitude)
                VALUES (%s, %s, %s)
                ON CONFLICT (city_name) DO UPDATE SET
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude
                RETURNING city_id
                """,
                (city["name"], city["latitude"], city["longitude"]),
            )
            city_ids[city["name"]] = cur.fetchone()[0]
    return city_ids
 
 
def _to_float(value):
    """Turn blank values (NaN) into None so PostgreSQL stores NULL."""
    return None if value is None or value != value else float(value)
 
 
def load_weather(conn, city_id, df):
    """Insert or update the rows of one city. Returns how many rows were sent."""
    if df.empty:
        return 0
 
    rows = [
        (
            city_id,
            row.observed_at.to_pydatetime(),
            _to_float(row.temperature_c),
            _to_float(row.humidity_pct),
            _to_float(row.precipitation_mm),
            _to_float(row.wind_speed_kmh),
        )
        for row in df.itertuples(index=False)
    ]
    with conn, conn.cursor() as cur:       # commits on success, rolls back on error
        execute_values(cur, UPSERT_WEATHER_SQL, rows)
    return len(rows)
 
 
def start_run(conn):
    """Write a 'RUNNING' line in etl_run_log and return its id."""
    with conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO etl_run_log (started_at, status) "
            "VALUES (CURRENT_TIMESTAMP, 'RUNNING') RETURNING run_id"
        )
        return cur.fetchone()[0]
 
 
def finish_run(conn, run_id, status, rows_loaded, message):
    """Update the log line with the final result."""
    with conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE etl_run_log SET finished_at = CURRENT_TIMESTAMP, "
            "status = %s, rows_loaded = %s, message = %s WHERE run_id = %s",
            (status, rows_loaded, message, run_id),
        )
