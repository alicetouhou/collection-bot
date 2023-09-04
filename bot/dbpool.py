import psycopg2
import psycopg2.pool
from contextlib import contextmanager
import os

dbpool = psycopg2.pool.ThreadedConnectionPool(database="characters",
                                            host="localhost",
                                            user="postgres",
                                            password=os.environ["DB_PASSWORD"],
                                            port="5432",
                                            minconn=0,
                                            maxconn=5)

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

with db_cursor() as cur:
    cur.execute("CREATE TABLE IF NOT EXISTS servers (ID varchar(31), PRIMARY KEY (ID))")
    cur.execute("CREATE TABLE IF NOT EXISTS players_583039543893295127 (ID varchar(31), characters varchar(65535), currency int, claims int, claimed_daily int, rolls int, claimed_rolls int, wishlist varchar(1027), upgrades varchar(2055), PRIMARY KEY (ID))")
    cur.execute("INSERT INTO servers VALUES (583039543893295127) ON CONFLICT DO NOTHING")
    cur.execute("CREATE TABLE IF NOT EXISTS players_556614414153809961 (ID varchar(31), characters varchar(65535), currency int, claims int, claimed_daily int, rolls int, claimed_rolls int, wishlist varchar(1027), upgrades varchar(2055), PRIMARY KEY (ID))")
    cur.execute("INSERT INTO servers VALUES (556614414153809961) ON CONFLICT DO NOTHING")