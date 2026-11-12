"""Project settings. Change cities or limits here, not in the other files."""
from pathlib import Path
 
# ---- Folders -------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
LOG_DIR = BASE_DIR / "logs"
SQL_DIR = BASE_DIR / "sql"
EXPORT_DIR = BASE_DIR / "exports"
 
# ---- API (Open-Meteo: free, no API key needed) ---------------------------
API_URL = "https://api.open-meteo.com/v1/forecast"
TIMEZONE = "Asia/Kolkata"
MAX_PAST_DAYS = 92          # the most history this API gives in one request
REQUEST_TIMEOUT = 30        # seconds to wait for the API
MAX_RETRIES = 3             # tries before giving up on one city
RETRY_WAIT_SECONDS = 5
 
# API name -> our database column name
COLUMN_MAP = {
    "temperature_2m": "temperature_c",
    "relative_humidity_2m": "humidity_pct",
    "precipitation": "precipitation_mm",
    "wind_speed_10m": "wind_speed_kmh",
}
HOURLY_VARIABLES = list(COLUMN_MAP.keys())
VALUE_COLUMNS = list(COLUMN_MAP.values())
 
# ---- Cities to collect ---------------------------------------------------
CITIES = [
    {"name": "Coimbatore", "latitude": 11.0168, "longitude": 76.9558},
    {"name": "Chennai",    "latitude": 13.0827, "longitude": 80.2707},
    {"name": "Madurai",    "latitude": 9.9252,  "longitude": 78.1198},
    {"name": "Bengaluru",  "latitude": 12.9716, "longitude": 77.5946},
    {"name": "Kochi",      "latitude": 9.9312,  "longitude": 76.2673},
]
 
# ---- Data quality rules: (minimum, maximum) allowed ----------------------
VALID_RANGES = {
    "temperature_c": (-10, 60),
    "humidity_pct": (0, 100),
    "precipitation_mm": (0, 500),
    "wind_speed_kmh": (0, 300),
}
