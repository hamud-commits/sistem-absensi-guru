import sqlite3
from flask import current_app, g


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DB_PATH"])
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        g.db = conn
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(current_app.config["DB_PATH"])
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON;")
    schema_path = current_app.root_path + "/database/schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        db.executescript(f.read())
    db.commit()
    db.close()


def query_one(sql, params=()):
    cur = get_db().execute(sql, params)
    row = cur.fetchone()
    cur.close()
    return row


def query_all(sql, params=()):
    cur = get_db().execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return rows


def execute(sql, params=()):
    db = get_db()
    cur = db.execute(sql, params)
    db.commit()
    return cur.lastrowid

