import sqlite3
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
        c.execute("""
            CREATE TABLE IF NOT EXISTS autoresponders (
                guild_id TEXT,
                name TEXT,
                trigger TEXT,
                response TEXT,
                language TEXT DEFAULT 'en',
                creator_id INTEGER,
                PRIMARY KEY (guild_id, name, language)
            )
        """)
        conn.commit()


def set_guild_config(guild_id, key, value):
    """set a configuration value for a guild"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO guild (guild_id, ?)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET ? = excluded.?
        """,
            (
                key,
                (str(guild_id), value),
                key,
                key,
            ),
        )
        conn.commit()


def get_guild_config(guild_id, key):
    """get a configuration value for a guild"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT ? FROM guild WHERE guild_id = ?",
            (
                key,
                guild_id,
            ),
        )
        row = c.fetchone()
        return row[0] if row else None


def set_user_config(user_id, key, value):
    """set a configuration value for a user"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO user (user_id, ?)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET ? = excluded.?
        """,
            (
                key,
                str(user_id),
                value,
                key,
                key,
            ),
        )
        conn.commit()


def get_user_config(user_id, key):
    """get a configuration value for a user"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT ? FROM user WHERE user_id = ?",
            (
                key,
                user_id,
            ),
        )
        row = c.fetchone()
        return row[0] if row else None
