import psycopg2
import psycopg2.pool
from contextlib import contextmanager
import os

dbpool = psycopg2.pool.ThreadedConnectionPool(
    database=os.environ["DATABASE"],
    host=os.environ["DATABASE_HOST"],
    user=os.environ["DATABASE_USER"],
    password=os.environ["DATABASE_PASSWORD"],
    port=os.environ["DATABASE_PORT"],
    minconn=0,
    maxconn=100,
)

@contextmanager
def db_cursor():
    conn = dbpool.getconn()
    try:
        with conn.cursor() as cur:
            yield cur
            conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        dbpool.putconn(conn)
