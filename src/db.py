import psycopg2
from db_config import DB_SETTINGS

def get_connection():
    return psycopg2.connect(**DB_SETTINGS)   # <- bullet 1

def run(sql, params=None, fetch=False):      # <- bullet 2 (helper)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall() if fetch else None
            rowcount = cur.rowcount
        conn.commit()
        return rows, rowcount
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()