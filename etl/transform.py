"""STEP 2 - TRANSFORM: turn raw JSON into a clean table and check quality."""
import logging
 
import pandas as pd
 
import config
 
log = logging.getLogger(__name__)
 
 
def transform(city_name, raw):
    """Convert the API JSON into a clean DataFrame.
 
    Returns (clean_dataframe, stats) where stats counts the rows we removed.
    Columns: observed_at, temperature_c, humidity_pct,
             precipitation_mm, wind_speed_kmh
    """
    hourly = raw.get("hourly")
    if not hourly or "time" not in hourly:
        raise ValueError(f"{city_name}: API response has no hourly data")
 
    df = pd.DataFrame(hourly).rename(
        columns={"time": "observed_at", **config.COLUMN_MAP}
    )
    df["observed_at"] = pd.to_datetime(df["observed_at"])
    for column in config.VALUE_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")
 
    total_rows = len(df)
 
    # Check 1: the API also returns future hours (forecast). Keep the past only.
    now_local = pd.Timestamp.now(tz=config.TIMEZONE).tz_localize(None)
    df = df[df["observed_at"] <= now_local]
    future_skipped = total_rows - len(df)
 
    # Check 2: temperature is required
    before = len(df)
    df = df.dropna(subset=["temperature_c"])
 
    # Check 3: values must be inside realistic ranges (blank values are allowed
    # for the other columns, but a present value must be realistic)
    for column, (low, high) in config.VALID_RANGES.items():
        df = df[df[column].isna() | df[column].between(low, high)]
 
    # Check 4: one row per hour
    df = df.drop_duplicates(subset=["observed_at"], keep="last")
 
    rejected = before - len(df)
    df = df.sort_values("observed_at").reset_index(drop=True)
 
    stats = {"future_hours_skipped": future_skipped, "rows_rejected": rejected}
    log.info(
        "%s: %d clean rows (skipped %d future hours, rejected %d bad rows)",
        city_name, len(df), future_skipped, rejected,
    )
    return df, stats
