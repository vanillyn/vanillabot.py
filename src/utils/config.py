import sqlite3
import os

DB_PATH = "config.db"

def init_config():
    """makes the configuration database"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS guild (
                guild_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'en',
                prefix TEXT DEFAULT 'y;'
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS user (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'en'
            )
        """)
        conn.commit()

def set_guild_config(guild_id, key, value):
    """set a configuration value for a guild"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(f"""
            INSERT INTO guild (guild_id, {key})
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET {key} = excluded.{key}
        """, (str(guild_id), value))
        conn.commit()

def get_guild_config(guild_id, key):
    """get a configuration value for a guild"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(f"SELECT {key} FROM guild WHERE guild_id = ?", (str(guild_id),))
        row = c.fetchone()
        print("getting guild config:", row)
        return row[0] if row else None

def set_user_config(user_id, key, value):
    """set a configuration value for a user"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(f"""
            INSERT INTO user (user_id, {key})
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET {key} = excluded.{key}
        """, (str(user_id), value))
        conn.commit()

def get_user_config(user_id, key):
    """get a configuration value for a user"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(f"SELECT {key} FROM user WHERE user_id = ?", (str(user_id),))
        row = c.fetchone()
        return row[0] if row else None
