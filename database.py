# database.py

import sqlite3
from datetime import datetime, date

DB_NAME = "api_keys.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        '''CREATE TABLE IF NOT EXISTS api_keys (
                key TEXT PRIMARY KEY,
                expired_at TEXT,
                user_type TEXT
            )'''
    )
    c.execute(
        '''CREATE TABLE IF NOT EXISTS usage (
                key TEXT,
                date TEXT,
                count INTEGER,
                PRIMARY KEY(key, date)
            )'''
    )
    conn.commit()
    conn.close()

def is_api_key_valid(api_key: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT expired_at FROM api_keys WHERE key=?", (api_key,))
    row = c.fetchone()
    conn.close()
    if not row:
        return False, None  # 不存在
    expired_at = row[0]
    if expired_at and datetime.fromisoformat(expired_at) < datetime.now():
        return False, None  # 过期
    return True, expired_at

def get_calls_today(api_key: str):
    today = str(date.today())
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT count FROM usage WHERE key=? AND date=?", (api_key, today))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def increment_call(api_key: str):
    today = str(date.today())
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # 查询
    c.execute("SELECT count FROM usage WHERE key=? AND date=?", (api_key, today))
    row = c.fetchone()
    if row:
        c.execute("UPDATE usage SET count = count + 1 WHERE key=? AND date=?", (api_key, today))
    else:
        c.execute("INSERT INTO usage(key, date, count) VALUES (?, ?, 1)", (api_key, today))
    conn.commit()
    conn.close()

def get_user_type(api_key: str) -> str:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_type FROM api_keys WHERE key=?", (api_key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def add_api_key(api_key: str, expired_at: str, user_type:str = "free"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO api_keys(key, expired_at, user_type) VALUES (?, ?, ?)", (api_key, expired_at, user_type))
    conn.commit()
    conn.close()
