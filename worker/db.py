import psycopg2
import os

from psycopg2.extras import RealDictCursor

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        database=os.getenv("DB_NAME", "studyflash"),
        user=os.getenv("DB_USER", "studyflash"),
        password=os.getenv("DB_PASSWORD", "studyFlash123!"),
        cursor_factory=RealDictCursor
    )
    return conn