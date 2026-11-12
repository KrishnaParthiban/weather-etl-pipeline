
"""STEP 1 - EXTRACT: download hourly weather data for one city from the API."""
import json
import logging
import time
 
import requests
 
import config
 
log = logging.getLogger(__name__)
 
 
def fetch_city_weather(city, past_days=1):
    """Call the Open-Meteo API for one city and return the JSON as a dict.
 
    Retries a few times if the internet or the API fails.
    """
    params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "hourly": ",".join(config.HOURLY_VARIABLES),
        "timezone": config.TIMEZONE,
        "past_days": past_days,
        "forecast_days": 1,
    }
 
    last_error = None
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            response = requests.get(
                config.API_URL, params=params, timeout=config.REQUEST_TIMEOUT
            )
            response.raise_for_status()      # raises an error for 4xx / 5xx
            data = response.json()
            _save_raw_copy(city["name"], data)
            return data
        except (requests.RequestException, ValueError) as error:
            last_error = error
            log.warning(
                "%s: attempt %d/%d failed: %s",
                city["name"], attempt, config.MAX_RETRIES, error,
            )
            if attempt < config.MAX_RETRIES:
                time.sleep(config.RETRY_WAIT_SECONDS)
 
    raise RuntimeError(
        f"Could not fetch data for {city['name']} after "
        f"{config.MAX_RETRIES} attempts"
    ) from last_error
 
 
def _save_raw_copy(city_name, data):
    """Keep the latest raw API response on disk (useful for debugging)."""
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = config.RAW_DIR / f"{city_name.lower()}_latest.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

