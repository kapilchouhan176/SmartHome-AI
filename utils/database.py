"""
utils/database.py
All MySQL access goes through these helper functions.
Always pass values through `params` (never build SQL with f-strings),
so user input can't break or change the query (SQL injection safety).
"""
import mysql.connector
from mysql.connector import pooling
from flask import g

_pool = None

# MySQL 8's standard mode. Cloud hosts like Aiven default to stricter ANSI mode,
# so we ask for the same mode everywhere and the app behaves the same.
SQL_MODE = ("ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,"
            "ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION")


def init_db(app):
    """Create the connection pool once, when the app starts."""
    global _pool
    _pool = pooling.MySQLConnectionPool(
        pool_name="smarthome_pool",
        pool_size=5,
        host=app.config["DB_HOST"],
        port=app.config["DB_PORT"],
        user=app.config["DB_USER"],
        password=app.config["DB_PASSWORD"],
        database=app.config["DB_NAME"],
        autocommit=False,
        time_zone=app.config["DB_TIME_ZONE"],
        sql_mode=SQL_MODE,
        **ssl_options(app.config["DB_SSL_CA"]),
    )
    # Return the connection to the pool at the end of every request
    app.teardown_appcontext(close_db)


# Extra connection settings for cloud MySQL (e.g. Aiven) that needs a CA certificate.
def ssl_options(ca_path):
    return {"ssl_ca": ca_path, "ssl_verify_cert": True} if ca_path else {}


def get_db():
    """Get the connection for the current request (one per request)."""
    if "db" not in g:
        g.db = _pool.get_connection()
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        if exception:
            db.rollback()
        db.close()  # returns it to the pool


def fetch_one(sql, params=()):
    """Run a SELECT and return one row as a dict (or None)."""
    cur = get_db().cursor(dictionary=True, buffered=True)   # buffered: extra rows are safely discarded
    cur.execute(sql, params)
    row = cur.fetchone()
    cur.close()
    return row


def fetch_all(sql, params=()):
    """Run a SELECT and return all rows as a list of dicts."""
    cur = get_db().cursor(dictionary=True)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return rows


def execute(sql, params=(), commit=True):
    """Run INSERT/UPDATE/DELETE. Returns the new row id for INSERTs."""
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute(sql, params)
        if commit:
            db.commit()
        return cur.lastrowid
    except mysql.connector.Error:
        db.rollback()
        raise
    finally:
        cur.close()


def commit():
    """Commit several execute(..., commit=False) calls together."""
    get_db().commit()


def rollback():
    get_db().rollback()
