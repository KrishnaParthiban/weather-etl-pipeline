-- Views used by Power BI (CREATE OR REPLACE = safe to run many times)
 
-- Hourly data with the city name (flat table, easy for Power BI)
CREATE OR REPLACE VIEW v_hourly_weather AS
SELECT c.city_name,
       w.observed_at,
       w.temperature_c,
       w.humidity_pct,
       w.precipitation_mm,
       w.wind_speed_kmh
FROM weather_hourly w
JOIN cities c ON c.city_id = w.city_id;
 
-- One row per city per day
CREATE OR REPLACE VIEW v_daily_weather AS
SELECT c.city_name,
       w.observed_at::date               AS weather_date,
       ROUND(AVG(w.temperature_c), 1)    AS avg_temp_c,
       MIN(w.temperature_c)              AS min_temp_c,
       MAX(w.temperature_c)              AS max_temp_c,
       ROUND(AVG(w.humidity_pct), 1)     AS avg_humidity_pct,
       ROUND(SUM(w.precipitation_mm), 1) AS total_rain_mm,
       ROUND(AVG(w.wind_speed_kmh), 1)   AS avg_wind_kmh,
       COUNT(*)                          AS hours_recorded
FROM weather_hourly w
JOIN cities c ON c.city_id = w.city_id
GROUP BY c.city_name, w.observed_at::date;
 
-- Is the pipeline still collecting fresh data?
CREATE OR REPLACE VIEW v_data_freshness AS
SELECT c.city_name,
       MAX(w.observed_at) AS last_observation,
       COUNT(*)           AS total_rows,
       ROUND(EXTRACT(EPOCH FROM
             ((NOW() AT TIME ZONE 'Asia/Kolkata') - MAX(w.observed_at))) / 3600.0, 1)
                          AS hours_since_last_data
FROM weather_hourly w
JOIN cities c ON c.city_id = w.city_id
GROUP BY c.city_name;
