-- Tables for the Weather ETL Pipeline (safe to run many times)
 
-- One row per city
CREATE TABLE IF NOT EXISTS cities (
    city_id    SERIAL PRIMARY KEY,
    city_name  VARCHAR(50) NOT NULL UNIQUE,
    latitude   NUMERIC(8,5) NOT NULL,
    longitude  NUMERIC(8,5) NOT NULL
);
 
-- One row per city per hour (the main fact table)
CREATE TABLE IF NOT EXISTS weather_hourly (
    city_id           INT NOT NULL REFERENCES cities(city_id),
    observed_at       TIMESTAMP NOT NULL,           -- local time (Asia/Kolkata)
    temperature_c     NUMERIC(5,2) NOT NULL,
    humidity_pct      NUMERIC(5,2),
    precipitation_mm  NUMERIC(6,2),
    wind_speed_kmh    NUMERIC(6,2),
    loaded_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (city_id, observed_at)              -- stops duplicate rows
);
 
-- One row per pipeline run (monitoring)
CREATE TABLE IF NOT EXISTS etl_run_log (
    run_id       SERIAL PRIMARY KEY,
    started_at   TIMESTAMP,
    finished_at  TIMESTAMP,
    status       VARCHAR(20),                       -- RUNNING / SUCCESS / PARTIAL / FAILED
    rows_loaded  INT,
    message      TEXT
);
