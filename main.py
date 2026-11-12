"""Weather ETL Pipeline - run this file.
 
Examples:
    python main.py --init-db        # create tables and views (first time only)
    python main.py --backfill 7     # load the last 7 days of history
    python main.py                  # normal run (last 1 day) - cron uses this
    python main.py --export-csv     # save the views as CSV files in exports/
"""
import argparse
import csv
import logging
import sys
 
import config
from etl import db
from etl.extract import fetch_city_weather
from etl.load import finish_run, load_weather, start_run, upsert_cities
from etl.transform import transform
 
log = logging.getLogger("weather_etl")
 
 
def setup_logging():
    config.LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        handlers=[
            logging.FileHandler(config.LOG_DIR / "etl.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
 
 
def run_pipeline(past_days):
    """Extract -> Transform -> Load for every city. Returns an exit code."""
    conn = db.get_connection()
    run_id = start_run(conn)
    log.info("Run %d started (last %d day(s) of data)", run_id, past_days)
    total_rows = 0
    failed_cities = []
    try:
        city_ids = upsert_cities(conn)
        for city in config.CITIES:
            try:
                raw = fetch_city_weather(city, past_days)             # 1. Extract
                clean, _stats = transform(city["name"], raw)          # 2. Transform
                rows = load_weather(conn, city_ids[city["name"]], clean)  # 3. Load
                total_rows += rows
                log.info("%s: %d rows saved", city["name"], rows)
            except Exception as error:      # one bad city must not stop the rest
                failed_cities.append(city["name"])
                log.error("%s failed: %s", city["name"], error)
 
        if not failed_cities:
            status, message = "SUCCESS", "All cities loaded"
        elif len(failed_cities) == len(config.CITIES):
            status, message = "FAILED", "All cities failed"
        else:
            status, message = "PARTIAL", "Failed cities: " + ", ".join(failed_cities)
        finish_run(conn, run_id, status, total_rows, message)
        log.info("Run %d finished: %s (%d rows)", run_id, status, total_rows)
        return 0 if status == "SUCCESS" else 1
    except Exception as error:
        log.exception("Pipeline stopped: %s", error)
        finish_run(conn, run_id, "FAILED", total_rows, str(error)[:500])
        return 1
    finally:
        conn.close()
 
 
def export_csv():
    """Save the Power BI views as CSV files (backup if Power BI cannot connect)."""
    config.EXPORT_DIR.mkdir(exist_ok=True)
    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            for view in ("v_hourly_weather", "v_daily_weather", "v_data_freshness"):
                cur.execute(f"SELECT * FROM {view} ORDER BY 1, 2")
                path = config.EXPORT_DIR / f"{view}.csv"
                with open(path, "w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow([col[0] for col in cur.description])
                    writer.writerows(cur.fetchall())
                log.info("Exported %s", path)
    finally:
        conn.close()
 
 
def backfill_days(value):
    days = int(value)
    if not 1 <= days <= config.MAX_PAST_DAYS:
        raise argparse.ArgumentTypeError(f"choose a number from 1 to {config.MAX_PAST_DAYS}")
    return days
 
 
def main():
    parser = argparse.ArgumentParser(description="Weather ETL Pipeline")
    parser.add_argument("--init-db", action="store_true", help="create tables and views")
    parser.add_argument("--backfill", type=backfill_days, default=1, metavar="DAYS",
                        help="how many past days to load (default 1)")
    parser.add_argument("--export-csv", action="store_true", help="export views to CSV")
    args = parser.parse_args()
 
    setup_logging()
    try:
        if args.init_db:
            db.init_db()
            log.info("Database tables and views are ready")
            return 0
        if args.export_csv:
            export_csv()
            return 0
        return run_pipeline(args.backfill)
    except Exception as error:
        log.error("Could not run: %s", error)
        return 1
 
 
if __name__ == "__main__":
    sys.exit(main())
