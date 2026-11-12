"""Database connection and one-time setup (tables + views)."""
import os
 
import psycopg2
from dotenv import load_dotenv
 
import config
 
# Read the secrets from the private .env file
load_dotenv(config.BASE_DIR / ".env")
 
 
def get_connection():
    """Open a connection to PostgreSQL using the values in .env"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "weather_etl"),
        user=os.getenv("DB_USER", "etl_user"),
        password=os.getenv("DB_PASSWORD"),
    )
 
 
def init_db():
    """Create the tables and views (safe to run more than once)."""
    conn = get_connection()
    try:
        with conn, conn.cursor() as cur:
            for file_name in ("schema.sql", "views.sql"):
                cur.execute((config.SQL_DIR / file_name).read_text(encoding="utf-8"))
    finally:
        conn.close()
